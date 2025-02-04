
import cv2
import numpy as np
import base64
import math
import matplotlib.pyplot as plt

from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender

from src.utils.messages.allMessages import (
    mainCamera,
    LaneKeeping
)



class threadLaneDetection(ThreadWithStop):

    def __init__(self, queueList, logging, debugging=False):
        super(threadLaneDetection, self).__init__()
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        self.width = 640
        self.height = 480

        ##TO DO:add camera calibration parameters


        self.laneKeepingSender = messageHandlerSender(self.queuesList, LaneKeeping)

        self.subscribe()

#=======================================================PROCESS IMAGE=================================================================###


    def gamma_correction(image, gamma=2.0):
        # Build a lookup table mapping pixel values [0, 255] to their gamma-corrected values
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype("uint8")
        # Apply gamma correction using the lookup table
        return cv2.LUT(image, table)

    def detect_lines(self,image):
        gray=cv2.cvtColor(image,cv2.COLOR_RGB2GRAY)
        blur=cv2.GaussianBlur(gray,(5,5),0) 
        canny=cv2.Canny(blur,50,150)

        polygons=np.array([
        [(1,self.height),(1,3*self.height//5),(self.width,3*self.height//5),(self.width,self.height)] #TO DO: make new roi
            ])
        mask=np.zeros_like(canny)
        cv2.fillPoly(mask,polygons,255)
        masked_image=cv2.bitwise_and(canny,mask)

        lines=cv2.HoughLinesP(masked_image,2,np.pi/180,50,np.array([]),minLineLength=5,maxLineGap=20) #TO DO: adjust parameters
        return lines
    
#TO DO: calibration
#TO DO: add Kalman filter for better line tracking
    
#=========================================================COMPUTING LANE LINES========================================================###
    def make_coordinates(self,line_parameters):
        if (line_parameters.size==2):
            slope,intercept=line_parameters
            #print("slope", slope)
            y1=self.height
            y2=int(y1*3/5)
            x1=int((y1-intercept)//slope)
            x2=int((y2-intercept)//slope)
            return np.array([x1,y1,x2,y2])
        return None

    def average_slope_intersect(self,lines):
        left_fit=[]
        right_fit=[]
        horizontal_fit=[]
        if (lines is not None):
            for line in lines:
                x1,y1,x2,y2=line.reshape(4) #mozda za ove tacke da dodas naknadno, neki uslov da bude sigurno koje su to tacno tacke
                parameters=np.polyfit((x1,x2),(y1,y2),1)
                slope=parameters[0]
                #print(slope,' slope')
                intersect=parameters[1]
                if slope<-0.1:
                    left_fit.append((slope,intersect)) #vodi racuna o tome kako su koordinate slike postavljene!!!!!
                elif slope>0.1:
                    right_fit.append((slope,intersect))
                else:
                    horizontal_fit.append((slope,intersect))
                    print("RASKRSINCAAA!!!!!!!!!!")
                    #print('raskrsnica koord ',x1,y1,x2,y2)

            left_fit_average=np.average(left_fit,axis=0)
            right_fit_average=np.average(right_fit,axis=0)
            horizontal_fit_average=np.average(horizontal_fit,axis=0)
            #print(horizontal_fit_average,' horizontal fit average')

            left_line=self.make_coordinates(left_fit_average)
            right_line=self.make_coordinates(right_fit_average)
            #horizontal_line=make_coordinates(height,horizontal_fit_average)
            
            lines=[]
            if (left_line is not None):
                #print('left ',left_line,' right ',right_line,'  hor') #ovde ne valja, treba da vraca i bar jednu listu ako je uhvatio bilo sta!!!!
            # if horizontal_line is None:
            #     horizontal_line = []
                lines.append(left_line)
            if (right_line is not None):
                lines.append(right_line)
            return lines
        else:
            return None
    
    def display_lines(self,image,lines): 
        line_image=np.zeros_like(image)
        if lines is not None:
        #  print(lines)
            for line in lines:
                if (line!= []):
                    x1,y1,x2,y2=line
                #   print(type(x1),x1,' nulti element x1', type(x2), x1, type(y1), y1,type(y2),y2)
                    cv2.line(line_image,(x1,y1),(x2,y2),(255,0,0),10)
        return line_image
    

#==============================================STEERING ANGLE===========================================================================###

    def get_steering_angle(self,lane_lines):
        if len(lane_lines) == 2: 
            left_x1, _, _, _ = lane_lines[0] 
            right_x1, _, _, _ = lane_lines[1] 
            x_offset = (left_x1 + right_x1) / 2 - self.width//2
            y_offset = int(self.height / 2)  

        elif len(lane_lines) == 1: 
            x1, _, x2, _ = lane_lines[0]
            x_offset = x2 - x1
            y_offset = int(self.height / 2)

        elif len(lane_lines) == 0:
            x_offset = 0
            y_offset = int(self.height / 2)

        angle_to_mid_radian = math.atan(x_offset / y_offset)
        angle_to_mid_deg = float(angle_to_mid_radian * 180.0 / math.pi)  
        steering_angle = angle_to_mid_deg + 90 

        return steering_angle
        

    def run(self):
        while self._running:
            #TO DO:calibrate camera
            imageRecv = self.imageSubscriber.receive()
            if imageRecv is not None:
                img_data = base64.b64decode(imageRecv["msgValue"])
                img = np.frombuffer(img_data, dtype=np.uint8)
                image = cv2.imdecode(img, cv2.IMREAD_COLOR)
                combo_image=np.copy(image)
                lane_image=np.copy(image)
                lane_image=self.gamma_correction(lane_image)
                lines=self.detect_lines(lane_image)
                average_lines=self.average_slope_intersect(lines)
                steering_angle=self.get_steering_angle(average_lines)
                self.laneKeepingSender.send(steering_angle)
                if (average_lines is not None):
                    line_image=self.display_lines(lane_image,average_lines)
                    combo_image=cv2.addWeighted(lane_image,0.8,line_image,1,1)
                plt.imshow(cv2.cvtColor(combo_image, cv2.COLOR_BGR2RGB))
                plt.axis('off')  # Hide axes
                plt.show()
                

    def subscribe(self):
        self.imageSubscriber = messageHandlerSubscriber(self.queuesList, mainCamera, "lastOnly", True)


    def start(self):
        super(threadLaneDetection, self).start()

    def stop(self):
        super(threadLaneDetection, self).stop()
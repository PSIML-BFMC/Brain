# Copyright (c) 2019, Bosch Engineering Center Cluj and BFMC organizers
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.

# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE

import json
import time


from src.hardware.serialhandler.threads.messageconverter import MessageConverter
from src.templates.threadwithstop import ThreadWithStop
from src.control.PIDController import PIDController
from src.control.states import States
from src.utils.messages.allMessages import (
    LaneKeeping,
    RecognisedSign,
    HorizontalLine,
)
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber



class threadWrite(ThreadWithStop):
    """This thread write the data that Raspberry PI send to NUCLEO.\n

    Args:
        queues (dictionar of multiprocessing.queues.Queue): Dictionar of queues where the ID is the type of messages.
        serialCom (serial.Serial): Serial connection between the two boards.
        logFile (FileHandler): The path to the history file where you can find the logs from the connection.
        example (bool, optional): Flag for exmaple activation. Defaults to False.
    """

    # ===================================== INIT =========================================
    def __init__(self, queues, serialCom, logFile, logger, debugger = False, example=False):
        super(threadWrite, self).__init__()
        self.queuesList = queues
        self.serialCom = serialCom
        self.logFile = logFile
        self.exampleFlag = example
        self.logger = logger
        self.debugger = debugger
        self.start_time=time.time()
        self.running = False
        self.engineEnabled = False
        self.messageConverter = MessageConverter()
        self.configPath = "src/utils/table_state.json"

        #initializing pid controller
        self.PID=PIDController()

        #adding states
        self.current_state=States.LANE_KEEPING

        self.loadConfig("init")
        self.subscribe()

    def subscribe(self):
        """Subscribe function. In this function we make all the required subscribe to process gateway"""

        self.LaneKeepingSubscriber=messageHandlerSubscriber(self.queuesList, LaneKeeping, "lastOnly", True)
        self.SignSubscriber=messageHandlerSubscriber(self.queuesList,RecognisedSign,"lastOnly",True)
        self.HorizontalLineSubsrciber=messageHandlerSubscriber(self.queuesList,HorizontalLine,"lastOnly",True)
    # ==================================== SENDING =======================================

    def sendToSerial(self, msg):
        command_msg = self.messageConverter.get_command(**msg)
        if command_msg != "error":
            self.serialCom.write(command_msg.encode("ascii"))
            self.logFile.write(command_msg)

    def loadConfig(self, configType):
        with open(self.configPath, "r") as file:
            data = json.load(file)

        if configType == "init":
            data = data[len(data)-1]
            command = {"action": "batteryCapacity", "capacity": data["batteryCapacity"]["capacity"]}
            self.sendToSerial(command)
            time.sleep(0.05)
        else:
            for e in range(4):
                if data[e]["value"] == "False":
                    value = 0
                else:
                    value = 1 
                command = {"action": data[e]['command'], "activate": value}
                self.sendToSerial(command)
                time.sleep(0.05)

    def convertFc(self,instantRecv):
        if instantRecv =="True":
            return 1
        else :
            return 0
        
     # ===================================== RUN ==========================================
    """ def run(self):

        self.running = True
        print("primio naredbu!!!!!")
        self.engineEnabled = True
        command = {"action": "kl", "mode": 30}
        self.sendToSerial(command)
        time.sleep(5)

        y=100
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)
            

        previous_angle=0
        while self._running:
            time_=time.time()-self.start_time
            if (time_)>60:
                print(time_,' ,proteklo vreme')
                self._running=False
                x=0
                command = {"action": "kl", "mode": int(x)}
                self.sendToSerial(command)
                time.sleep(0.2)
                break
            send=True

                 
           
            steeringangleRecv = self.LaneKeepingSubscriber.receive()
            if steeringangleRecv is not None:
                steeringangle=int(round(self.PID.compute(steeringangleRecv))*10)
                if (abs(steeringangle-previous_angle)>50):
                    command = {"action": "steer", "steerAngle": int(steeringangle)}
                    self.sendToSerial(command)
                    previous_angle=steeringangle
            
         
        command = {"action": "speed", "speed": 0}
        self.sendToSerial(command)
        command = {"action": "kl", "mode": 0}
        self.sendToSerial(command)
        """

    #=============================== STATE MACHINE LOGIC =================================     

    def run(self):

        self.running = True
        print("primio naredbu!!!!!")
        self.engineEnabled = True
        command = {"action": "kl", "mode": 30}
        self.sendToSerial(command)
        time.sleep(10)

        y=100
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)

        y=100
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)

        y=100
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)
            

        previous_angle=0
        while self._running:
            time_=time.time()-self.start_time
            if (time_)>60:
                print(time_,' ,proteklo vreme')
                self._running=False
                x=0
                command = {"action": "kl", "mode": int(x)}
                self.sendToSerial(command)
                time.sleep(0.2)
                break

            
            steeringangleRecv = self.LaneKeepingSubscriber.receive()
            if (self.current_state==States.LANE_KEEPING):
                if steeringangleRecv is not None:
                    steeringangle=int(round(self.PID.compute(steeringangleRecv))*10)
                    if (abs(steeringangle-previous_angle)>50):
                        command = {"action": "steer", "steerAngle": int(steeringangle)}
                        self.sendToSerial(command)
                        previous_angle=steeringangle
            
            recognisedsignRecv = self.SignSubscriber.receive()
            if (recognisedsignRecv is not None):
                if (recognisedsignRecv=='Stop sign'): #dodaj uslovee dodatne!!!!!!
                    self.transition_to(States.STOP_INTERSECTION)
                elif (recognisedsignRecv=='Parking sign'):
                    self.transition_to(States.PARKING)
                elif (recognisedsignRecv=='Priority sign'):
                    self.transition_to(States.PRIORITY_INTERSECTION)
                elif (recognisedsignRecv=='Crosswalk sign'):
                    self.transition_to(States.CROSSWALK)
                elif (recognisedsignRecv=='Highway entrance sign'):
                    self.transition_to(States.HIGHWAY)
                elif (recognisedsignRecv=='Highway exit sign'):
                    self.transition_to(States.HIGHWAY_EXIT)
                elif (recognisedsignRecv=='Round-about sign'):
                    self.transition_to(States.ROUND_ABOUT)
                elif (recognisedsignRecv=='One way road sign'):
                    self.transition_to(States.LANE_KEEPING)
                elif (recognisedsignRecv=='No-entry road sign'):
                    self.transition_to(States.LANE_KEEPING) #mozda ovo bude trebalo da se menja idk

         
        command = {"action": "speed", "speed": 0}
        self.sendToSerial(command)
        command = {"action": "kl", "mode": 0}
        self.sendToSerial(command)    



    def transition_to(self, new_state):
        self.current_state = new_state
        if (self.current_state!=States.LANE_KEEPING):
            self.enter_state()

    def enter_state(self):
        if self.current_state == States.CROSSWALK:
            self.handle_crosswalk()
        elif self.current_state == States.STOP_INTERSECTION:
            self.handle_stop_intersection()
        elif self.current_state == States.PRIORITY_INTERSECTION:
            self.handle_priority_intersection()
        elif self.current_state == States.HIGHWAY:
            self.handle_highway()
        elif self.current_state == States.PARKING:
            self.handle_parking()
        elif self.current_state == States.HIGHWAY_EXIT:
            self.handle_highway_exit()
        elif self.current_state ==States.ROUND_ABOUT:
            self.handle_round_about()

    def handle_lane_following(self):
        steeringangleRecv = self.LaneKeepingSubscriber.receive()
        if steeringangleRecv is not None:
            steeringangle=int(round(self.PID.compute(steeringangleRecv))*10)
            if (abs(steeringangle-previous_angle)>50):
                command = {"action": "steer", "steerAngle": int(steeringangle)}
                self.sendToSerial(command)
                previous_angle=steeringangle
    
    def handle_crosswalk(self):
        print("Car is stopping for pedestrians...")
        print("slowing down...")
        
        time.sleep(0.02)
        y=50
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)
        time.sleep(0.01)
        y=50
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)
        start_time=time.time()
        previous_angle=0   
        while (True):
            steeringangleRecv = self.LaneKeepingSubscriber.receive()
            if steeringangleRecv is not None:
                steeringangle=int(round(self.PID.compute(steeringangleRecv))*10)
                if (abs(steeringangle-previous_angle)>50):
                    command = {"action": "steer", "steerAngle": int(steeringangle)}
                    self.sendToSerial(command)
                    previous_angle=steeringangle

            current_time=time.time()
            if (current_time-start_time>7):
                time.sleep(0.01)
                y=100
                command = {"action": "speed", "speed": int(y)}            
                self.sendToSerial(command)
                break

        y=100
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)
        self.SignSubscriber.receive()
        
        self.transition_to(States.LANE_KEEPING)
    
    def handle_stop_intersection(self):
        print("Car is stopping at an intersection...")
        previous_angle=0
        while (True): 
            steeringangleRecv = self.LaneKeepingSubscriber.receive()
            if steeringangleRecv is not None:
                steeringangle=int(round(self.PID.compute(steeringangleRecv))*10)
                if (abs(steeringangle-previous_angle)>50):
                    command = {"action": "steer", "steerAngle": int(steeringangle)}
                    self.sendToSerial(command)
                    previous_angle=steeringangle

            horizontallineRecv=self.HorizontalLineSubsrciber.receive()
            if (horizontallineRecv is not None and horizontallineRecv<100.0):
                print("stopping...")
                break
        time.sleep(0.01)
        y=0
        #command = {"action": "speed", "speed": int(y)}            
        #self.sendToSerial(command)
        command = {"action": "brake", "steerAngle": int(y)}
        self.sendToSerial(command)
        
        self.SignSubscriber.receive()
        time.sleep(3)
        y=100
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)
        y=100
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)
        y=100
        command = {"action": "speed", "speed": int(y)}            
        self.sendToSerial(command)
        self.transition_to(States.LANE_KEEPING)
    
    def handle_priority_intersection(self):
        print("Car is checking for priority and moving accordingly...")
        self.transition_to(States.LANE_KEEPING)
    
    def handle_highway(self):
        print("Car is on the highway, adjusting speed...")
        time.sleep(0.01)
        y=200
        command = {"action": "speed", "speed": int(y)}  
        self.sendToSerial(command)
        self.transition_to(States.LANE_KEEPING)
    
    def handle_parking(self):
        print("Car is parking...")
        self.transition_to(States.LANE_KEEPING)
    
    def handle_highway_exit(self):
        print("Car is leaving the highway...")
        time.sleep(0.01)
        y=100
        command = {"action": "speed", "speed": int(y)}  
        self.sendToSerial(command)
        self.transition_to(States.LANE_KEEPING)

    def handle_round_about(self):
        print("Car has entered the roundabout...")


    # ==================================== START =========================================
    def start(self):
        super(threadWrite, self).start()

    # ==================================== STOP ==========================================
    def stop(self):
        """This function will close the thread and will stop the car."""

        self.exampleFlag = False
        command = {"action": "kl", "mode": 0}
        self.sendToSerial(command)
        time.sleep(2)
        super(threadWrite, self).stop()


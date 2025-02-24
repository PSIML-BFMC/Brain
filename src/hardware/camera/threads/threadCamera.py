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

import cv2
import threading
import base64
import picamera2
import time
import numpy as np

from src.utils.messages.allMessages import (
    mainCamera,
    serialCamera,
    Recording,
    Record,
    Brightness,
    Contrast,
    RecognisedSign,
)
from src.utils.messages.messageHandlerSender import messageHandlerSender
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.templates.threadwithstop import ThreadWithStop

from ncnn_preprocess import ncnn_inference, draw_detections 


class threadCamera(ThreadWithStop):
    """Thread which will handle camera functionalities.\n
    Args:
        queuesList (dictionar of multiprocessing.queues.Queue): Dictionar of queues where the ID is the type of messages.
        logger (logging object): Made for debugging.
        debugger (bool): A flag for debugging.
    """

    # ================================ INIT ===============================================
    def __init__(self, queuesList, logger, debugger):
        super(threadCamera, self).__init__()
        self.queuesList = queuesList
        self.logger = logger
        self.debugger = debugger
        #self.frame_rate = 10
        self.frame_rate = 5
        self.recording = False

        self.video_writer = ""

        self.recordingSender = messageHandlerSender(self.queuesList, Recording)
        self.mainCameraSender = messageHandlerSender(self.queuesList, mainCamera)
        self.serialCameraSender = messageHandlerSender(self.queuesList, serialCamera)
        self.SignSender = messageHandlerSender(self.queuesList,RecognisedSign)

        self.subscribe()
        self._init_camera()
        self.Queue_Sending()
    #    self.Configs() -zakomentirala sam, posto pretpostavljam da necu primati poruke sa dashboarda za autonomnu voznju

    def subscribe(self):
        """Subscribe function. In this function we make all the required subscribe to process gateway"""

        self.recordSubscriber = messageHandlerSubscriber(self.queuesList, Record, "lastOnly", True)
        self.brightnessSubscriber = messageHandlerSubscriber(self.queuesList, Brightness, "lastOnly", True)
        self.contrastSubscriber = messageHandlerSubscriber(self.queuesList, Contrast, "lastOnly", True)

    def Queue_Sending(self):
        """Callback function for recording flag."""

        self.recordingSender.send(self.recording)
        threading.Timer(1, self.Queue_Sending).start()
        
    # =============================== STOP ================================================
    def stop(self):
        if self.recording:
            self.video_writer.release()
        super(threadCamera, self).stop()

    # =============================== CONFIG ==============================================
    def Configs(self):
        """Callback function for receiving configs on the pipe."""

        if self.brightnessSubscriber.isDataInPipe():
            message = self.brightnessSubscriber.receive()
            if self.debugger:
                self.logger.info(str(message))
            self.camera.set_controls(
                {
                    "AeEnable": False,
                    "AwbEnable": False,
                   # "Brightness": max(0.0, min(1.0, float(message))),
                    "Brightness": 0.5,
                }
            )
        if self.contrastSubscriber.isDataInPipe():
            message = self.contrastSubscriber.receive() # de modificat marti uc camera noua 
            if self.debugger:
                self.logger.info(str(message))
            self.camera.set_controls(
                {
                    "AeEnable": False,
                    "AwbEnable": False,
                    "Contrast": max(0.0, min(32.0, float(message))),
                }
            )
        threading.Timer(1, self.Configs).start()

    def gamma_correction(self, image, gamma=2.0):
        # Build a lookup table mapping pixel values [0, 255] to their gamma-corrected values
        inv_gamma = 1.0 / gamma
        table = np.array([(i / 255.0) ** inv_gamma * 255 for i in range(256)]).astype("uint8")
        # Apply gamma correction using the lookup table
        return cv2.LUT(image, table)

    # ================================ RUN ================================================
    def run(self):
        """This function will run while the running flag is True. It captures the image from camera and make the required modifies and then it send the data to process gateway."""
        send = True
        while self._running:
            try:
                recordRecv = self.recordSubscriber.receive()
                if recordRecv is not None: 
                    self.recording = bool(recordRecv)
                    if recordRecv == False:
                        self.video_writer.release()
                    else:
                        fourcc = cv2.VideoWriter_fourcc(
                            *"XVID"
                        )  # You can choose different codecs, e.g., 'MJPG', 'XVID', 'H264', etc.
                        self.video_writer = cv2.VideoWriter(
                            "output_video" + str(time.time()) + ".avi",
                            fourcc,
                            self.frame_rate,
                            (2048, 1080),
                        )

            except Exception as e:
                print(e)

            if send:
                mainRequest = self.camera.capture_array("main")
                serialRequest = self.camera.capture_array("lores")  # Will capture an array that can be used by OpenCV library

                if self.recording == True:
                    self.video_writer.write(mainRequest)

                serialRequest = cv2.cvtColor(serialRequest, cv2.COLOR_YUV2BGR_I420)

                # Start of Sign Detection
                top_right_crop = self.gamma_correction(serialRequest[0:320, 640 - 320:])
                outputs = ncnn_inference(top_right_crop, conf=0.8)
                detection_frame = draw_detections(top_right_crop, outputs)
                serialRequest[0:320, 640 - 320:] = detection_frame
                # End of Sign Detection

                _, mainEncodedImg = cv2.imencode(".jpg", mainRequest)                   
                _, serialEncodedImg = cv2.imencode(".jpg", serialRequest)

                mainEncodedImageData = base64.b64encode(mainEncodedImg).decode("utf-8")
                serialEncodedImageData = base64.b64encode(serialEncodedImg).decode("utf-8")

                self.mainCameraSender.send(mainEncodedImageData)
                self.serialCameraSender.send(serialEncodedImageData)
                #send information about detected sign
                if (outputs!=[]):
                    sign=outputs[0].class_name
                    self.SignSender.send(sign)

            send = not send

    # =============================== START ===============================================
    def start(self):
        super(threadCamera, self).start()

    # ================================ INIT CAMERA ========================================
    def _init_camera(self):
        """This function will initialize the camera object. It will make this camera object have two chanels "lore" and "main"."""

        self.camera = picamera2.Picamera2()
        config = self.camera.create_preview_configuration(
            buffer_count=1,
            queue=False,
           # main={"format": "RGB888", "size": (2048, 1080)},
            main={"format": "RGB888", "size": (640, 480)},
            lores={"size": (640, 480)}, #512, 270
            encode="lores",
        )
        self.camera.configure(config)
        self.camera.start()


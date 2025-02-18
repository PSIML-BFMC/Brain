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
from src.utils.messages.allMessages import (
    LaneKeeping,
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
        self.PID=PIDController()
        

        self.loadConfig("init")
        self.subscribe()

    def subscribe(self):
        """Subscribe function. In this function we make all the required subscribe to process gateway"""

        self.LaneKeepingSubscriber=messageHandlerSubscriber(self.queuesList, LaneKeeping, "lastOnly", True)
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
    def run(self):

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


from src.templates.threadwithstop import ThreadWithStop
from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender
from src.control.PIDController import PIDController
import time

from src.utils.messages.allMessages import (
    LaneKeeping,
    SpeedMotor_c,
    SteerMotor_c,
    Brake_c,
    Klem_c
)

class threadControl(ThreadWithStop):
    """This thread handles Control.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        self.PID=PIDController()
        self.subscribe()
        super(threadControl, self).__init__()

        self.SpeedMotorSender_c=messageHandlerSender(self.queuesList,SpeedMotor_c)
        self.SteerMotorSender_c=messageHandlerSender(self.queuesList,SteerMotor_c)
        self.Brake_c=messageHandlerSender(self.queuesList,Brake_c)
        self.Klem_c=messageHandlerSender(self.queuesList,Klem_c)
        self.Klem_c.send("30")

    def run(self):
        start_time=time.time()
        for i in range(30):
            self.Klem_c.send("30")
        print("sent to the motors")
        print('aaa')
        print("saaaaaaaaasaaa")
        print('AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA')
        self.SpeedMotorSender_c.send(str(100))
        while self._running:
            self.SpeedMotorSender_c.send(str(100))
           # print('u procesu control.....')
            steeringangleRecv = self.LaneKeepingSubscriber.receive()
            if steeringangleRecv is not None:
               # print(steeringangleRecv,' received steering angle')
               # print(steeringangleRecv,' received steering angle')
               # print(steeringangleRecv,' received steering angle')
                steeringangle=int(round(self.PID.compute(steeringangleRecv)))
                if (steeringangle>10 or steeringangle<-10):
                    self.SteerMotorSender_c.send(str(-1*steeringangle*10))
                    self.SteerMotorSender_c.send(str(-1*steeringangle*10))
                    self.SteerMotorSender_c.send(str(-1*steeringangle*10))
                    self.SteerMotorSender_c.send(str(-1*steeringangle*10))
                    self.SteerMotorSender_c.send(str(-1*steeringangle*10))
                    self.SteerMotorSender_c.send(str(-1*steeringangle*10))
                    self.SteerMotorSender_c.send(str(-1*steeringangle*10))
            time_=time.time()-start_time
            if (time_)>10:
                break

        self.Klem_c.send("0")
        self.Klem_c.send("0")

    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        self.LaneKeepingSubscriber=messageHandlerSubscriber(self.queuesList, LaneKeeping, "lastOnly", True)


    def start(self):
        super(threadControl, self).start()


    def stop(self):
        """This function will close the thread and will stop the car."""
        for i in range(5):
            self.Klem_c.send("0")
        time.sleep(2)
        super(threadControl, self).stop()

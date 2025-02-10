import cv2
import numpy as np
import base64


#best model ncnn, tako nesto na rasp pi nadji
#metadata.yaml ima za sta je sta



from src.templates.threadwithstop import ThreadWithStop

from src.utils.messages.messageHandlerSubscriber import messageHandlerSubscriber
from src.utils.messages.messageHandlerSender import messageHandlerSender

from src.utils.messages.allMessages import (
    mainCamera,
    RecognisedSign
    )

class threadSignRecognition(ThreadWithStop):
    """This thread handles SignRecognition.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        self.width=640
        self.height=480

        self.recognisedSignSender=messageHandlerSender(self,queueList, RecognisedSign)

        self.subscribe()
        super(threadSignRecognition, self).__init__()



    def preprocess_image(self,image):
        nn_image=image[0:320,320:640]
        #to do: other preprocessinf techniues, horizontal motion blur????, gamma correction??
        return nn_image

    def run(self):
        while self._running:
            imageRecv= self.imageSubscriber.receive()
            if imageRecv is not None:
                img_data = base64.b64decode(imageRecv)
                img = np.frombuffer(img_data, dtype=np.uint8)
                image = cv2.imdecode(img, cv2.IMREAD_COLOR)
                nn_image=self.preprocess_image(np.copy(image))
                #to do: neural network, output, send messages depending on detected sign
                


    def subscribe(self):
        """Subscribes to the messages you are interested in"""
        self.imageSubscriber=messageHandlerSubscriber(self.queuesList, mainCamera, "lastOnly", True)

    def start(self):
        super(threadSignRecognition, self).start()

    def stop(self):
        super(threadSignRecognition, self).stop()
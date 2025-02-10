if __name__ == "__main__":
    import sys
    sys.path.insert(0, "../../..")

from src.templates.workerprocess import WorkerProcess
from src.vision_sytem.SignRecognition.threads.threadSignRecognition import threadSignRecognition

class processSignRecognition(WorkerProcess):
    """This process handles SignRecognition.
    Args:
        queueList (dictionary of multiprocessing.queues.Queue): Dictionary of queues where the ID is the type of messages.
        logging (logging object): Made for debugging.
        debugging (bool, optional): A flag for debugging. Defaults to False.
    """

    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging
        super(processSignRecognition, self).__init__(self.queuesList)

    def run(self):
        """Apply the initializing methods and start the threads."""
        super(processSignRecognition, self).run()

    def _init_threads(self):
        """Create the SignRecognition Publisher thread and add to the list of threads."""
        SignRecognitionTh = threadSignRecognition(
            self.queuesList, self.logging, self.debugging
        )
        self.threads.append(SignRecognitionTh)

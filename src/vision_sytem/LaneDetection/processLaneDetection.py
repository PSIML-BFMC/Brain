if __name__ == "__main__":
    import sys
    sys.path.insert(0, "../../..")

from src.templates.workerprocess import WorkerProcess
from src.vision_sytem.LaneDetection.threads.threadLaneDetection import threadLaneDetection

class processLaneDetection(WorkerProcess):
    """This process detects lanes, and according to that, sends commands for lane keeping"""
    def __init__(self, queueList, logging, debugging=False):
        self.queuesList = queueList
        self.logging = logging
        self.debugging = debugging

        super(processLaneDetection, self).__init__(self.queuesList)

    def run(self):
        """Apply the initializing methods and start the threads."""
        super(processLaneDetection, self).run()

    def _init_threads(self):
        """Create the LaneDetection Publisher thread and add to the list of threads."""
        LaneDetectionTh = threadLaneDetection(
            self.queuesList, self.logging, self.debugging
        )
        self.threads.append(LaneDetectionTh)

#TO DO: make fake main, to test only this functionality!!
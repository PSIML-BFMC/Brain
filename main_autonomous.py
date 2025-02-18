# ===================================== GENERAL IMPORTS ==================================
import sys
import subprocess

sys.path.append(".")
from multiprocessing import Queue, Event
import logging

logging.basicConfig(level=logging.INFO)

# ===================================== PROCESS IMPORTS ==================================

from src.gateway.processGateway import processGateway
from src.hardware.camera.processCamera import processCamera
from src.hardware.serialhandler.processSerialHandler import processSerialHandler
from src.vision_sytem.LaneDetection.processLaneDetection import processLaneDetection
from src.dashboard.processDashboard import processDashboard
from src.data.Semaphores.Semaphores import processSemaphores
from src.data.TrafficCommunication.processTrafficCommunication import processTrafficCommunication
from src.utils.ipManager.IpReplacement import IPManager
# ------ New component imports starts here ------#

# ------ New component imports ends here ------#
# ======================================== SETTING UP ====================================
allProcesses = list()

queueList = {
    "Critical": Queue(),
    "Warning": Queue(),
    "General": Queue(),
    "Config": Queue(),
}

logging = logging.getLogger()

Camera = True
SerialHandler = True
LaneDeteciton = True
Dashboard=True

processGateway = processGateway(queueList, logging)
processGateway.start()

path = './src/dashboard/frontend/src/app/webSocket/web-socket.service.ts'
IpChanger = IPManager(path)
IpChanger.replace_ip_in_file()


# Initializing camera
if Camera:
    processCamera = processCamera(queueList, logging , debugging = False)
    allProcesses.append(processCamera)

#initialization dashboard
if Dashboard:
    processDashboard = processDashboard( queueList, logging, debugging = False)
    allProcesses.append(processDashboard)

# Initializing serial connection NUCLEO - > PI
if SerialHandler:
    processSerialHandler = processSerialHandler(queueList, logging, debugging = False)
    allProcesses.append(processSerialHandler)

if LaneDeteciton:
    processLaneDetection=processLaneDetection(queueList, logging, debugging=False)
    allProcesses.append(processLaneDetection)



# ===================================== START PROCESSES ==================================
for process in allProcesses:
    process.daemon = True
    process.start()

# ===================================== STAYING ALIVE ====================================
blocker = Event()
try:
    blocker.wait()
except KeyboardInterrupt:
    print("\nCatching a KeyboardInterruption exception! Shutdown all processes.\n")
    for proc in reversed(allProcesses):
        print("Process stopped", proc)
        proc.stop()

processGateway.stop()


#napravi ocitavanje za battery level npr koristeci se nekim dugmetomm sa tastature

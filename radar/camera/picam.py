import logging
import time
from picamera2 import Picamera2

logger = logging.getLogger(__name__)

class Picam:
    def __init__ (self):
        self.camera = Picamera2()
        self.camera.start()

    def __del__(self):
        self.camera.stop()
        self.camera.close()

    def takeStill(self):
        now = time.time()*1000
        filename = f'''images/{now}.jpg'''
        logger.info(f'''Click! [{filename}]''')
        self.camera.capture_file(filename)

def go():
    camera = Picam()
    camera.takeStill()
    return

if (__name__ == "__main__"):
    go()

import time
from picamera2 import Picamera2


class Picam:
    def __init__ (self):
        self.camera = Picamera2()
        self.camera.start()

    def __del__(self):
        self.camera.stop()
        self.camera.close()

    def takeStill(self):
        now = time.time()*1000
        self.camera.capture_file(f'''{now}.jpg''')

def go():
    camera = Picam()
    camera.takeStill()
    return

if (__name__ == "__main__"):
    go()

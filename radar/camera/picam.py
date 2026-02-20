from pprint import *
import logging
import time
from datetime import datetime
from picamera2 import Picamera2, MappedArray
import cv2

logger = logging.getLogger(__name__)

class Picam:
    def __init__ (self):

        self.camera = Picamera2()

        #pprint(self.camera.sensor_modes)
        '''
        arducam configs
        modes[0]:'size': (640, 480),
        modes[1]:'size': (1640, 1232),
        modes[2]:'size': (1920, 1080),
        modes[3]:'size': (3280, 2464),
        modes[4]:'size': (640, 480),
        modes[5]:'size': (1640, 1232),
        modes[6]:'size': (1920, 1080),
        modes[7]:'size': (3280, 2464),
        '''

        # grab values from sensor values so there will be no guessing
        mode = self.camera.sensor_modes[3]
        config = self.camera.create_still_configuration(main={'size': mode['size']})

        self.camera.configure(config)

        self.camera.start()

    def __del__(self):
        self.camera.stop()
        self.camera.close()

    def takeStill(self, speed, distance):

        while True:
            now = datetime.now()
            filename = f'''images/{now.year}{now.month:0>2}{now.day:0>2}{now.hour:0>2}{now.minute:0>2}{now.second:0>2}{now.microsecond:0>6}-{speed:0>2}.jpg'''

            text = now.isoformat(timespec='seconds')
            image_size = self.camera.camera_configuration()["main"]["size"]
            # left bottom corner
            position = (0, image_size[1] - 20)
            font_scale = 1
            font = cv2.FONT_HERSHEY_COMPLEX
            color = (255, 255, 255)
            thickness = 2
            status = f'''{text} [{speed}] [{distance}] [{self.camera.camera_configuration()["main"]["size"]}]'''

            with self.camera.captured_request() as request:
                with MappedArray(request, 'main') as m:
                    cv2.putText(m.array, status, position, font, font_scale, color, thickness)
                    request.save("main", filename)
            break

        logger.info(f'''Click! [{filename}]''')


def go():
    camera = Picam()
    camera.takeStill(20, 1024)
    return

if (__name__ == "__main__"):
    go()

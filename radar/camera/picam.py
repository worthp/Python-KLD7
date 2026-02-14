import logging
import time
from datetime import datetime
from picamera2 import Picamera2, MappedArray
import cv2

logger = logging.getLogger(__name__)

class Picam:
    def __init__ (self):
        self.camera = Picamera2()
        self.camera.start(show_preview=True)

    def __del__(self):
        self.camera.stop()
        self.camera.close()

    def takeStill(self, speed):

        while True:
            now = int(time.time()*1000)
            filename = f'''images/{speed}-{now}.jpg'''

            text = datetime.now().isoformat(timespec='seconds')
            # 640x480
            position = (0, 470)
            font_scale = 0.5
            font = cv2.FONT_HERSHEY_COMPLEX
            color = (255, 255, 255)
            thickness = 2
            status = f'''{text} [{speed}]'''

            with self.camera.captured_request() as request:
                with MappedArray(request, 'main') as m:
                    cv2.putText(m.array, status, position, font, font_scale, color, thickness)
                    request.save("main", filename)
            break

        logger.info(f'''Click! [{filename}]''')


def go():
    camera = Picam()
    camera.takeStill(20)
    return

if (__name__ == "__main__"):
    go()

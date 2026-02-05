import sys
import signal
import threading
import argparse
import logging
import time

from kld7.radar import KLD7
from camera.picam import Picam
from controller.controller import Controller
from web.web import HttpInterface

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)

#making these global to attempt better clean up upon signal handling
camera = None
wif = HttpInterface()
controller = Controller()

def handle_signal(signum, frame):
    logger.info(f'''caught signal [{signum}]frame{frame}] thread[{threading.current_thread().name}]. exiting''')
    controller.stop()
    wif.stop()
    sys.exit()

def main():

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="serial port", required=True)
    args = parser.parse_args()

    try:
        logger.info(f'''creating KLD7''')
        radar = KLD7()

        logger.info(f'''initializing KLD7 with [{args.device}]''')
        r = radar.init(args.device)

        if (r == KLD7.RESPONSE.OK):
            logger.info(f"radar inited[{radar._inited}] with device[{args.device}]")
        else:
            logger.info(f"radar failed to init[{r}] with device[{args.device}]")
            exit

        camera = Picam()

        controller.init(radar, camera)
        wif.init(controller)

        rthread = threading.Thread(target=controller.run, name="Radar Controller", kwargs={})
        wthread = threading.Thread(target=wif.go, name="Web Interface", kwargs={})

        rthread.start()
        wthread.start()

        rthread.join()
        wthread.join()
    except Exception as e:
         logger.info(f'''caught some exception {e}''')
    finally:
        radar.disconnect()

if __name__ == "__main__":
    main()

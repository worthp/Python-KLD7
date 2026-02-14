import sys
import os
import signal
import traceback
import threading
import argparse
import logging
import time

isRaspberryPi = False
if (os.path.isfile("/boot/firmware/config.txt")):
    isRaspberryPi = True
    from camera.picam import Picam

from kld7.radar import KLD7
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
    parser.add_argument("-w", "--web_interface", help="web interface control", action='store_false')
    parser.add_argument("-r", "--radar_interface", help="radar controller control", action='store_false')
    args = parser.parse_args()

    try:
        logger.info(f'''creating KLD7''')
        radar = KLD7()

        if (args.radar_interface):
            logger.info(f'''initializing KLD7 with [{args.device}]''')
            r = radar.init(args.device)

            if (r == KLD7.RESPONSE.OK):
                logger.info(f"radar inited[{radar._inited}] with device[{args.device}]")
            else:
                logger.info(f"radar failed to init[{r}] with device[{args.device}]")
                exit

        if (isRaspberryPi and args.radar_interface):
            camera = Picam()
            controller.init(radar, camera)
        else:
            controller.init(radar)

        wif.init(controller)

        rthread = threading.Thread(target=controller.run, name="Radar Controller", kwargs={})
        wthread = threading.Thread(target=wif.go, name="Web Interface", kwargs={})

        threads = []
        if (args.radar_interface):
            threads.append(rthread)
            rthread.start()
        if (args.web_interface):
            threads.append(wthread)
            wthread.start()

        for t in threads:
            t.join()
    except Exception as e:
        traceback.print_exc()
        logger.info(f'''caught some exception {e}''')
    finally:
        radar.disconnect()
        

if __name__ == "__main__":
    main()

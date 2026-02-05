import sys
import signal
import threading
import argparse
import time
from kld7.radar import KLD7
from controller.controller import Controller

from web.web import HttpInterface

camera = None
wif = HttpInterface()
controller = Controller()

def handle_signal(signum, frame):
    print(f'''caught signal [{signum}]frame{frame}] thread[{threading.current_thread().name}]. exiting''')
    controller.stop()
    wif.stop()
    sys.exit()

def main():

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="which device")
    args = parser.parse_args()

    try:
        radar = KLD7()

        r = radar.init(args.device)

        if (r == KLD7.RESPONSE.OK):
            print(f"radar inited[{radar._inited}] with device[{args.device}]")
        else:
            print(f"radar failed to init[{r}] with device[{args.device}]")
            exit

        controller.init(radar, camera)
        wif.init(controller)

        rthread = threading.Thread(target=controller.run, name="Radar Controller", kwargs={})
        wthread = threading.Thread(target=wif.go, name="Web Interface", kwargs={})
        rthread.start()
        wthread.start()

        rthread.join()
        wthread.join()
    except Exception as e:
         print(f'caught some exception {e}')
    finally:
        radar.disconnect()

if __name__ == "__main__":
    main()
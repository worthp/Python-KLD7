import sys
import threading
import argparse
import time
from kld7.radar import KLD7
from controller.controller import Controller

from web.web import HttpInterface

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="which device")
    args = parser.parse_args()

    try:

        radar = KLD7()
        try:
            r = radar.init(args.device)

            if (r == KLD7.RESPONSE.OK):
                print(f"radar inited[{radar._inited}] with device[{args.device}]")
            else:
                print(f"radar failed to init[{r}] with device[{args.device}]")
                exit
        except Exception as e:
            print (e)
            

        camera = None
        controller = Controller()
        controller.init(radar, camera)

        wif = HttpInterface()
        wif.init(controller)

        rthread = threading.Thread(target=controller.run)
        wthread = threading.Thread(target=wif.go, kwargs={})
        rthread.start()
        wthread.start()

        rthread.join()
        wthread.join()
    except Exception as e:
         print(f'caught some exception {e}')
    finally:
        if (radar._inited == True):
            radar.disconnect()
        print('KLD7 exiting')

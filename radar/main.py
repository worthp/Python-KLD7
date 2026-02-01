import sys
import threading
import argparse
import time
from kld7.radar import KLD7, run

from web.HttpRequestHandler import handleHttpRequests


if __name__ == "__main__":
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
            
        rthread = threading.Thread(target=run, args=(radar,), kwargs={"oneShot":False})
        rthread.start()

        wthread = threading.Thread(target=handleHttpRequests, args=(radar,), kwargs={})
        wthread.start()

        rthread.join()
        wthread.join()
    except Exception as e:
         print(f'caught some exception {e}')
    finally:
        if (radar._inited == True):
            radar.disconnect()
        print('KLD7 exiting')

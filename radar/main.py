import threading
import argparse
import time
from kld7.kld7 import KLD7
from web.HttpRequestHandler import handleHttpRequests

radar = KLD7()

    

def kld7(device):
    try:
        r = radar.init(device)

        if (r == KLD7.RESPONSE.OK):
            print(f"radar inited[{radar._inited}] with device[{radar._device}]")
        else:
            print(f"radar failed to init[{r}]")
            return
            
        radar.setParameter('THOF', 30)
            
        print(radar.getParameterSettings())
        
        while True:
            distance, speed, angle, magnitude = radar.getTDAT()
            if (speed != None):
                print(f's[{speed}] d[{distance}] a[{angle}] m[{magnitude}]')
            else:
                print('nothing detected')
                
            time.sleep(0.005)

    except Exception as e:
            print(f"radar exception [{e}]")
    finally:
            r = radar.disconnect()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="which device")
    args = parser.parse_args()

    try:
        rthread = threading.Thread(target=kld7, args=(args.device,))
        rthread.start()

        wthread = threading.Thread(target=handleHttpRequests, args=(radar,), kwargs={})
        wthread.start()
        wthread.join()
        rthread.join()
    except Exception as e:
         print(f'caught some exception {e}')
    finally:
        radar.disconnect()
        print('KLD7 exiting')

import threading
import argparse
import time
from kld7.kld7 import KLD7
from web.HttpRequestHandler import handleHttpRequests

radar = KLD7()

def web():

    t = threading.Thread(target=handleHttpRequests, args=(radar,), kwargs={})
    t.start()
    

def kld7(device):
    r = radar.init(device)
    print(f"radar init response[{r}]")

    if (r == KLD7.RESPONSE.OK):
        print(f"radar inited[{radar._inited}] with device[{radar._device}]")
    else:
        print(f"radar failed to init[{r}]")
        
    print(radar.getParameterSettings())
    
    for i in range(250):
        distance, speed, angle, magnitude = radar.getTDAT()
        if (speed != None):
            print(f's[{speed}] d[{distance}] a[{angle}] m[{magnitude}]')
        else:
            print('nothing detected')

    r = radar.disconnect()
    print(f"radar disconnect response[{r}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="which device")
    fu = parser.parse_args()

    t = threading.Thread(target=kld7, args=(fu.device,))
    t.start()
    web()

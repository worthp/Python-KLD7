import sys
import time
import threading
from kld7.radar import KLD7
#from camera.picam import Picam

class Controller:
    def __init__ (self):
        self.radar:KLD7 = None
        self.camera = None
        self._maxTDATReadings = 10
        self._TDATReadings = []
        self._lastTDATReadingIndex = -1
        
        self._lastTrackedReadingTime = 0

        self.threadLock = threading.RLock()

        return
    
    def __del__ (self):
        # do what we can to get __del__() called
        self.radar = None
        self.camera = None
        return
    
    #def init(self, radar:KLD7, camera:Picam):
    def init(self, radar:KLD7, camera):
        self.radar = radar
        self.camera = camera
    
    def getInitTime(self):
        return self.radar._init_time
    
    def getLastTDATReadings(self):
        """
        return array of last readings newest to oldest. newest is always top 
        of the array. lastTDATReadingIndex is the dividing line
        
        :param self: Description
        """
        with self.threadLock:
            readings = []
            for i in range(self._lastTDATReadingIndex, -1, -1):
                readings.append(self._TDATReadings[i])
            for i in range(len(self._TDATReadings)-1, self._lastTDATReadingIndex, -1):
                readings.append(self._TDATReadings[i])

        return readings

    def addTDATReading(self, reading):
        with self.threadLock:
            # need to fill it first because python is stupid
            if (len(self._TDATReadings) < self._maxTDATReadings):
                self._TDATReadings.append(reading)
                self._lastTDATReadingIndex = len(self._TDATReadings)-1
                return

            # let the wrapping start
            if (self._lastTDATReadingIndex == self._maxTDATReadings-1):
                self._lastTDATReadingIndex = -1

            self._lastTDATReadingIndex += 1
            self._TDATReadings[self._lastTDATReadingIndex] = reading

        return

    def getRadarParameters(self):
        return self.radar.getRadarParameters()

    def setParameter(self, name, value):
        return self.radar.setParameter(name, value)
    
    def run(self):

        if (not self.radar._inited):
            print("radar is not inited")
            return
            
        counter = 0
        while True:
            distance, speed, angle, magnitude = self.radar.getTDAT()
            if (speed != None):
                counter = 0

                # remember the last one
                self.addTDATReading({"millis": self._lastTrackedReadingTime,
                                "distance": distance,
                                "speed": speed,
                                "angle": angle,
                                "magnitude": magnitude})

                print(f's[{speed}] d[{distance}] a[{angle}] m[{magnitude}]')
            else:
                if (counter > 1000):
                    sys.stdout.write('*')
                    sys.stdout.flush()
                    counter = 0

                counter += 1
                
            time.sleep(0.033)

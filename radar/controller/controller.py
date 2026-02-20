import sys
import math
import os
import time
from datetime import datetime
import threading
import traceback
import logging
from kld7.radar import KLD7

isRaspberryPi = False
if (os.path.isfile("/boot/firmware/config.txt")):
    isRaspberryPi = True
    from camera.picam import Picam
    import RPi.GPIO as GPIO

logger = logging.getLogger(__name__)

class Controller:
    def __init__ (self):
        self.isStopped = False
        self.radar:KLD7 = None
        self.speed_threshold = 15.0

        self.camera = None

        self._TDATReadings = []
        self._maxTDATReadings = 10
        self._lastTDATReadingIndex = -1
        
        self._lastTrackedReadingTime = 0

        self.stats = {}
        self.read_count = "read_count"
        self.min_speed = "min_speed"
        self.max_speed = "max_speed"
        self.min_angle = "min_angle"
        self.max_angle = "max_angle"
        self.min_distance = "min_distance"
        self.max_distance = "max_distance"
        self.min_magnitude = "min_magnitude"
        self.max_magnitude = "max_magnitude"
        self.speed_counts = "speed_counts"
        self.hourly_counts = "hourly_counts"

        # set mins to a big value so they get reset
        self.stats[self.read_count] = 0
        self.stats[self.min_speed] = 10000
        self.stats[self.max_speed] = 0
        self.stats[self.min_angle] = 10000
        self.stats[self.max_angle] = 0
        self.stats[self.min_distance] = 10000
        self.stats[self.max_distance] = 0
        self.stats[self.min_magnitude] = 10000
        self.stats[self.max_magnitude] = 0

        self.speed_buckets = [1,5,10,15,20,25,30,35,40,45,50]

        h = []
        for i in range(0, 24):
            h.append(0)
        self.stats[self.hourly_counts] = h

        h = {}
        for b in self.speed_buckets:
            h[str(b)] = 0
        self.stats[self.speed_counts] = h

        self.threadLock = threading.RLock()

        return

    def dropInBucket(self, buckets, counts, v):
        for b in buckets[::-1]:
            if v > b:
                counts[str(b)] += 1
                break
    
    def __del__ (self):
        # do what we can to get __del__() called
        self.radar = None
        self.camera = None
        return

    def stop(self):
        self.isStopped = True
    
    def init(self, radar:KLD7, camera = None):
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

    def setSpeedThreshold(self, threshold):
        self.speed_threshold = int(threshold)
    
    def getStats(self):
        return self.stats

    def resetRadarPower(self):

        if not isRaspberryPi:
            return

        radarResetPin = 20
        try :
            GPIO.setmode(GPIO.BCM)
            GPIO.setup(radarResetPin, GPIO.OUT)

            GPIO.output(radarResetPin, GPIO.HIGH)
            time.sleep(0.5)
            GPIO.output(radarResetPin, GPIO.LOW)
        finally:
            GPIO.cleanup()

        return

    def takeStill(self):
        self.camera.takeStill("0", "0")
    
    def run(self):

        if (not self.radar._inited):
            logger.info("radar is not inited")
            return
        
        try:
            counter = 0
            while not self.isStopped:
                now = datetime.now()
                distance, speed, angle, magnitude = self.radar.getTDAT()
                if (speed != None):
                    counter = 0
                    speed = int(abs(speed * 0.6212712)) # kph->mph

                    self._lastTrackedReadingTime = time.time() * 1000

                    self.addTDATReading({"millis": self._lastTrackedReadingTime,
                                    "distance": distance,
                                    "speed": speed,
                                    "angle": angle,
                                    "magnitude": magnitude})

                    logger.info(f's[{speed}] d[{distance}] a[{angle}] m[{magnitude}]')

                    self.stats[self.read_count] += 1
                    self.stats[self.min_speed] = min(speed, self.stats[self.min_speed])
                    self.stats[self.min_distance] = min(distance, self.stats[self.min_distance])
                    self.stats[self.min_angle] = min(angle, self.stats[self.min_angle])
                    self.stats[self.min_magnitude] = min(magnitude, self.stats[self.min_magnitude])
                    self.stats[self.max_speed] = max(speed, self.stats[self.max_speed])
                    self.stats[self.max_distance] = max(distance, self.stats[self.max_distance])
                    self.stats[self.max_angle] = max(angle, self.stats[self.max_angle])
                    self.stats[self.max_magnitude] = max(magnitude, self.stats[self.max_magnitude])

                    self.stats[self.hourly_counts][now.hour] += 1
                    self.dropInBucket(self.speed_buckets, self.stats[self.speed_counts], speed)
                    
                    logger.info(f'''speed [{speed}] th[{self.speed_threshold}]''')
                    if (self.camera != None and speed > self.speed_threshold):
                         self.camera.takeStill(speed, distance)

                else:
                    if (counter > 200):
                        logger.info('*')
                        counter = 0

                    counter += 1
                    
                time.sleep(0.033) # mostly arbitrary
                
            logger.info(f'''controller was stopped''')
        except Exception as e:
            traceback.print_exc()
            self.radar.disconnect()
            return

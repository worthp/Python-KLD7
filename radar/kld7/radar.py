import sys
import logging
import math
from struct import unpack
import serial
import time 
import threading

logger = logging.getLogger(__name__)

class KLD7:
    class RESPONSE():
        OK = 0
        UNKNOWN_COMMAND = 1
        INVALID_PARAMETER_VALUE = 2
        INVALID_RPST_VERSION = 3
        UART_ERROR = 4
        SENSOR_BUSY = 5
        TIMEOUT = 6

    def __del__(self):
        self.disconnect()

    def __init__(self):
        self.threadLock = threading.RLock()

        self._inited = False
        self._init_time = 0
        self._device = ''
        self.serialPort = None
        
        # this will hold the actual values when they are read as well
        self._radarParameters = {
                        "software_version":{"cmd":"None", "values":None},
                        "base_frequency":{"cmd":"RBFR", "values": {"Low":0,"Middle":1,"High":2}},
                        "maximum_speed":{"cmd":"RSPI", "values": {"12.5km/h":0,
                                                                  "25km/h": 1,
                                                                  "50km/h":2,
                                                                  "100km/h":3}},
                        "maximum_range":{"cmd":"RRAI", "values": {
                                                        "5m": 0,
                                                        "10m": 1,
                                                        "30m":2,
                                                        "100m":3
                                                        }},

                        "threshold_offset":{"cmd":"THOF", "values":{
                                                            "10dB":10,
                                                            "20dB":20,
                                                            "30dB":30,
                                                            "40dB":40,
                                                            "50dB":50,
                                                            "60dB":60
                                                            }},
                        "tracking_filter_type":{"cmd":"TRFT", "values": {
                                                            "Standard":0,
                                                            "Fast":1,
                                                            "Long":2
                                                             }},

                        "vibration_suppression":{"cmd":"VISU", "values": {
                                                                    "None":0,
                                                                    "Low":2,
                                                                    "Low-Med": 4,
                                                                    "Medium":8,
                                                                    "Medium-High":10,
                                                                    "High":12,
                                                                    "Max":16
                                                                   }},

                       "minimum_detection_distance":{"cmd":"MIRA", "values": {
                                                                    "0":0, "10":10, "20":20, "30":30, "40":40,
                                                                    "50":50, "60":60, "70":70, "80":80,
                                                                    "90":90, "100":100
                                    }},

                     "maximum_detection_distance":{"cmd":"MARA", "values": {
                                                "0":0, "10":10, "20":20, "30":30, "40":40,
                                                "50":50, "60":60, "70":70, "80":80,
                                                "90":90, "100":100
                                          }},

                     "minimum_detection_angle":{"cmd":"MIAN", "values": {
                                            "-90":-90, "-60":-60, "-45":-45, "-30":-30, "-15":-15,
                                            "0":0,
                                            "15":15, "30":30, "45":45, "60":60, "90":90,
                                       }},
                     "maximum_detection_angle":{"cmd":"MAAN", "values": {
                                            "-90":-90, "-60":-60, "-45":-45, "-30":-30, "-15":-15,
                                            "0":0,
                                            "15":15, "30":30, "45":45, "60":60, "90":90,
                                       }},
                     "minimum_detection_speed":{"cmd":"MISP", "values": {
                                            "0":0, "10":10, "20":20, "30":30, "40":40,
                                            "50":50, "60":60, "70":70, "80":80,
                                            "90":90, "100":100
                                       }},
                     "maximum_detection_speed":{"cmd":"MASP", "values": {
                                            "0":0, "10":10, "20":20, "30":30, "40":40,
                                            "50":50, "60":60, "70":70, "80":80,
                                            "90":90, "100":100
                                       }},
                     "detection_direction":{"cmd":"DEDI", "values": {
                                        "Approaching":0,
                                        "Receding":1,
                                        "Both":2
                                       }},

                     "range_threshold":{"cmd":"RATH", "values": {
                                            "0":0, "10":10, "20":20, "30":30, "40":40,
                                            "50":50, "60":60, "70":70, "80":80,
                                            "90":90, "100":100
                           }},
                     "angle_threshold":{"cmd":"ANTH", "values": {
                                            "-90":-90, "-60":-60, "-45":-45, "-30":-30, "-15":-15,
                                            "0":0,
                                            "15":15, "30":30, "45":45, "60":60, "90":90,
                                               }},
                     "speed_threshold":{"cmd":"SPTH", "values": {
                                            "0":0, "10":10, "20":20, "30":30, "40":40,
                                            "50":50, "60":60, "70":70, "80":80,
                                            "90":90, "100":100
                                               }},

                    "digital_output_1":{"cmd":"DIG1", "values": {
                                          "Direction":0, "Angle":1, "Range":2,
                                          "Speed":3, "Micro detection":4,
                                          "Not Valid":5
                                            }},

                    "digital_output_2":{"cmd":"DIG2", "values": None},
                    "digital_output_3":{"cmd":"DIG3", "values": None},
                    "hold_time":{"cmd":"HOLD", "values": None},
                    "micro_detection_retrigger":{"cmd":"MIDE", "values": None},
                    "micro_detection_sensitivity":{"cmd":"MIDS","values": None},
                    "restore_factory_settings":{"cmd":"RFSE", "values": {"Reset":0}, "value":""}
                    }

        self._software_version = None # // STRING,19,Zero-terminated String,K-LD7_APP-RFB-XXXX
        self._base_frequency = None # UINT8,1,0 = Low, 1 = Middle, 2 = High,1 = Middle
        self._maximum_speed = None #UINT8,1,0 = 12.5km/h, 1 = 25km/h, 2 = 50km/h, 3 = 100km/h,1 = 25km/h
        self._maximum_range = None #UINT8,1,0 = 5m, 1 = 10m, 2 = 30m, 3 = 100m,1 = 10m
        self._threshold_offset = None # UINT8,1,10-60 dB,30 dB
        self._tracking_filter_type = None # UINT8,1,0 = Standard, 1 = Fast detection, 2 = Long visibility,0 = Standard
        self._vibration_suppression = None # UINT8,1,0-16, 0 = No suppression, 16 = High suppression,3 = Medium suppression
        self._minimum_detection_distance = None #UINT8,1,0 – 100% of range setting,0%
        self._maximum_detection_distance = None #UINT8,1,0 – 100% of range setting,50%
        self._minimum_detection_angle = None #INT8,1,-90° to +90°,-90°
        self._maximum_detection_angle = None # INT8,1,-90° to +90°,+90°
        self._minimum_detection_speed = None # UINT8,1,0 – 100% of speed setting,0%
        self._maximum_detection_speed = None # UINT8,1,0 – 100% of speed setting,100%
        self._detection_direction = None # UINT8,1,0 = Approaching, 1 = Receding, 2 = Both,2 = Both
        self._range_threshold = None # UINT8,1,0 – 100% of range setting,10%
        self._angle_threshold = None # INT8,1,-90° to +90°,0°
        self._speed_threshold = None # UINT8,1,0 – 100% of speed setting,50%
        self._digital_output_1 = None # UINT8,1,0 = Direction, 1 = Angle, 2 = Range, 3 = Speed,", "= Micro detection,0 = Direction
        self._digital_output_2 = None # UINT8,1,0 = Direction, 1 = Angle, 2 = Range, 3 = Speed, 4 = Micro detection,1 = Angle
        self._digital_output_3 = None # UINT8,1,0 = Direction, 1 = Angle, 2 = Range, 3 = Speed, 4 = Micro detection,2 = Range
        self._hold_time = None # UINT16,2,1 – 7200s (1s – 2h), 120s
        self._micro_detection_retrigger = None # UINT8,1,0 = Off, 1 = Retrigger,0 = Off
        self._micro_detection_sensitivity = None # UINT8,1,0-9, 0=Min. sensitivity, 9=Max. sensitvity,4 = Medium sensitivity

    def init(self, device):
        if (self._inited == True):
            logger.info(f'''kld7 is already inited.''')
            return self.RESPONSE.OK

        logger.info(f'''kld7 is initializing.''')
        self._init_time = int(time.time()*1000)
        self._device = device

        # create serial object with corresponding COM Port and open it 
        logger.info(f'''creating serialPort''')
        self.serialPort =serial.Serial(self._device)
        self.serialPort.baudrate=115200
        self.serialPort.parity=serial.PARITY_EVEN
        self.serialPort.stopbits=serial.STOPBITS_ONE
        self.serialPort.bytesize=serial.EIGHTBITS

        # connect to sensor and set baudrate 
        payloadlength = (4).to_bytes(4, byteorder='little')
        value = (3).to_bytes(4, byteorder='little') # set baud rate to 2000000
        header = bytes("INIT", 'utf-8')
        cmd_init = header+payloadlength+value
        self.serialPort.write(cmd_init)

        # get response
        logger.info(f'''waiting for kld7 init response''')
        response = self.serialPort.read(9)
        if response[8] != 0:
            logger.info('Error during initialisation for K-LD7')
            return response[8]

        # change to higher baudrate based on the '3' value in the INIT payload
        self.serialPort.baudrate = 2E6
        
        # just to get them for visibility
        r = self._getRadarParameters()
        self._inited = True

        return r
    
    def _getRadarParameters(self):
        with self.threadLock:

            header = bytes("GRPS", 'utf-8')
            payloadlength = (0).to_bytes(4, byteorder='little') # all commands except grps and srps are 4 byte payloads
            cmd_frame = header+payloadlength

            self.serialPort.write(cmd_frame)

            # get response
            response = self.serialPort.read(9)
            if response[8] != 0:
                logger.info(f'[GRPS] error[{response[8]}]')
                return response[8]
            
            header, payloadLength = unpack('<4sI', self.serialPort.read(8))

            buf = self.serialPort.read(payloadLength)

            # this looks weird but there is a struct.unpack about 23 lines below here
            self._software_version,\
            self._base_frequency,\
            self._maximum_speed,\
            self._maximum_range,\
            self._threshold_offset,\
            self._tracking_filter_type,\
            self._vibration_suppression,\
            self._minimum_detection_distance,\
            self._maximum_detection_distance,\
            self._minimum_detection_angle,\
            self._maximum_detection_angle,\
            self._minimum_detection_speed,\
            self._maximum_detection_speed,\
            self._detection_direction,\
            self._range_threshold,\
            self._angle_threshold,\
            self._speed_threshold,\
            self._digital_output_1,\
            self._digital_output_2,\
            self._digital_output_3,\
            self._hold_time,\
            self._micro_detection_retrigger,\
            self._micro_detection_sensitivity\
             = unpack('<19s8B2b4Bb4BH2B', buf)
             
            # makes it easier to expose the data
            # _radarParameters also carries meta data 
            self._radarParameters["software_version"]["value"] = self._software_version.decode("utf-8")
            self._radarParameters["base_frequency"]["value"] = self._base_frequency
            self._radarParameters["maximum_speed"]["value"] = self._maximum_speed
            self._radarParameters["maximum_range"]["value"] = self._maximum_range
            self._radarParameters["threshold_offset"]["value"] = self._threshold_offset
            self._radarParameters["tracking_filter_type"]["value"] = self._tracking_filter_type
            self._radarParameters["vibration_suppression"]["value"] = self._vibration_suppression
            self._radarParameters["minimum_detection_distance"]["value"] = self._minimum_detection_distance
            self._radarParameters["maximum_detection_distance"]["value"] = self._maximum_detection_distance
            self._radarParameters["minimum_detection_angle"]["value"] = self._minimum_detection_angle
            self._radarParameters["maximum_detection_angle"]["value"] = self._maximum_detection_angle
            self._radarParameters["minimum_detection_speed"]["value"] = self._minimum_detection_speed
            self._radarParameters["maximum_detection_speed"]["value"] = self._maximum_detection_speed
            self._radarParameters["detection_direction"]["value"] = self._detection_direction
            self._radarParameters["range_threshold"]["value"] = self._range_threshold
            self._radarParameters["angle_threshold"]["value"] = self._angle_threshold
            self._radarParameters["speed_threshold"]["value"] = self._speed_threshold
            self._radarParameters["digital_output_1"]["value"] = self._digital_output_1
            self._radarParameters["digital_output_2"]["value"] = self._digital_output_2
            self._radarParameters["digital_output_3"]["value"] = self._digital_output_3
            self._radarParameters["hold_time"]["value"] = self._hold_time
            self._radarParameters["micro_detection_retrigger"]["value"] = self._micro_detection_retrigger
            self._radarParameters["micro_detection_sensitivity"]["value"] = self._micro_detection_sensitivity
         
        return 0


    def getTDAT(self):
        with self.threadLock:
            r = self.sendCommand("GNFD", 8) # 8 is for TDAT
            if (r != 0):
                logger.info(f'GNFD failed[{r}]')
                return None, None, None, None

            # look for header and payload
            tdatResponse = self.serialPort.read(8)
            if (tdatResponse[4] > 0):
                readings = self.serialPort.read(8)
                distance, speed, angle, magnitude = unpack('<HhhH', readings)
                speed = speed / 100
                angle = math.radians(angle)/100
                
                self._lastTrackedReadingTime = int(time.time() * 1000) # make secs millis

                return distance, speed, angle, magnitude
            
        return None, None, None, None

    
    def setParameter(self, name, value):

        if (name not in self._radarParameters):
            return 1
        
        cmd = self._radarParameters[name]['cmd']
        r = self.sendCommand(cmd, int(value))
        # re-read parameters just to be sure to be we're in sync
        if (r == 0):
            self._getRadarParameters()
        return r

    def sendCommand(self, cmd, value):
        if (not self._inited):
            return

        with self.threadLock:
            header = bytes(cmd, 'utf-8')

            # hack for reset.
            # it's the only cmd with zero payload except for GRPS and GBYE
            # which aren't exposed externally cuz they have completely diff semantics
            if (cmd != "RFSE"):
                payloadlength = (4).to_bytes(4, byteorder='little') # all commands except grps and srps are 4 byte payloads
                if (value < 0):
                    f = True
                else:
                    f = False

                v = (value).to_bytes(4, byteorder='little', signed=f)
                cmd_frame = header+payloadlength+v
            else:
                payloadlength = (0).to_bytes(4, byteorder='little') # all commands except grps and srps are 4 byte payloads
                cmd_frame = header+payloadlength

            if (cmd != "GNFD"):
                logger.info(f"cmd_frame[{cmd_frame}]")

            self.serialPort.write(cmd_frame)

            # get response
            response = self.serialPort.read(9)
            if response[8] != 0:
                logger.info(f'[{cmd}] error[{response[8]}]')

        return response[8]
    
    def disconnect(self):
        if (self._inited == False):
            return
        logger.info(f'''KLD7 shutting down ...''')
        with self.threadLock:
            logger.info(f'''sending BYE to sensor''')
            # disconnect from sensor 
            payloadlength = (0).to_bytes(4, byteorder='little')
            header = bytes("GBYE", 'utf-8')
            cmd_frame = header+payloadlength
            self.serialPort.write(cmd_frame)

            # get response
            response = self.serialPort.read(9)
            if response[8] == 0:
                logger.info('KLD7 acknowledged BYE')
            else:
                logger.info('Error during disconnecting with K-LD7')
                
            logger.info(f'''closing [{self._device}]''')
            self.serialPort.close()
            self._inited = False
        return response[8]
        
    def getRadarParameters(self):
        return self._radarParameters
    
    def getLastTrackedReadingTime(self):
        return self._lastTrackedReadingTime

from enum import Enum
from struct import unpack
from collections import namedtuple
import serial
import time 

class KLD7:
    class RESPONSE():
        OK = 0
        UKNOWN_COMMAND = 1
        INVALID_PARAMETER_VALUE = 2
        INVALID_RPST_VERSION = 3
        UART_ERROR = 4
        SENSOR_BUSY = 5
        TIMEOUT = 6

    def __init__(self):
        self._inited = False
        self._device = ''
        self.radar = None
        
        self._radarParameters = None
        
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
        self._digital_output_1 = None # UINT8,1,0 = Direction, 1 = Angle, 2 = Range, 3 = Speed, 4 = Micro detection,0 = Direction
        self._digital_output_2 = None # UINT8,1,0 = Direction, 1 = Angle, 2 = Range, 3 = Speed, 4 = Micro detection,1 = Angle
        self._digital_output_3 = None # UINT8,1,0 = Direction, 1 = Angle, 2 = Range, 3 = Speed, 4 = Micro detection,2 = Range
        self._hold_time = None # UINT16,2,1 – 7200s (1s – 2h), 120s
        self._micro_detection_retrigger = None # UINT8,1,0 = Off, 1 = Retrigger,0 = Off
        self._micro_detection_sensitivity = None # UINT8,1,0-9, 0=Min. sensitivity, 9=Max. sensitvity,4 = Medium sensitivity

    def init(self, device):
        self._inited = True
        self._device = device

        # create serial object with corresponding COM Port and open it 
        self.radar =serial.Serial(self._device)
        self.radar.baudrate=115200
        self.radar.parity=serial.PARITY_EVEN
        self.radar.stopbits=serial.STOPBITS_ONE
        self.radar.bytesize=serial.EIGHTBITS

        # connect to sensor and set baudrate 
        payloadlength = (4).to_bytes(4, byteorder='little')
        value = (3).to_bytes(4, byteorder='little') # set baud rate to 2000000
        header = bytes("INIT", 'utf-8')
        cmd_init = header+payloadlength+value
        self.radar.write(cmd_init)

        # get response
        response = self.radar.read(9)
        if response[8] != 0:
            print('Error during initialisation for K-LD7')

        # change to higher baudrate based on the '3' value in the INIT payload
        self.radar.baudrate = 2E6

        return response[8]
    
    def getRadarParameters(self):
        header = bytes("GRPS", 'utf-8')
        payloadlength = (0).to_bytes(4, byteorder='little') # all commands except grps and srps are 4 byte payloads
        cmd_frame = header+payloadlength

        self.radar.write(cmd_frame)

        # get response
        response = self.radar.read(9)
        if response[8] != 0:
            print(f'[GRPS] error[{response[8]}]')
            return response[8]
        
        header, payloadLength = unpack('<4sI', self.radar.read(8))
        print(f'header[{header}] length[{payloadLength}]')

        self.radarParameters = self.radar.read(payloadLength)

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
        self._micro_detection_sensitivity,\
         = unpack('<19s8B2b4Bb4BH2B', self.radarParameters)

    
    def setParameter(self, name, value):
        self.sendCommand(name, value)

    def sendCommand(self, cmd, value):
        header = bytes(cmd, 'utf-8')
        payloadlength = (4).to_bytes(4, byteorder='little') # all commands except grps and srps are 4 byte payloads
        v = (value).to_bytes(4, byteorder='little') # set baud rate to 2000000
        cmd_frame = header+payloadlength+v

        self.radar.write(cmd_frame)

        # get response
        response = self.radar.read(9)
        if response[8] != 0:
            print(f'[{cmd}] error[{response[8]}]')

        return response[8]
    
    def disconnect(self):
        # disconnect from sensor 
        payloadlength = (0).to_bytes(4, byteorder='little')
        header = bytes("GBYE", 'utf-8')
        cmd_frame = header+payloadlength
        self.radar.write(cmd_frame)

        # get response
        response = self.radar.read(9)
        if response[8] != 0:
            print('Error during disconnecting with K-LD7')
            
            
        self.radar.close()
        return response[8]
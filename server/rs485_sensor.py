import RPi.GPIO as GPIO
import serial
import struct
import time
from modbus_crc import add_crc
class Sensor:
    def __init__(self, port:str, bound:int) -> None:
        EN_485 =  4
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(EN_485,GPIO.OUT)
        GPIO.output(EN_485,GPIO.HIGH)
        self.t = serial.Serial(port,bound)
    def ReadValue(self, req:bytes) -> bytes:
        req_crc = add_crc(req)
        n = self.t.write(req_crc)
        time.sleep(0.01)
        str = self.t.read(9)
        
        return str
    def ReadTemp(self) -> float:
        res = self.ReadValue(b'\x01\x03\x00\x08\x00\x02')
        return struct.unpack('>f', res[3:7])[0]
    def ReadP1(self) -> float:
        res = self.ReadValue(b'\x01\x03\x00\x02\x00\x02')
        return struct.unpack('>f', res[3:7])[0]
    def ReadP2(self) -> float:
        res = self.ReadValue(b'\x01\x03\x00\x04\x00\x02')
        return struct.unpack('>f', res[3:7])[0]
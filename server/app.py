
import ctypes
import socket
from queue import Queue,Empty
from threading import Thread
import time
from someip.someip_header import SomeIPHeader
import struct
from rs485_sensor import Sensor
import time
import sys
import RPi.GPIO as GPIO
from hx711 import HX711
from ds18b20 import DS18B20
from servo import Servo
# ADAPTER_IP = '192.168.11.101'
LOCAL_IP = '0.0.0.0'
# PORT = 10000
PORTRX = 10000

global flag
flag = True
global client_list
client_list = []
servo_list:list(Servo)=[]

send_queue=Queue()

tenso_val = 0

tar_flag = False

referenceUnit = 110.29
class client:
    def __init__(self, ip:str, port:int) -> None:
        self.ip = ip
        self.port = port

def tx_communication_thread(send_queue:Queue):
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        while True:
            sendEvent(send_queue.get(True,0.01))


def rx_comunication_thread():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM,socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((LOCAL_IP, PORTRX))
    # wrong: mreq = struct.pack("sl", socket.inet_aton("224.51.105.104"), socket.INADDR_ANY)
    mreq = struct.pack("=4sl", socket.inet_aton("224.51.105.104"), socket.INADDR_ANY)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
    socket.setdefaulttimeout(0.0)
    global flag
    while flag:
        someiph = SomeIPHeader(0x00,0x00)
        hex = sock.recv(10240)
        someiph.read(hex)
        if(someiph.service_id == 0x01 and someiph.methode_id == 0x01):
            payload = hex[16:]
            ip = ''    
            ip = ip + str(payload[0])+"."
            ip = ip + str(payload[1])+"."
            ip = ip + str(payload[2])+"."
            ip = ip + str(payload[3])
            port = int.from_bytes(payload[4:6],byteorder="big",signed=False)
            global client_list
            new_c = client(ip,port)
            res = False
            for obj in client_list:
                if obj.ip == new_c.ip and obj.port == new_c.port:
                    res = True

            if not res:
                client_list.append(new_c)
                print("IP: "+ip + ":"+str(port))
        elif(someiph.service_id == 0x01 and someiph.methode_id == 0x02):
            payload = hex[16:]
            val = struct.unpack("f",payload)[0]
            global referenceUnit
            referenceUnit = val
            global tar_flag
            tar_flag = True
        elif(someiph.service_id== 0x01 and someiph.methode_id ==0x03):
            payload=hex[16:]
            pin=int.from_bytes(payload[0:1],byteorder="big",signed=False)
            value=int.from_bytes(payload[1:],byteorder="big",signed=False)
            obj=next((obj for obj in servo_list if obj.pin == pin),None)
            if obj is None:
                servo_list.append(Servo(pin,value))
            else:
                obj.changeValue(value)

        


def sendEvent(data:bytes):
    sock = socket.socket(socket.AF_INET,  # Internet
                             socket.SOCK_DGRAM)  # UDP
    global client_list
    for obj in client_list:
        sock.sendto(data, (obj.ip, obj.port))
def read_raw_Volt(ch):
    read = 0
    try:
        f = open("/sys/bus/iio/devices/iio:device0/in_voltage"+str(ch)+"_raw",'r')
        read = f.read()
    except:
        pass
    f.close()
    return int(read)
def read_scale(ch):
    read = -1
    try:
        f = open("/sys/bus/iio/devices/iio:device0/in_voltage"+str(ch)+"_scale",'r')
        read = f.read()
    except:
        pass
    f.close()
    return float(read)
def hx711_loop():
    global referenceUnit
    hx = HX711(5, 6)
    hx.set_reading_format("MSB", "MSB")
    hx.set_reference_unit(referenceUnit)
    hx.reset()
    hx.tare()
    print("Tare done! Add weight now...")
    while True:
        global tar_flag
        if(not tar_flag):
            global tenso_val
            tenso_val = hx.get_weight(1)
            hx.power_down()
            hx.power_up()
            time.sleep(0.1)
        else:
            # global referenceUnit
            hx.set_reference_unit(referenceUnit)
            hx.reset()
            hx.tare()
            print("Tare done! Add weight now...")

def read_Volt(ch):
    return volt_convert(float(read_raw_Volt(ch)),read_scale(ch))
def volt_convert(raw,scale):
    return raw*scale/1000.0
def loop():
    rs_sensor = Sensor("/dev/ttyS0",9600)
    t1=DS18B20(send_queue)
    t1.start()
    while True:
        header = SomeIPHeader(0x01,0x8001,0x02)
        
        val = rs_sensor.ReadP1()
        send_queue.put_nowait(b''.join(header.GetSomeIPDataPayload(struct.pack("f", val))))
        val = rs_sensor.ReadTemp()
        header = SomeIPHeader(0x01,0x8002,0x02)
        send_queue.put_nowait(b''.join(header.GetSomeIPDataPayload(struct.pack("f", val))))
        header = SomeIPHeader(0x01,0x8003,0x02)
        send_queue.put_nowait(b''.join(header.GetSomeIPDataPayload(struct.pack("f", read_Volt(0)))))
        header = SomeIPHeader(0x01,0x8004,0x02)
        send_queue.put_nowait(b''.join(header.GetSomeIPDataPayload(struct.pack("f", read_Volt(1)))))
        header = SomeIPHeader(0x01,0x8005,0x02)
        send_queue.put_nowait(b''.join(header.GetSomeIPDataPayload(struct.pack("f", read_Volt(2)))))
        header = SomeIPHeader(0x01,0x8006,0x02)
        global tenso_val
        send_queue.put_nowait(b''.join(header.GetSomeIPDataPayload(struct.pack("f", tenso_val))))
        header=SomeIPHeader(0x01,0x8007,0x02)
        sendmsg=0


def main():
    t2 = Thread(target=rx_comunication_thread,daemon=True)
    t2.start()
    t3 = Thread(target=hx711_loop,daemon=True)
    t3.start()
    tx_thread=Thread(target=tx_communication_thread,daemon=True,args=[send_queue])
    tx_thread.start()
    loop()

if __name__ == "__main__":
    main()

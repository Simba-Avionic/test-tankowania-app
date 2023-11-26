import socket
from someip import SomeIPHeader
import ctypes
import struct
import csv
import datetime
import keyboard
import time
import threading


tm=datetime.datetime.now()
filename=f"data_{tm.hour};{tm.minute};{tm.second}.csv"
temp:float=None
pressuer:float=None
A0:float=None
A1:float=None
A2:float=None
tenso:float=None
d_temp:float=None
d_pressuer:float=None
d_A0:float=None
d_A1:float=None
d_A2:float=None
d_tenso:float=None

firstTime=True
stop=False



with open(file=filename,mode='w',encoding='UTF-8') as csvFile:
    writer=csv.writer(csvFile,delimiter=";")
    writer.writerow(['TIMESTAMP','TEMP',"PRESURE","A0","A1","A2","TENSO"])

is_s_pressed=False
is_k_pressed=False


def check_for_s():
    global is_s_pressed
    global is_k_pressed
    global stop
    while not stop:
        if keyboard.is_pressed('s'):
            is_s_pressed=True
            time.sleep(0.1)
        if keyboard.is_pressed('k'):
            is_k_pressed=True
            print("k is presed")
            time.sleep(0.3)

def printThread():
    global d_temp
    global d_pressuer
    global d_A0
    global d_A1
    global d_A2
    global d_tenso
    global stop
    while not stop:
        os.system('cls')
        print(f"temp:{d_temp}")
        print(f"pressure:{d_pressuer}")
        print(f"A0:{d_A0}")
        print(f"A1:{d_A1}")
        print(f"A2:{d_A2}")
        print(f"tenso:{d_tenso}")
        time.sleep(1)



print_thread=threading.Thread(target=printThread)
key_thread=threading.Thread(target=check_for_s)

print_thread.start()
key_thread.start()


H_HOST = "192.168.137.221" # RPI HOST
H_PORT = 10000 # RPI PORT
R_PORT = 10101 # THIS APP PORT
R_HOST = "192.168.137.199" # THIS APP HOST

with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
    initHeader=SomeIPHeader(0x01,0x01)
    R_PORT_bytes=R_PORT.to_bytes(2,byteorder='big')
    R_HOST_bytes=socket.inet_aton(R_HOST)
    payload=R_HOST_bytes+R_PORT_bytes
    initHeader.GetSomeIPDataPayload(b'\xc0\xa8\x0b\x65\x27\x75')
    MSG=b''.join(initHeader.GetSomeIPDataPayload(payload))
    s.sendto(MSG,(H_HOST,H_PORT))
    s.close()


with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
    s.bind(("0.0.0.0",R_PORT))
    while True:
        try:
            if is_k_pressed:
                is_k_pressed=False
            if is_s_pressed and firstTime:
                startTime=datetime.datetime.now()
                firstTime=False
            if temp is not None and pressuer is not None and A0 is not  None and A1 is not None and A2 is not None:
                timestamp=datetime.datetime.now()-startTime
                with open(filename,'a',encoding='UTF-8',newline='') as csvFile:
                    writer=csv.writer(csvFile,delimiter=";")
                    writer.writerow([timestamp,temp,pressuer,A0,A1,A2,tenso])
                temp=None
                pressuer=None
                A0=None
                A1=None
                A2=None
                tenso=None
            data=s.recv(100)
            if(data==0):
                break
            d=SomeIPHeader(0x00,0x00)
            d.read(data)
            payload=data[16:]
            if hex(d.methode_id)=="0x8001":
                d_pressuer=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    pressuer=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8002":
                d_temp=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    temp=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8003":
                d_A0=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    A0=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8004":
                d_A1=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    A1=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8005":
                d_A2=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    A2=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8006":
                d_tenso=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    tenso=struct.unpack('f',payload)[0]
        except (KeyboardInterrupt,SystemExit):
            exit(0)


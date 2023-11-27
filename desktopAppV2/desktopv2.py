import threading
import socket
import time
import curses
import socket
import struct
from someip import SomeIPHeader
import datetime
import csv
from config import *

class Data:
    def __init__(self):
        self.temp:float=None
        self.pressuer:float=None
        self.A0:float=None
        self.A1:float=None
        self.A2:float=None
        self.tenso:float=None
        self.d_temp:float=None
        self.d_pressuer:float=None
        self.d_A0:float=None
        self.d_A1:float=None
        self.d_A2:float=None
        self.d_tenso:float=None

rpiData=Data()

stop=False
is_s_pressed=False




stdscr = curses.initscr()
curses.cbreak()
curses.noecho()
stdscr.keypad(True)

def sendData(data:bytes,Host:str,Port:int):
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.sendto(data,(Host,Port))
        s.close()

def sendSomeIPMsg(service_id:hex,method_id:hex,payload:bytes,Host:str,Port:int):
    header=SomeIPHeader(service_id,method_id)
    msg=b''.join(header.GetSomeIPDataPayload(payload))
    sendData(msg,Host,Port)


def display_thread():
    global rpiData
    global stop
    data=[f"temp:{rpiData.d_temp}",f"pressure:{rpiData.d_pressuer}",f"A0:{rpiData.d_A0}",
f"A1:{rpiData.d_A1}",f"A2:{rpiData.d_A2}",f"tenso:{rpiData.d_tenso}"]
    while not stop:
        stdscr.clear()
        for i,line in enumerate(data,start=1):
            stdscr.addstr(i, 0, line)
        stdscr.refresh()
        time.sleep(1)

def socket_thread():
    global rpiData
    global R_PORT
    global is_s_pressed
    global stop
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.bind(("0.0.0.0",R_PORT))
        while not stop:
            da=s.recv(100)
            if(da==0):
                break
            d=SomeIPHeader(0x00,0x00)
            d.read(da)
            payload=da[16:]
            if hex(d.methode_id)=="0x8001":
                rpiData.d_pressuer=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    rpiData.pressuer=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8002":
                rpiData.d_temp=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    rpiData.temp=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8003":
                rpiData.d_A0=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    rpiData.A0=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8004":
                rpiData.d_A1=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    rpiData.A1=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8005":
                rpiData.d_A2=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    rpiData.A2=struct.unpack('f',payload)[0]
            elif hex(d.methode_id)=="0x8006":
                rpiData.d_tenso=struct.unpack('f',payload)[0]
                if is_s_pressed:
                    rpiData.tenso=struct.unpack('f',payload)[0]

def file_thread():
    global rpiData
    global is_s_pressed
    global stop
    first_time=True
    tm=datetime.datetime.now()
    filename=f"data_{tm.hour};{tm.minute};{tm.second}.csv"
    with open(file=filename,mode='w',encoding='UTF-8') as csvFile:
        writer=csv.writer(csvFile,delimiter=";")
        writer.writerow(['TIMESTAMP','TEMP',"PRESURE","A0","A1","A2","TENSO"])
    while not stop:
        if is_s_pressed and first_time:
            startTime=datetime.datetime.now()
            firstTime=False
        if rpiData.temp is not None and rpiData.pressuer is not None and rpiData.A0 is not  None and rpiData.A1 is not None and rpiData.A2 is not None and rpiData.tenso is not None:
            timestamp=datetime.datetime.now()-startTime
            with open(filename,'a',encoding='UTF-8',newline='') as csvFile:
                writer=csv.writer(csvFile,delimiter=";")
                writer.writerow([timestamp,rpiData.temp,rpiData.pressuer,
                                 rpiData.A0,rpiData.A1,rpiData.A2,rpiData.tenso])
            rpiData.temp=None
            rpiData.pressuer=None
            rpiData.A0=None
            rpiData.A1=None
            rpiData.A2=None
            rpiData.tenso=None

def user_input_thread():
    global is_s_pressed
    global stop
    try:
        while not stop:
            key = stdscr.getch()
            if key != curses.ERR:
                user_input = chr(key)
                if user_input=='k':
                    sendSomeIPMsg(0x01,0x02,b'',H_HOST,H_PORT)
                if user_input=='s':
                    is_s_pressed=True
            time.sleep(0.2)
    except KeyboardInterrupt:
        stop=True

R_PORT_bytes=R_PORT.to_bytes(2,byteorder='big')
R_HOST_bytes=socket.inet_aton(R_HOST)
payload=R_HOST_bytes+R_PORT_bytes

sendSomeIPMsg(0x01,0x01,payload,H_HOST,H_PORT)

display_thread = threading.Thread(target=display_thread)
socket_thread = threading.Thread(target=socket_thread)
file_thread = threading.Thread(target=file_thread)
user_input_thread = threading.Thread(target=user_input_thread)

display_thread.start()
socket_thread.start()
file_thread.start()
user_input_thread.start()

try:
    display_thread.join()
    print("Display thread joined.")
    socket_thread.join()
    print("Socket thread joined.")
    file_thread.join()
    print("File thread joined.")
    user_input_thread.join()
    print("User input thread joined.")
except KeyboardInterrupt:
    pass
finally:
    stop=True
    curses.endwin()
    exit(0)

import flet
from flet import TextButton,Page,Column,Row,Text
import socket
from someip import SomeIPHeader
from threading import Thread,Event
import struct
import time
import datetime
import csv
from sys import exit,argv

def calculete_pressure(num:float)->float:
    num+=0.008
    print(num, 61.875*num, (61.875*num)-23.75)
    return (61.875*num)-23.75



def get_local_ip():
    try:
        # Tworzymy gniazdo i łączymy się z dowolnym adresem i portem (nie jest to rzeczywiste połączenie, służy tylko do uzyskania lokalnego adresu IP)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Adres IP Google DNS i dowolny port
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception as e:
        print(f"Błąd podczas uzyskiwania lokalnego adresu IP: {e}")
        return None

H_HOST = "192.168.11.100" # RPI HOST
H_PORT = 10000 # RPI PORT
R_PORT = 10101 # THIS APP PORT
R_HOST = "192.168.11.101" # THIS APP HOST

run=True

class Data:
    def __init__(self):
        self.pressure=None
        self.temp=None
        self.A0=None
        self.A1=None
        self.A2=None
        self.tenso=None
        self.Tg=None
        self.Ts=None
        self.Td=None

    def is_None(self):
        if self.pressure is None or self.temp is None or self.A1 is None or self.tenso is None:
            return True
        return False

displayed_data=Data()
to_save_data=Data()

save_is_run=False
stop_saving=Event()

def startSave():
    global stop_saving
    tm=datetime.datetime.now()
    filename=f"data_{tm.hour};{tm.minute};{tm.second}.csv"
    with open(file=filename,mode='w',encoding='UTF-8') as csvFile:
        writer=csv.writer(csvFile,delimiter=";")
        writer.writerow(['TIMESTAMP','TEMP',"PRESURE","A1","TENSO","Tg","Ts","Td"])
    startTime=datetime.datetime.now()
    while not stop_saving.is_set():
        if to_save_data.is_None() is False:
            timestamp=datetime.datetime.now()-startTime
            with open(filename,'a',encoding='UTF-8',newline='') as csvFile:
                writer=csv.writer(csvFile,delimiter=";")
                writer.writerow([timestamp,to_save_data.temp,
                        to_save_data.pressure,to_save_data.A1,to_save_data.tenso,
                        to_save_data.Tg,to_save_data.Ts,to_save_data.Td])
            to_save_data.temp=None
            to_save_data.pressure=None
            to_save_data.A0=None
            to_save_data.A1=None
            to_save_data.A2=None
            to_save_data.tenso=None   




def receiverThreadFunc():
    run=True
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.bind(("0.0.0.0",R_PORT))
        try:
            while run:
                data=sock.recv(150)
                if len(data)==0:
                    break
                someipHeader=SomeIPHeader(0x00,0x00)
                someipHeader.read(data)
                payload=data[16:]
                if hex(someipHeader.methode_id)=="0x8001":
                    displayed_data.pressure=round(struct.unpack('f',payload)[0],6)
                    to_save_data.pressure=struct.unpack('f',payload)[0]
                elif hex(someipHeader.methode_id)=="0x8002":
                    displayed_data.temp=round(struct.unpack('f',payload)[0],6)
                    to_save_data.temp=struct.unpack('f',payload)[0]
                elif hex(someipHeader.methode_id)=="0x8003":
                    displayed_data.A0=round(struct.unpack('f',payload)[0],6)
                    to_save_data.A0=struct.unpack('f',payload)[0]
                elif hex(someipHeader.methode_id)=="0x8004":
                    displayed_data.A1=round(calculete_pressure(struct.unpack('f',payload)[0]),6)
                    to_save_data.A1=struct.unpack('f',payload)[0]
                elif hex(someipHeader.methode_id)=="0x8005":
                    displayed_data.A2=round(struct.unpack('f',payload)[0],6)
                    to_save_data.A2=struct.unpack('f',payload)[0]
                elif hex(someipHeader.methode_id)=="0x8006":
                    displayed_data.tenso=round(struct.unpack('f',payload)[0],6)
                    to_save_data.tenso=struct.unpack('f',payload)[0]
                elif hex(someipHeader.methode_id)=="0x8007":
                    sensor=payload[4:].decode("UTF-8")
                    if sensor=='28-062018f00883':
                        displayed_data.Tg=round(struct.unpack('f',payload[:4])[0],2)
                        to_save_data.Tg=struct.unpack('f',payload[:4])[0]
                    elif sensor=='28-3c29e381356d':
                        displayed_data.Ts=round(struct.unpack('f',payload[:4])[0],2)
                        to_save_data.Ts=struct.unpack('f',payload[:4])[0]
                    elif sensor=='28-3c01e076e761':
                        displayed_data.Td=round(struct.unpack('f',payload[:4])[0],2)
                        to_save_data.Td=struct.unpack('f',payload[:4])[0]

        except KeyboardInterrupt:
            run=False
            time.sleep(0.1)
    sock.close()


def sendData(data:bytes,Host:str,Port:int):
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
        s.sendto(data,(Host,Port))
        s.close()
    

def sendSomeIPMsg(service_id:hex,method_id:hex,payload:bytes,Host:str,Port:int):
    header=SomeIPHeader(service_id,method_id)
    msg=b''.join(header.GetSomeIPDataPayload(payload))
    sendData(msg,Host,Port)

def run_thread():
    global save_is_run
    global stop_saving
    if save_is_run==False:
        stop_saving.clear()
        Thread(target=startSave).start()
        save_is_run=True

def stop_thread():
    global save_is_run
    global stop_saving
    if save_is_run==True:
        stop_saving.set()
        save_is_run=False

def sendTaraThreadFunc(e):
    th=Thread(target=lambda:sendSomeIPMsg(0x01,0x02,b'',H_HOST,H_PORT))
    th.start()

receiverThread=Thread(target=receiverThreadFunc,daemon=True)

def main(page:Page):
    global H_HOST
    if len(argv)>1:
        H_HOST=argv[1]
    page.window_width=350
    page.window_height=500
    try:
        global run
        receiverThread.start()
        def sendInitMsg():
            R_PORT_bytes=R_PORT.to_bytes(2,byteorder='big')
            R_HOST_bytes=socket.inet_aton(R_HOST)
            init_payload=R_HOST_bytes+R_PORT_bytes
            sendSomeIPMsg(0x01,0x01,init_payload,H_HOST,H_PORT)


        page.title="Engine test app"
        page.vertical_alignment="center"

        sendInitMsg()
        while run:
            page.add(flet.DataTable(
                columns=[
                    flet.DataColumn(flet.Text("name")),
                    flet.DataColumn(flet.Text("value"),numeric=True)
                ],
                rows=[
                    flet.DataRow(
                        cells=[
                            flet.DataCell(flet.Text("pressure")),
                            flet.DataCell(flet.Text(displayed_data.pressure))
                        ]
                    ),
                    flet.DataRow(
                        cells=[
                            flet.DataCell(flet.Text("temp")),
                            flet.DataCell(flet.Text(displayed_data.temp))
                        ]
                    ),
                    flet.DataRow(
                        cells=[
                            flet.DataCell(flet.Text("A1")),
                            flet.DataCell(flet.Text(displayed_data.A1))
                        ]
                    ),
                    flet.DataRow(
                        cells=[
                            flet.DataCell(flet.Text("tenso")),
                            flet.DataCell(flet.Text(displayed_data.tenso))
                        ]
                    ),
                                        flet.DataRow(
                        cells=[
                            flet.DataCell(flet.Text("temp góra")),
                            flet.DataCell(flet.Text(displayed_data.Tg))
                        ]
                    ),
                    flet.DataRow(
                        cells=[
                            flet.DataCell(flet.Text("temp środek")),
                            flet.DataCell(flet.Text(displayed_data.Ts))
                        ]
                    ),
                    flet.DataRow(
                        cells=[
                            flet.DataCell(flet.Text("tmp dół")),
                            flet.DataCell(flet.Text(displayed_data.Td))
                        ]
                    )
                ]
            ))
            page.add(
            Row([
                TextButton("Tara",on_click=sendTaraThreadFunc),
                TextButton("Start Save",on_click=lambda e:run_thread()),
                TextButton("Stop Save",on_click=lambda e:stop_thread())
            ])
        )
            time.sleep(1)
            page.clean()
    except KeyboardInterrupt:
        run=False
        receiverThread.join()




flet.app(target=main)
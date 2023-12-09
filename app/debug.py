import socket
from SomeIPHeader import SomeIPHeader
import ctypes
import struct
import random
import time
from queue import Queue
import threading
from threading import Event

first=True
HOST="127.0.0.1"
PORT=10101

stop_event=Event()

class Client:
    def __init__(self,host,port):
        self.Host=host
        self.Port=port

class Clients:
    def __init__(self):
        self.clients:dict(Client)=[]

    def clientInList(self,client:Client):
        for c in self.clients:
            if c.Host==client.Host and c.Port==client.Port:
                return True
        return False

    def addClient(self,client:Client):
        if not self.clientInList(client):
            self.clients.append(client)
            print(f"{client.Host}:{client.Port}")
        else:
            print("client alreagy added")


que=Queue()
clients=Clients()

def addClientThreadFunc():
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        sock.bind(("0.0.0.0",10000))
        while not stop_event.is_set():
            data=sock.recv(100)
            if len(data)==0:
                break
            HOST=socket.inet_ntoa(data[16:20])
            PORT=struct.unpack('>H',data[20:22])[0]
            clients.addClient(Client(HOST,PORT))


def sendThredFunc():
    with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as sock:
        while not stop_event.is_set():
            if que.empty() is False:
                msg=que.get(block=False)
                for client in clients.clients:
                    sock.sendto(msg,(client.Host,client.Port))
            else:
                time.sleep(0.1)


def readSensorsFunc():
    while not stop_event.is_set():
        hdr=SomeIPHeader(0x01,0x8002)
        payload=struct.pack('f',random.uniform(20,25))
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        hdr=SomeIPHeader(0x01,0x8001)
        payload=struct.pack('f',random.uniform(0,15))
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        hdr=SomeIPHeader(0x01,0x8003)
        payload=struct.pack('f',random.uniform(0,3.3))
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        hdr=SomeIPHeader(0x01,0x8004)
        payload=struct.pack('f',random.uniform(0,3.3))
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        hdr=SomeIPHeader(0x01,0x8005)
        payload=struct.pack('f',random.uniform(0,3.3))
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        hdr=SomeIPHeader(0x01,0x8006)
        payload=struct.pack('f',random.uniform(0,10000))
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        hdr=SomeIPHeader(0x01,0x8007)
        payload=struct.pack('f',random.uniform(0,20))+"28-062018f00883".encode("UTF-8")
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        payload=struct.pack('f',random.uniform(0,20))+"28-3c29e381356d".encode("UTF-8")
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        payload=struct.pack('f',random.uniform(0,20))+("28-3c01e076e761".encode("UTF-8"))
        msg=b''.join(hdr.GetSomeIPDataPayload(payload))
        que.put(msg)
        time.sleep(0.1)




readThread=threading.Thread(target=readSensorsFunc,daemon=True)
addClientThread=threading.Thread(target=addClientThreadFunc,daemon=True)
sendThread=threading.Thread(target=sendThredFunc,daemon=True)

addClientThread.start()
readThread.start()
sendThread.start()

try:
    while input()!="q":
        time.sleep(0.2)
    stop_event.set()
except KeyboardInterrupt:
    time.sleep(0.2)
    exit(0)
import socket
from SomeIPHeader import SomeIPHeader
import threading
import logging


class RawSock:
    def __init__(self):
        logging.info("[RAW_SOCKET]Init")
        pass

    def sendData(self,data:bytes,Host:str,Port:int):
        logging.info(f"[RAW_SOCKET] send: {data} to {Host}:{Port}")
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
            s.sendto(data,(Host,Port))
            s.close()  

    def _receiveData(self,port:int,callback_func):
        logging.info(f"[RAW_SOCKET] Start thread receiving data on port: {port}")
        with socket.socket(socket.AF_INET,socket.SOCK_DGRAM) as s:
            s.bind(('0.0.0.0',port))
            while True:
                data,addr=s.recvfrom(1024)
                if data:
                    #logging.info(f"[RAW_SOCKET] Receive: {data}")
                    callback_func(data)

    def startReceiver(self,port:int,callback_func):
        receiverThread=threading.Thread(target=self._receiveData,args=(port,callback_func),daemon=True)
        receiverThread.start()

class SomeIpSocket:
    def __init__(self,name:str):
        self.name=name
        logging.info(f"[SOMEIP_SOCKET] Start SomeIPSocket {name}")
        self.rawSock=RawSock()
    
    def startReceiver(self,port:int,callback_func):
        self.rawSock.startReceiver(port,callback_func)

    def sendSomeIPMsg(self,service_id:hex,method_id:hex,payload:bytes,Host:str,Port:int):
        header=SomeIPHeader(service_id,method_id)
        msg=b''.join(header.GetSomeIPDataPayload(payload))
        logging.info(f"[SOMEIP_SOCKET] Send someIPMsg:{msg}")
        self.rawSock.sendData(msg,Host,Port)

    def _sendInitMsg(self,customerHost,customerPort,myHost,myPort):
        R_PORT_bytes=myPort.to_bytes(2,byteorder='big')
        R_HOST_bytes=socket.inet_aton(myHost)
        init_payload=R_HOST_bytes+R_PORT_bytes
        self.sendSomeIPMsg(0x01,0x01,init_payload,customerHost,customerPort)

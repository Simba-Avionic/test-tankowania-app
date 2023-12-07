import os
import glob
import time
import threading
import queue

os.system('modprobe w1-gpio')
os.system('modprobe w1-therm')




class DS18B20(threading.Thread):
    def __init__(self,temp_queue):
        threading.Thread.__init__(self)
        self.device_file=[
             '/sys/bus/w1/devices/28-062018f00883',
             '/sys/bus/w1/devices/28-3c29e381356d',
             '/sys/bus/w1/devices/28-3c01e076e761'
             ]
        self.queue:queue.Queue=temp_queue

    def run(self):
        while True:
            for device in self.device_file:
                data=self.read_id_and_temp(device)
                self.queue.put(data,timeout=0.5)
    
    def __read_temp_raw(self,device_path):
        f = open(device_path+"/w1_slave", 'r')
        lines = f.readlines()
        f.close()
        return lines
    def __read_id(self,device_path):
        with open(device_path+"/name",'r') as f:
            line=f.readline()
        return line

    def read_id_and_temp(self,device):
        lines = self.__read_temp_raw(device)
        while lines[0].strip()[-3:] != 'YES':
            break
        equals_pos = lines[1].find('t=')
        if equals_pos != -1:
            id=self.__read_id(device).replace("\n","")
            temp_string = lines[1][equals_pos+2:]
            temp_c = float(temp_string) / 1000.0
            return id,temp_c
    
kolejka=queue.Queue(150)

w1=DS18B20("123",kolejka)
w1.start()
while True:
    try:
        data = kolejka.get_nowait()
        print("Odebrano dane:", data)
    except queue.Empty:
        pass
    if not w1.is_alive() and kolejka.empty():
        break
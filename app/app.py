from  SomeIPHeader import SomeIPHeader
import struct
from SomeIPSocket import SomeIpSocket
import datetime
import csv
import threading
from config import Config
import flet
from flet import Page,Row,TextButton
import time
import logging
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from data import Data,PlotData

class MainApp(SomeIpSocket):
    def __init__(self,name,log_lvl,view_plot_time=10000):
        self.viewTime=view_plot_time

        logging.basicConfig(level=log_lvl)
        logging.getLogger("flet_core").setLevel(logging.CRITICAL)
        super().__init__(name)
        self.config=Config()
        self.config=Config("127.0.0.1",10000,"127.0.0.1",10101) # comment this to real use
        
        self.displayed_data=Data()

        self.to_save_data=Data()
        self.stop_saving=threading.Event()
        self.save_is_run=False

        self.plotData=PlotData()


        self.saveThread=threading.Thread(target=self._startSaveFunc,daemon=True)
        self.mainReceiver=threading.Thread(target=self.startReceiver,args=(self.config.OWN_PORT,self._MainreceiverThreadFunc),daemon=True)
        self.plotReceiverThread=threading.Thread(target=self.startReceiver,args=(self.config.OWN_PORT+1,self._PlotreceiverThreadFunc),daemon=True)
        self.fletDisplay=threading.Thread(target=self._fletDisplay_thread,daemon=True)
        self.plotThread=threading.Thread(target=self._plotFunc,daemon=True)

        
        self.fletDisplay.start()
        self.mainReceiver.start()
        self.plotThread.start()
        self.plotReceiverThread.start()

        self._sendInitMsg(self.config.RPI_HOST,self.config.RPI_PORT,self.config.OWN_HOST,self.config.OWN_PORT+1)
        self._sendInitMsg(self.config.RPI_HOST,self.config.RPI_PORT,self.config.OWN_HOST,self.config.OWN_PORT)

        self.mainReceiver.join()
        self.fletDisplay.join()
        self.plotThread.join()
        self.plotReceiverThread.join()

    def _run_thread(self):
        if self.save_is_run==False:
            self.stop_saving.clear()
            self.saveThread=threading.Thread(target=self._startSaveFunc,daemon=True)
            self.saveThread.start()
            self.save_is_run=True

    def _stop_thread(self):
        if self.save_is_run==True:
            self.stop_saving.set()
            self.save_is_run=False

    def _fletDisplay_thread(self):
        
        def main(page:Page):
            page.window_width=self.config.window_width
            page.window_height=self.config.window_height
            page.title="Engine test app"
            page.vertical_alignment="center"
            while True:
                page.add(flet.DataTable(
                    columns=[
                        flet.DataColumn(flet.Text("name")),
                        flet.DataColumn(flet.Text("value"),numeric=True)
                    ],
                    rows=[
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("pressure")),
                                flet.DataCell(flet.Text(self.displayed_data.pressure))
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("temp")),
                                flet.DataCell(flet.Text(self.displayed_data.temp))
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("A1")),
                                flet.DataCell(flet.Text(self.displayed_data.A1))
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("tenso")),
                                flet.DataCell(flet.Text(self.displayed_data.tenso))
                            ]
                        ),
                                            flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("temp góra")),
                                flet.DataCell(flet.Text(self.displayed_data.Tg))
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("temp środek")),
                                flet.DataCell(flet.Text(self.displayed_data.Ts))
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("tmp dół")),
                                flet.DataCell(flet.Text(self.displayed_data.Td))
                            ]
                        )
                    ]
                ))
                page.add(
                Row([
                    TextButton("Tara",on_click=lambda e:self.sendSomeIPMsg(0x01,0x01,struct.pack('f',self.displayed_data.tenso),
                            self.config.RPI_HOST,self.config.RPI_PORT)),
                    TextButton("Start Save",on_click=lambda e:self._run_thread()),
                    TextButton("Stop Save",on_click=lambda e:self._stop_thread())
                ])
            )
                time.sleep(1)
                page.clean()

        flet.app(target=main)

    def __calculete_pressure(self,num:float)->float:
        num+=0.008
        return (61.875*num)-23.75
    
    def _startSaveFunc(self):
        tm=datetime.datetime.now()
        filename=f"data_{tm.hour};{tm.minute};{tm.second}.csv"
        with open(file=filename,mode='w',encoding='UTF-8') as csvFile:
            writer=csv.writer(csvFile,delimiter=";")
            writer.writerow(['TIMESTAMP','TEMP',"PRESURE","A1","TENSO","Tg","Ts","Td"])
        startTime=datetime.datetime.now()
        while not self.stop_saving.is_set():
            if self.to_save_data.is_None() is False:
                timestamp=datetime.datetime.now()-startTime
                with open(filename,'a',encoding='UTF-8',newline='') as csvFile:
                    writer=csv.writer(csvFile,delimiter=";")
                    writer.writerow([timestamp,self.to_save_data.temp,
                            self.to_save_data.pressure,self.to_save_data.A1,self.to_save_data.tenso,
                            self.to_save_data.Tg,self.to_save_data.Ts,self.to_save_data.Td])
                self.to_save_data.temp=None
                self.to_save_data.pressure=None
                self.to_save_data.A0=None
                self.to_save_data.A1=None
                self.to_save_data.A2=None
                self.to_save_data.tenso=None   

    def _PlotreceiverThreadFunc(self,data):
        someipHeader=SomeIPHeader(0x00,0x00)
        someipHeader.read(data)
        payload=data[16:]
        if hex(someipHeader.methode_id)=="0x8001":
            data=struct.unpack('f',payload)[0]
            self.plotData.delpressureData.append(data)
            self.plotData.delpressX.append(self.plotData.delpressX[-1]+1)
        elif hex(someipHeader.methode_id)=="0x8002":
            data=struct.unpack('f',payload)[0]
            self.plotData.TRozData.append(data)
            self.plotData.TrozX.append(self.plotData.TrozX[-1]+1)
        elif hex(someipHeader.methode_id)=="0x8004":
            data=self.__calculete_pressure(struct.unpack('f',payload)[0])
            self.plotData.pressureData.append(data)
            self.plotData.pressureX.append(self.plotData.pressureX[-1]+1)
        elif hex(someipHeader.methode_id)=="0x8006":
            data=struct.unpack('f',payload)[0]
            self.plotData.tensoData.append(data)
            self.plotData.tensoX.append(self.plotData.tensoX[-1]+1)
        elif hex(someipHeader.methode_id)=="0x8007":
            data=struct.unpack('f',payload[:4])[0]
            sensor=payload[4:].decode("UTF-8",errors="ignore")
            if sensor=='28-062018f00883':
                self.plotData.TgData.append(data)
                self.plotData.TgX.append(self.plotData.TgX[-1]+1)
            elif sensor=='28-3c29e381356d':
                self.plotData.TsData.append(data)
                self.plotData.TsX.append(self.plotData.TsX[-1]+1)
            elif sensor=='28-3c01e076e761':
                self.plotData.TdData.append(data)
                self.plotData.TdX.append(self.plotData.TdX[-1]+1)

    def _MainreceiverThreadFunc(self,data):
        someipHeader=SomeIPHeader(0x00,0x00)
        someipHeader.read(data)
        payload=data[16:]
        if hex(someipHeader.methode_id)=="0x8001":
            data=struct.unpack('f',payload)[0]
            self.displayed_data.pressure=round(data,6)
            self.to_save_data.pressure=data
        elif hex(someipHeader.methode_id)=="0x8002":
            data=struct.unpack('f',payload)[0]
            self.displayed_data.temp=round(data,6)
            self.to_save_data.temp=data
        elif hex(someipHeader.methode_id)=="0x8003":
            self.displayed_data.A0=round(struct.unpack('f',payload)[0],6)
            self.to_save_data.A0=struct.unpack('f',payload)[0]
        elif hex(someipHeader.methode_id)=="0x8004":
            self.displayed_data.A1=round(self.__calculete_pressure(struct.unpack('f',payload)[0]),6)
            self.to_save_data.A1=struct.unpack('f',payload)[0]
        elif hex(someipHeader.methode_id)=="0x8006":
            data=struct.unpack('f',payload)[0]
            self.displayed_data.tenso=round(data,6)
            self.to_save_data.tenso=data
        elif hex(someipHeader.methode_id)=="0x8007":
            data=struct.unpack('f',payload[:4])[0]
            sensor=payload[4:].decode("UTF-8",errors="ignore")
            if sensor=='28-062018f00883':
                self.displayed_data.Tg=round(data,2)
                self.to_save_data.Tg=data
            elif sensor=='28-3c29e381356d':
                self.displayed_data.Ts=round(data,2)
                self.to_save_data.Ts=data
            elif sensor=='28-3c01e076e761':
                self.displayed_data.Td=round(data,2)
                self.to_save_data.Td=data

    def _plotFunc(self):
        how=10*self.viewTime
        def update(frame):
            ax[0,0].clear()
            ax[1,0].clear()
            ax[1,1].clear()
            ax[0,1].clear()

            
            ax[0,0].plot(self.plotData.pressureX[-how:],self.plotData.pressureData[-how:])
            ax[0,0].set_title("Pressure")

            ax[1,0].plot(self.plotData.delpressX[-how:],self.plotData.delpressureData[-how:])
            ax[1,0].set_title(r'$\Delta$ Pressure')

            ax[0,1].plot(self.plotData.tensoX[-how:],self.plotData.tensoData[-how:])
            ax[0,1].set_title("Tenso")

            ax[1,1].plot(self.plotData.TgX[-how:],self.plotData.TgData[-how:],label=r'$T_{\mathrm{góra}}$')
            ax[1,1].plot(self.plotData.TsX[-how:],self.plotData.TsData[-how:],label=r'$T_{\mathrm{środek}}$')
            ax[1,1].plot(self.plotData.TdX[-how:],self.plotData.TdData[-how:],label=r'$T_{\mathrm{dół}}$')
            ax[1,1].plot(self.plotData.TrozX[-how:],self.plotData.TRozData[-how:],label=r'$T_{\mathrm{Ciśnienie}}$')

            ax[1,1].set_title("Temperatury")

            ax[1,1].legend()
        
        fig,ax=plt.subplots(2,2,figsize=(12,10))
        ani=FuncAnimation(fig,update,interval=1000,save_count=1000,cache_frame_data=True)
        plt.show()

if __name__=="__main__":
    MainApp("mainapp",logging.INFO)
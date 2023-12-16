from  SomeIPHeader import SomeIPHeader
import struct
from SomeIPSocket import SomeIpSocket
import datetime
import csv
import threading
from config import Config
import flet
from flet import Page,Row,TextButton,TextField
import time
import logging
from matplotlib.animation import FuncAnimation
import matplotlib.pyplot as plt
from data import Data,PlotData
import asyncio


class View(flet.UserControl):
    def __init__(self,displayed_data:Data,my_config:Config,start_func,stop_func):
        self.displayed_data=displayed_data
        self.my_config=my_config
        self.sock=SomeIpSocket("button_socket")
        self._run_thread=start_func
        self._stop_thread=stop_func
        super().__init__()

    async def did_mount_async(self):
        self.running=True
        asyncio.create_task(self.update_timer())

    async def will_unmount_async(self):
        self.running=False

    async def handle_button_click_Vo(self):
        await self._button_click_Vo()
    async def handle_button_click_Vc(self):
        await self._button_click_Vc()


    async def _button_click_Vc(self):
        self.my_config.open_value=int(self.Vo.value)
        self.my_config.close_value=int(self.Vc.value)
        self.sock.sendSomeIPMsg(0x01,0x03,int.to_bytes(self.my_config.servo_pin)+int.to_bytes(self.my_config.close_value),self.my_config.RPI_HOST,self.my_config.RPI_PORT)
        await asyncio.sleep(0.001)
    async def _button_click_Vo(self):
        self.my_config.open_value=int(self.Vo.value)
        self.my_config.close_value=int(self.Vc.value)
        self.sock.sendSomeIPMsg(0x01,0x03,int.to_bytes(self.my_config.servo_pin)+int.to_bytes(self.my_config.open_value),self.my_config.RPI_HOST,self.my_config.RPI_PORT)
        await asyncio.sleep(0.001)

    async def update_timer(self):
        while self.running:
            self.press_view.value=self.displayed_data.pressure
            self.temp_view.value=self.displayed_data.temp
            self.A1_view.value=self.displayed_data.A1
            self.tenso_view.value=self.displayed_data.tenso
            self.tg_view.value=self.displayed_data.Tg
            self.ts_view.value=self.displayed_data.Ts
            self.td_view.value=self.displayed_data.Td
            await self.update_async()
            await asyncio.sleep(1)

    def build(self):
        self.press_view=flet.Text()
        self.temp_view=flet.Text()
        self.A1_view=flet.Text()
        self.tenso_view=flet.Text()
        self.tg_view=flet.Text()
        self.ts_view=flet.Text()
        self.td_view=flet.Text()
        self.Vo=TextField(flet.Text("Vo"),width=60,value=self.my_config.open_value)
        self.Vc=TextField(flet.Text("Vc"),width=60,value=self.my_config.close_value)

        self.view=flet.Column([flet.DataTable(
                    columns=[
                        flet.DataColumn(flet.Text("name")),
                        flet.DataColumn(flet.Text("value"),numeric=True)
                    ],
                    rows=[
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("pressure")),
                                flet.DataCell(self.press_view)
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("temp")),
                                flet.DataCell(self.temp_view)
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("A1")),
                                flet.DataCell(self.A1_view)
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("tenso")),
                                flet.DataCell(self.tenso_view)
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("temp góra")),
                                flet.DataCell(self.tg_view)
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("temp środek")),
                                flet.DataCell( self.ts_view)
                            ]
                        ),
                        flet.DataRow(
                            cells=[
                                flet.DataCell(flet.Text("tmp dół")),
                                flet.DataCell(self.td_view)
                            ]
                        )
                    ]
                ),
                Row([
                    TextButton("Tara",on_click=lambda e:self.sock.sendSomeIPMsg(0x01,0x01,struct.pack('f',self.displayed_data.tenso),
                            self.my_config.RPI_HOST,self.my_config.RPI_PORT)),
                    TextButton("Start Save",on_click=lambda e:self._run_thread()),
                    TextButton("Stop Save",on_click=lambda e:self._stop_thread()),
                ]),
                Row([
                    self.Vo,
                    TextButton("Open valve",on_click=lambda e: asyncio.create_task(self.handle_button_click_Vo())),
                    self.Vc,
                    TextButton("Close valve",on_click=lambda e: asyncio.create_task(self.handle_button_click_Vc()))

                ])
                ])

        return self.view
        


class MainApp(SomeIpSocket):
    def __init__(self,name,view_plot_time=10000,config=Config("127.0.0.1",10000,"127.0.0.1",10101)):
        self.viewTime=view_plot_time

        logging.basicConfig(level=config.log_lvl)
        logging.getLogger("flet_core").setLevel(logging.CRITICAL)
        super().__init__(name)
        self.config=config
        
        self.displayed_data=Data()

        self.to_save_data=Data()
        self.stop_saving=threading.Event()
        self.save_is_run=False

        self.plotData=PlotData()


        self.saveThread=threading.Thread(target=self._startSaveFunc,daemon=True)
        self.mainReceiver=threading.Thread(target=self.startReceiver,args=(self.config.OWN_PORT,self._MainreceiverThreadFunc),daemon=True)
        self.plotReceiverThread=threading.Thread(target=self.startReceiver,args=(self.config.OWN_PORT+1,self._PlotreceiverThreadFunc),daemon=True)
        self.plotThread=threading.Thread(target=self._plotFunc,daemon=True)

        
        self.mainReceiver.start()
        self.plotThread.start()
        self.plotReceiverThread.start()

        self._sendInitMsg(self.config.RPI_HOST,self.config.RPI_PORT,self.config.OWN_HOST,self.config.OWN_PORT+1)
        self._sendInitMsg(self.config.RPI_HOST,self.config.RPI_PORT,self.config.OWN_HOST,self.config.OWN_PORT)

        self._fletDisplay_thread()

        self.mainReceiver.join()
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
        
        async def main(page:Page):
            page.window_width=400
            page.window_height=550
            await page.add_async(View(self.displayed_data,self.config,self._run_thread,self._stop_thread))
        flet.app(main)

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
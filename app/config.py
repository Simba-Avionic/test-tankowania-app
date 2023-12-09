
class Config:
    def __init__(self,RPI_HOST:str="192.168.11.100",RPI_PORT=10000,
                 OWN_HOST:str="192.168.11.101",OWN_PORT=10101,
                 width=400,height=500):
        self.RPI_HOST=RPI_HOST
        self.RPI_PORT=RPI_PORT
        self.OWN_HOST=OWN_HOST
        self.OWN_PORT=OWN_PORT
        self.window_height=height
        self.window_width=width




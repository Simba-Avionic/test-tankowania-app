class PlotData:
    def __init__(self):
        self.pressureData=[0]
        self.pressureX=[0]
        self.delpressureData=[0]
        self.delpressX=[0]
        self.tensoX=[0]
        self.tensoData=[0]
        self.TgX=[0]
        self.TsX=[0]
        self.TdX=[0]
        self.TgData=[0]
        self.TsData=[0]
        self.TdData=[0]
        self.TrozX=[0]
        self.TRozData=[0]

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
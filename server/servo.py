import RPi.GPIO as GPIO
from time import sleep

class Servo:
    def __init__(self,pin:int,default_value=0):
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(pin,GPIO.OUT)
        self.pin=pin
        self.pi_pwm = GPIO.PWM(pin,180)
        self.pi_pwm.start()
        self.changeValue(default_value)
        pass
    def changeValue(self,value):
        self.pi_pwm.ChangeDutyCycle(value)
        self.value=value

    def __cleanup(self):
        self.pi_pwm.stop()
        GPIO.cleanup()


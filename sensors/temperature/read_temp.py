import RPi.GPIO as GPIO
import dht11
import time
import datetime
from Sensor import Sensor
from my_libs import *

setup_logging()
log = logging.getLogger("DHT11Exception")

class Temperature(Sensor):
    def __init__(self, digital):
        self.device_name="DHT11"
        self.digital = digital
        self.interval = 2  # initialize GPIO
        self.verbose = False

	self.lastknown = (23, 35)

        # GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        # read data using pin 18

        self.instance = dht11.DHT11(pin=self.digital)
        #GPIO.cleanup()
    def read(self):
        result1, result2 = self.lastknown
        try:
            result = self.instance.read()
            if (result.is_valid):
                result1 = result.temperature
                result2 = result.humidity
                if(result2==0):
                    result1, result2 = self.lastknown
                if(self.verbose):
                    print "<{}> :: Temperature ::".format(self.device_name), result1
                    print "<{}> :: Humidity    ::".format(self.device_name), result2
            else:
                result1, result2 = self.lastknown
                if (self.verbose):
                    print "<{}> :: Temperature :: NOT VALID".format(self.device_name)
                    print "<{}> :: Humidity    :: NOT VALID".format(self.device_name)
            self.lastknown = result1, result2
	    return result1, result2
        except:
            eprint("ERROR in READ...PI/sensors/temperature/read_temp.py")
            log.exception("ERROR in READ...PI/sensors/temperature/read_temp.py")

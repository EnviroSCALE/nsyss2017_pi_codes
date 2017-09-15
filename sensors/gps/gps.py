import RPi.GPIO as GPIO
import time
import datetime
import gps3
from Sensor import Sensor
from my_libs import *

setup_logging()
log = logging.getLogger("GPSException")

class GPS(Sensor):
    def __init__(self):
        self.device_name = "GPS"
        self.interval = 0
        self.verbose = False
        # GPS Stuff
        self.the_connection = gps3.GPSDSocket()
        self.the_fix = gps3.Fix()

    def read(self):
        ret1 = -1
        ret2 = -1
        try:
            if(self.verbose):
                print '<{}> Reading GPS....'.format(self.device_name)
            self.gpsValid = False
            self.gpsPrintable = True

            for new_data in self.the_connection:
                if new_data:
                    self.the_fix.refresh(new_data)
                    self.gpsValid = True
                else:
                    self.gpsValid = False

                # check for valid data in gps
                if not isinstance(self.the_fix.TPV['lat'], str):
                    self.gpsPrintable = True
                else:
                    self.gpsPrintable = False

                if self.gpsValid and self.gpsPrintable:
                    if(self.verbose):
                        print("<{}> Latitude: %f".format(self.device_name) % self.the_fix.TPV['lat'])
                        print("<{}> Longitude: %f".format(self.device_name) % self.the_fix.TPV['lon'])
                        print("<{}> Altitude: %f".format(self.device_name) % self.the_fix.TPV['alt'])
                    return self.the_fix.TPV['lat'], self.the_fix.TPV['lon']
                else:
                    if (self.verbose):
                        print('<{}> No valid data.'.format(self.device_name))
                    return ret1, ret2
                #time.sleep(2)
        except:
            eprint("ERROR in READ...PI/sensors/gps/gps.py")
            log.exception('ERROR in READ...PI/sensors/gps.py')
        return ret1, ret2
        

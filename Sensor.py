import time

import sensors.adc
from my_libs import *

setup_logging()
log = logging.getLogger("SensorException")


class Sensor(object):
    """A Sensor have the following properties:
    Attributes:
        name: A string representing the sensor's name.
        id: int
        analog: An int tracking number of analog channels needed
        digital: An int tracking number of digital pins needed
    """

    def __init__(self, id, analog, interval):
        """Return a Sensor object whose name is *name* and starting
            analog is *analog*."""
        self.id = id
        self.analog = analog
        self.interval = interval
        self.delay = None
        self.verbose = False

    @staticmethod
    def do_static(x, y):
        """An example of a static method"""
        return x + y

    def read(self):
        """Return instant reading (sensor specific)
        """
        raise NotImplementedError()

    def read_raw(self):
        return sensors.adc.readadc(self.analog)

    def getDelayedReading(self):
        raise NotImplementedError()

    def getDelay(self):
        return self.interval

    def avgReadMS(self, ms):
        """Return the avg of continuous readings taken for "ms" amount of time (milliseconds)
           without any gap
        """
        avg2 = 0
        n2 = 0
        start_time = time.time() * 1000
        while time.time() * 1000 - start_time < ms:
            x2 = self.read()
            n2 += 1
            avg2 = (avg2 * (n2 - 1) + x2) / n2
            time.sleep(0.1)
        return avg2

    def avgReadTimes(self, no_iter=30):
        """Return the avg of no_iter readings
        """
        avg2 = 0
        n2 = 0
        start_time = time.time() * 1000
        while n2 < no_iter:
            x2 = self.read()
            n2 += 1
            avg2 = (avg2 * (n2 - 1) + x2) / n2
            time.sleep(0.1)
        return avg2





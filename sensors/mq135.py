import time
from adc import readadc
from Sensor import Sensor
from my_libs import *

setup_logging()
log = logging.getLogger("<MQ135>")

class MQ135(Sensor):
    def __init__(self, analog):
        self.analog = analog
        self.interval = 0
        self.verbose = False
        self.device_name = "MQ135"    
        #
        self.ADC_CHANNEL = analog
        self.RLOAD = 40.0
        # Calibration resistance at atmospheric CO2 level (kOhm)
        # RZERO=76.63 #this was provided
        # here in our sensor we got this
        # RZERO=1251.06763706 #1st time
        

        # Parameters for calculating ppm of CO2 from sensor resistance - y = a^x - b, x = ppm, y = Rs/Ro
        self.PARA = 116.6020682
        self.PARB = 2.769034857

        # Parameters to model temperature and humidity dependence
        self.CORA = 0.00035
        self.CORB = 0.02718
        self.CORC = 1.39538
        self.CORD = 0.0018

        # Atmospheric CO2 level for calibration purposes (unit:ppm)
        self.ATMOCO2 = 397.13
        self.RZERO = self.auto_calibrate()

        #super(MQ135, self).__init__("mq135", analog)

    # #override
    # def takeAvgReading(self, ms):
    #     return super(MQ135, self).takeAvgReading(ms)




    #####HELPER FUNCTIONS####
    # source: https://hackaday.io/project/3475-sniffing-trinket/log/12363-mq135-arduino-library
    # @brief  Get the correction factor to correct for temperature and humidity
    # @param[in] t  The ambient air temperature
    # @param[in] h  The relative humidity
    # @return The calculated correction factor
    # /**************************************************************************/
    def getCorrectionFactor(self, t, h):
        return self.CORA * t * t - self.CORB * t + self.CORC - (h - 33.) * self.CORD

    # /**************************************************************************/


    # @brief  Get the resistance of the sensor, ie. the measurement value
    # @return The sensor resistance in kOhm
    # /**************************************************************************/
    def getResistance(self):
        val = readadc(self.ADC_CHANNEL)
	print val
        return ((1023. / val) * 5. - 1.) * self.RLOAD

    # /**************************************************************************/


    # @brief  Get the resistance of the sensor, ie. the measurement value corrected
    #         for temp/hum
    # @param[in] t  The ambient air temperature
    # @param[in] h  The relative humidity
    # @return The corrected sensor resistance kOhm
    # /**************************************************************************/
    def getCorrectedResistance(self, t, h):
        return self.getResistance() / self.getCorrectionFactor(t, h)

    # /**************************************************************************/


    # @brief  Get the ppm of CO2 sensed (assuming only CO2 in the air)
    # @return The ppm of CO2 in the air
    # /**************************************************************************/
    def getPPM(self):
        return self.PARA * pow((self.getResistance() / self.RZERO), -self.PARB)

    # /**************************************************************************/


    # @brief  Get the ppm of CO2 sensed (assuming only CO2 in the air), corrected
    #         for temp/hum
    # @param[in] t  The ambient air temperature
    # @param[in] h  The relative humidity
    # @return The ppm of CO2 in the air
    # /**************************************************************************/
    def getCorrectedPPM(self, t, h):
        return self.PARA * pow((self.getCorrectedResistance(t, h) / self.RZERO), -self.PARB)

    # /**************************************************************************/


    # @brief  Get the resistance RZero of the sensor for calibration purposes
    # @return The sensor resistance RZero in kOhm
    # /**************************************************************************/
    def getRZero(self):
        return self.getResistance() * pow((self.ATMOCO2 / self.PARA), (1. / self.PARB))

    # /**************************************************************************/


    # @brief  Get the corrected resistance RZero of the sensor for calibration
    #         purposes
    #
    # @param[in] t  The ambient air temperature
    # @param[in] h  The relative humidity
    #
    # @return The corrected sensor resistance RZero in kOhm
    # /**************************************************************************/
    def getCorrectedRZero(self, t, h):
        return self.getCorrectedResistance(t, h) * pow((self.ATMOCO2 / self.PARA), (1. / self.PARB))

    # /**************************************************************************/

    # to calibrate, calculate average value every 0.5 seconds
    def calibrate135(self):
        avg = 0
        n = 0
        try:
            while n<100:
                x = self.getRZero()
                n += 1
                avg = (avg * (n - 1) + x) / n
                print avg, "kohm, Adcout:", readadc(self.ADC_CHANNEL)
                time.sleep(0.5)
        except KeyboardInterrupt:  # If CTRL+C is pressed, exit cleanly:
            print 'bye'
        return avg


    def auto_calibrate(self):
        try:
            avg = 0
            n = 0
            #try:
            while n < 10:
                x = self.getRZero()
                n += 1
                avg = (avg * (n - 1) + x) / n

                time.sleep(0.5)
        except Exception as e:
            log.error('ERROR in CALIBRATE...sensors/mq135.py')
        raw_calib = readadc(self.analog)
        edit_calib_config("MQ135", avg)
        edit_calib_config("MQ135_RAW", raw_calib)
        log.info('Calibrated, RZERO = '+str(avg))
        return avg

    def getDelayedReading(self):
        pass

    # override
    def read(self):
        pp = -1
        try:
            pp = self.getPPM()
            if (self.verbose):
                print "<{0}> CO2 conc. = {1}".format(self.device_name, pp)
        except:
            eprint("<MQ135> ERROR in READ...sensors/mq135.py")
            log.error("ERROR in READ...sensors/mq135.py")
        return pp

# sensor = MQ135(2)
# sensor.takeAvgReading(3)


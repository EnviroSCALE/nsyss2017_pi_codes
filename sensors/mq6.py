#source: http://sandboxelectronics.com/?p=191
from adc import readadc
import time
import math
from my_libs import *
from Sensor import Sensor

setup_logging()
log = logging.getLogger("<MQ6>")

#/*******************Demo for MQ-6 Gas Sensor Module V1.3*****************************
class MQ6(Sensor):
    def __init__(self, analog):
        self.analog = analog
        self.interval = 0.2
        self.verbose = False
        self.device_name = "MQ6"
        #ANALOG_CHANNEL = 0 #define which analog input channel you are going to use
        self.RL_VALUE = 20 #define the load resistance on the board, in kilo ohms
        self.RO_CLEAN_AIR_FACTOR = 10 #RO_CLEAR_AIR_FACTOR=(Sensor resistance in clean air)/RO, which is derived from the chart in datasheet

        #/***********************Software Related Macros************************************/
        self.CALIBARAION_SAMPLE_TIMES = 50 #define how many samples you are going to take in the calibration phase
        self.CALIBRATION_SAMPLE_INTERVAL = 500/1000 #define the time interal(in second) between each samples in the cablibration phase
        self.READ_SAMPLE_TIMES = 50 #define how many samples you are going to take in normal operation
        self.READ_SAMPLE_INTERVAL = 5/1000  #define the time interval(in second) between each samples in normal operation

        #/**********************Application Related Macros**********************************/
        self.GAS_LPG = 0
        self.GAS_CH4 = 1

        #/*****************************Globals***********************************************/
        self.LPGCurve  =  [3,   0,  -0.4]    # //two points are taken from the curve.
                                        # //with these two points, a line is formed which is "approximately equivalent"
                                        # //to the original curve.
                                        # //data format:{ x, y, slope}; point1: (lg1000, lg1), point2: (lg10000, lg0.4)

        self.CH4Curve  =  [3.3, 0,  -0.38]   #//two points are taken from the curve.
                                        #//with these two points, a line is formed which is "approximately equivalent"
                                        #//to the original curve.
                                        #//data format:{ x, y, slope}; point1: (lg2000, lg1), point2: (lg5000,  lg0.7)
        #Ro = 10     #Ro is initialized to 10 kilo ohms
        self.Ro = 31		#after 1st calibration
        self.Ro = self.MQCalibration()

# /****************** MQResistanceCalculation ****************************************
# Input:   raw_adc - raw value read from adc, which represents the voltage
# Output:  the calculated sensor resistance
# Remarks: The sensor and the load resistor forms a voltage divider. Given the voltage
#          across the load resistor and its resistance, the resistance of the sensor
#          could be derived.
# ************************************************************************************/
    def MQResistanceCalculation(self, raw_adc):
      #raw_adc = raw_adc + 1
      return ( (self.RL_VALUE*(1023.-raw_adc)/raw_adc))
# ************************************************************************************/


# /***************************** MQCalibration ****************************************
# Input:   mq_pin - analog channel
# Output:  Ro of the sensor
# Remarks: This function assumes that the sensor is in clean air. It use
#          MQResistanceCalculation to calculates the sensor resistance in clean air
#          and then divides it with RO_CLEAN_AIR_FACTOR. RO_CLEAN_AIR_FACTOR is about
#          10, which differs slightly between different sensors.
    # ************************************************************************************/
    def MQCalibration(self):
          val=0
          raw_calib = readadc(self.analog)
          for i in range(0, self.CALIBARAION_SAMPLE_TIMES): #take multiple samples
            val += self.MQResistanceCalculation(readadc(self.analog))
            time.sleep(self.CALIBRATION_SAMPLE_INTERVAL)
          val = val/self.CALIBARAION_SAMPLE_TIMES;                   #calculate the average value

          val = val/self.RO_CLEAN_AIR_FACTOR;                        #divided by RO_CLEAN_AIR_FACTOR yields the Ro
                                                                #according to the chart in the datasheet
          edit_calib_config("MQ6", val)
          edit_calib_config("MQ6_RAW", raw_calib)
          log.info("Calibrated, Ro = " + str(val))
          if(self.verbose):
                print "<{}> :: Calibration is done...".format(self.device_name)
                print "<{}> :: Ro = ".format(self.device_name), self.Ro , " kohm"
          return val

# /*****************************  MQRead *********************************************
# Input:   mq_pin - analog channel
# Output:  Rs of the sensor
# Remarks: This function use MQResistanceCalculation to caculate the sensor resistenc (Rs).
#          The Rs changes as the sensor is in the different consentration of the target
#          gas. The sample times and the time interval between samples could be configured
#          by changing the definition of the macros.
# ************************************************************************************/
    def MQRead(self):
        rs=0
        for i in range(0, self.READ_SAMPLE_TIMES):
            rs += self.MQResistanceCalculation(readadc(self.analog))
            time.sleep(self.READ_SAMPLE_INTERVAL)
        rs = rs/self.READ_SAMPLE_TIMES
        return rs


    #/*****************************  MQGetGasPercentage **********************************
    # Input:   rs_ro_ratio - Rs divided by Ro
    #          gas_id      - target gas type
    # Output:  ppm of the target gas
    # Remarks: This function passes different curves to the MQGetPercentage function which
    #          calculates the ppm (parts per million) of the target gas.
    # ************************************************************************************/
    def MQGetGasPercentage(self, rs_ro_ratio, gas_id):
        if gas_id == self.GAS_LPG :
            return self.MQGetPercentage(rs_ro_ratio, self.LPGCurve)
        elif gas_id == self.GAS_CH4:
            return self.MQGetPercentage(rs_ro_ratio,self.CH4Curve)
        return 0


    # /*****************************  MQGetPercentage **********************************
    # Input:   rs_ro_ratio - Rs divided by Ro
    #          pcurve      - pointer to the curve of the target gas
    # Output:  ppm of the target gas
    # Remarks: By using the slope and a point of the line. The x(logarithmic value of ppm)
    #          of the line could be derived if y(rs_ro_ratio) is provided. As it is a
    #          logarithmic coordinate, power of 10 is used to convert the result to non-logarithmic
    #          value.
    # ************************************************************************************/
    def  MQGetPercentage(self, rs_ro_ratio, pcurve):
        return (pow(10, (((math.log10(rs_ro_ratio)-pcurve[1])/pcurve[2]) + pcurve[0])))


    def read(self):
        lpg = -1
        ch4 = -1
        try:        
            lpg = self.MQGetGasPercentage(self.MQRead() / self.Ro, self.GAS_LPG)
            ch4 = self.MQGetGasPercentage(self.MQRead() / self.Ro, self.GAS_CH4)
            if(self.verbose):
                print "<{}> :: LPG:".format(self.device_name), lpg, "ppm"
                print "<{}> :: CH4:".format(self.device_name), ch4, "ppm"
        except:
            eprint("<MQ6> ERROR in READ...sensors/mq6.py")
            log.error('ERROR in READ...sensors/mq6.py')
        return lpg, ch4


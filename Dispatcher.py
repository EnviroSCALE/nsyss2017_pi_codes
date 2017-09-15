# !/usr/bin/env python
from __future__ import print_function
from sensors.mq4 import MQ4
from sensors.mq135 import MQ135
from sensors.dust import Dust
from sensors.mq6 import MQ6
from sensors.temperature.read_temp import Temperature
from sensors.gps.gps import GPS
import mqtt
import cam
import os
from my_libs import eprint
from my_libs import get_timestamp
from my_libs import *
from struct import *
from socket import *
import traceback
import paho.mqtt.client as mqttc
import json
from circuits import Component, Debugger, handler, Event, Worker, task, Timer
import datetime
import time


#################
# Setup Logging #
#################
setup_logging()
log = logging.getLogger("<Dispatcher>")
#logging.disable(logging.CRITICAL)          #uncomment this to disable all logging


####################
# Read from config #
####################
try:
    with open('config/config.json', 'r') as f:
        config = json.load(f)
    SENSE_INTERVAL = config['SENSE_INTERVAL']
    TX_MEDIUM = config['TX_MEDIUM']
    MQTT_BROKER_HOSTNAME = config['MQTT_BROKER_HOSTNAME']
    RUNTIME = config['RUNTIME']
except:
    print("Error reading from config file: using default configuration")
    SENSE_INTERVAL = 6
    TX_MEDIUM = "wlan0"  # wlan0 for WIFI, ppp0 for 3G
    MQTT_BROKER_HOSTNAME = "iot.eclipse.org"
    RUNTIME = 50

CHECK_ALIVE_INTERVAL = 30
STARTUP_INTERVAL = 4


#####################################
# Bandwidth Consumption Calculation #
#####################################
start_tx = 0
act_payload = 0

class GlobalValues(object):
    def __init__(self):
        self.id = 0
    def inc_id(self):
        self.id = self.id + 1


##########################
# initialize all sensors #
##########################
log.info("*****   Initializing Sensors   *****")

global_values = GlobalValues()
mq135 = MQ135(2)
mq6 = MQ6(1)
mq4 = MQ4(0)
dust = Dust(3, 25)
temp = Temperature(18)
gps = GPS()
gps.verbose = True
temp.verbose = True
mq4.verbose = True
mq6.verbose = True
dust.verbose = True
mq135.verbose = True

def sense_a_bundle():
    """
    Returns:
        2 bundles of sensor data as array (dictionary)
        1st one is Reading
        2nd one is Raw Sensor Data
    """
    global mq4, mq6, mq135, dust, temp, gps, global_values
    data = {}
    data_raw = {}
    # MQ6
    data["lpg"], data["ch4"] = mq6.read()
    data["ch4"] = mq4.read()
    data_raw["lpg"] = mq6.read_raw()
    data_raw["ch4"] = mq4.read_raw()
    # MQ135
    data["co2"] = mq135.read()
    data_raw["co2"] = mq135.read_raw()
    # dust
    data["dust"], data_raw["dust"] = dust.read()
    # temp
    data["temp"], data["humidity"] = temp.read()
    data_raw["temp"], data_raw["humidity"] = data["temp"], data["humidity"]
    # gps
    data["lat"], data["long"] = gps.read()
    data_raw["lat"] = data["lat"]
    data_raw["long"] = data["long"]
    # time
    data["time"] = int(time.time())
    data_raw["time"] = data["time"]

    
    data["cng"]=data["ch4"]
    data_raw["cng"]=data_raw["ch4"]
    
    # data["lpg"], another_ch4 = 10, 10
    # data["co2"] = 10
    # data["ch4"] = 10
    # data["dust"] = 10
    # data["temp"], data["humidity"] = 10, 10
    # data["lat"], data["long"] = 10, 10
    # data["time"] = get_timestamp()
    # print(data)
    # encode_json(data)
    # encode_json(data)

    packed = encode_structpack(data)
    packed2 = encode_structpack(data_raw)
    return packed, packed2


#########################################
# Different Encoding Schemes to Compare #
#########################################
def encode_structpack(data):
    '''
    Args:
        data:
        dictionary form data array
    Returns:
        36 bytes struct.pack
    '''
    packed = pack('ifffffffff', (data["time"]), (data["ch4"]), (data["lpg"]), (data["co2"]),
                  (data["dust"]), (data["temp"]),
                  (data["humidity"]), (data["lat"]), (data["long"]), data["cng"])
    return packed


def encode_json(data):
    '''
        Args:
            data:
            dictionary form data array
        Returns:
            162 bytes labelled data : JSON
        '''
    json_str = json.dumps(data)
    # print("JSON LEN "+ str(len(json_str)))
    # print(json_str)


def upload_a_packet():
    pack1, pack2 = sense_a_bundle()
    b = bytearray(pack1)
    b2 = bytearray(pack2)
        # time = bb[0]
        # ch4 = bb[1]
        # lpg = bb[2]
        # co2 = bb[3]
        # dust = bb[4]
        # temp = bb[5]
        # humidity = bb[6]
        # lat = bb[7]
        # long = bb[8]
        # cng = bb[9]

    if (mqtt.publish_packet(b)==False):
        #traceback.print_exc()
        bb = (unpack('ifffffffff', pack1))
        strnew = "missing\t"
        for i in range(0,10):
            strnew = strnew + str(bb[i]) + "\t"
        log.log(45, strnew)
        
    if (mqtt.publish_packet_raw(b2)==False):
        #traceback.print_exc()
        bb = (unpack('ifffffffff', pack2))
        strnew = "missing_raw\t"
        for i in range(0,10):
            strnew = strnew + str(bb[i]) + "\t"
        log.log(45, strnew)


###############################
# statistics &OS command codes #
###############################
def get_tx_bytes():
    try:
        astring = 'cat /sys/class/net/' + TX_MEDIUM + '/statistics/tx_bytes'
        return long(os.popen(astring).read())
    except:
        return 0

def reconnect(tx = TX_MEDIUM):
    cmd = 'sudo bash netpi/restart_net.sh ' + str(tx)
    os.system(cmd)

def do_power_off():
    astring = 'sudo poweroff'
    return long(os.popen(astring).read())


def calculate_payload(given_str):
    '''
    Args:        given list
    Returns:     from given list -> estimate bytes
    '''
    return len(str(given_str).encode('utf-8'))

def time_of_now():
    return datetime.datetime.fromtimestamp(time.time()).strftime('%H:%M:%S')


"""
Main Program
"""
def blocking_sense():
    # print(time_of_now(), "blocking sensing start")
    ### we can put any blocking codes here
    # print("blocking sense done")
    return 0

class SenseHandler(Component):
    _worker = Worker(process=True)

    @handler("sense_event", priority=20)
    def sense_event(self, event):
        ### Fire and Wait for: task()
        #yield self.call(task(blocking_sense), self._worker)
        ### This will only print after task() is complete.
        print(time_of_now(), "SENSING done. Now uploading...")
        self.fire(Event.create("upload_event"))

class UploadHandler(Component):
    _worker = Worker(process=True)

    @handler("upload_event", priority=10)
    def upload_event(self, event):
        ustart = time_of_now()
        print(time_of_now(), "Sensing+Uploading started")
        ###log.log(45, "Before upload BYTES\t" + str(get_tx_bytes()))
        yield self.call(task(upload_a_packet), self._worker)
        ###log.log(45, "After upload BYTES\t" + str(get_tx_bytes()))
        print(time_of_now(), "Sensing+Uploading IS COMPLETED. of time ", ustart)


class App(Component):
    h1 = SenseHandler()
    h2 = UploadHandler()
    #reconnect(TX_MEDIUM)
    log.info("*****   RUN START   *****")
    
    @handler("exit_event", priority=20)
    def exit_event(self):
        log.info("*****   EXIT command received   *****")     
        print(time_of_now(), "Exiting...")
        #print(get_tx_bytes())
        #log.log(45, "END_BYTES\t" + str(get_tx_bytes()))
        CircuitsApp.timer.persist = False
        # do_power_off()

    def started(self, component):
        while True:
    	    try:
	        actuatorClient = mqttc.Client()
                actuatorClient.on_connect = on_connect
                actuatorClient.on_message = on_message
                actuatorClient.connect(MQTT_BROKER_HOSTNAME, 1883, 60)
                actuatorClient.loop_start()
                print(time_of_now(), "Started => Running")
                print(get_tx_bytes())
                log.log(45, "START_BYTES\t" + str(get_tx_bytes()))
                self.fire(Event.create("sense_event"))
                self.timer = Timer(SENSE_INTERVAL, Event.create("sense_event"), persist=True).register(self)
                Timer(RUNTIME, Event.create("exit_event"), persist=False).register(self)
		break
	    except gaierror:
                log.error("Failure connecting to MQTT controller")
	        print("FAILED")
		#reconnect(TX_MEDIUM)
	    time.sleep(10)

def on_connect(client, userdata, flags, rc):
    print("PI is listening for controls from paho/test/iotBUET/piCONTROL/ with result code " + str(rc))
    client.subscribe("paho/test/iotBUET/piCONTROL/")


def on_message(client, userdata, msg):
    try:
        parsed_json = json.loads(msg.payload)
        if (parsed_json["power"] == False):
            # do_power_off()
            log.log(45, "POWEROFF BYTES\t" + str(get_tx_bytes()))
            CircuitsApp.timer.persist = False
            log.info("Received Control: PAUSE EXECUTION")

        if (parsed_json["power"] == True):
            # do_power_off()
            log.info("Received Control: RESET TIMER")
            CircuitsApp.timer.reset(int(parsed_json["sampling_rate"]))
            log.log(45, "RESET\t" + str(get_tx_bytes()))
            CircuitsApp.timer = Timer(SENSE_INTERVAL, Event.create("sense_event"), persist=True).register(CircuitsApp)

        if (parsed_json["camera"] == True):
            print("Taking picture")
            newstr = "image" + str(get_timestamp()) + ".jpg"
            try:                
                cam.take_picture(newstr)
                log.info("Successfully captured picture\t" + str(newstr))
            except:
                log.error("Error in taking picture.")

        if (int(parsed_json["sampling_rate"]) != SENSE_INTERVAL):
	    CircuitsApp.timer.persist = False
            CircuitsApp.timer.reset(int(parsed_json["sampling_rate"]))
            log.info("Timer Reset. New sampling rate is\t" + str(parsed_json["sampling_rate"]))
            print("Timer resetted")
        log.info("Received external control command.")
        print("Received a control string")
        print(parsed_json)
    except:
        print("From topic: " + msg.topic + " INVALID DATA")
	traceback.print_exc()


CircuitsApp = App()
CircuitsApp.run()
if __name__ == '__main__':
    (App() + Debugger()).run()
    log.info("Keyboard Exit.")

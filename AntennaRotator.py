###############################################################################
#
# Antenna Rotator v0.7 (MicroPython)
#
# rka 24-Dec-23
#
###############################################################################
import machine
import network
from umqttsimple import MQTTClient
from machine import Pin
from time import sleep, ticks_ms, ticks_diff
from blinker import Blinker
from drv8825_stepper import Stepper
import ubinascii


class Config:    ##############################################################
    wifi_ssid = ""
    wifi_pwd = ""
    mqtt_server = ""
    mqtt_port = ""
    mqtt_uid = ""
    mqtt_pwd = ""

    def __init__(self, filename):
        try:
            f = open(filename, 'r')
            Config.wifi_ssid   = f.readline().strip()
            Config.wifi_pwd    = f.readline().strip()
            Config.mqtt_server = f.readline().strip()
            Config.mqtt_port   = f.readline().strip()
            Config.mqtt_uid    = f.readline().strip()
            Config.mqtt_pwd    = f.readline().strip()
            f.close()
            self.valid = True
        except:
            self.valid = False
            
    def valid(self):
        return(self.valid)
##### class Config ############################################################


# global variables
az = 0
el = 0
last_message = 0
MQTT_Rx = False
MQTT_Rx_msg = ""

blinker=Blinker()
az_motor = Stepper(dir_pin=Pin(7, Pin.OUT), step_pin=Pin(8, Pin.OUT), full_rot=3200)
el_motor = Stepper(dir_pin=Pin(5, Pin.OUT), step_pin=Pin(6, Pin.OUT), full_rot=3200)


# initialize WiFi connection
def start_wifi(ssid, password):
    global blinker
    #print(f"start_wifi({ssid}, {password})")
    station = network.WLAN(network.STA_IF)
    while not station.isconnected():
        station.active(True)
        station.connect(ssid, password)
        # print(station.ifconfig())
        blinker.blink("RED", 1)
        print("WiFi initialization failed")
    blinker.blink("GRN", 1)
    print("WiFi connected")
    return(0)


# callback function activated when a MQTT message is received
def on_message(topic, message):
    global MQTT_Rx, MQTT_Rx_msg
    #print(f"on_message triggered: {topic}, {message}")
    if topic.decode("utf-8") == "controller":
        MQTT_Rx_msg = message.decode("utf-8")
        MQTT_Rx = True
        #print(f"message received: {MQTT_Rx_msg}")


def start_mqtt(server, client_id, uid, pwd):
    global blinker
    #print(f"start_mqtt({server}, {client_id}, {uid}, {pwd})")
    client = MQTTClient(client_id, server, 1883, uid, pwd)
    client.set_callback(on_message)
    connected = False
    while not connected:
        try:
            client.connect()
            connected = True
        except OSError as e:
            print(f"MQTT initialization failed: {e}")
            blinker.blink("RED", 2)
    blinker.blink("GRN", 2)     
    print("MQTT Connected")
    return client


def setup_motors():
    global blinker, el_motor, az_motor
 
    az_motor.set_zero()
    el_motor.set_zero()
    blinker.blink("GRN", 3)


if __name__ == "__main__":
    print("Start antenna rotator")
    cnf = Config('AntennaRotator.cnf')
    # initialize WiFi & MQTT connection
    start_wifi(cnf.wifi_ssid, cnf.wifi_pwd)
    client = start_mqtt('homeassistant.local', ubinascii.hexlify(machine.unique_id()), 'MQTTClient', 'MQTTClient')
    client.subscribe("controller")
    client.publish("antenna/info", "antenna ready")
    setup_motors()
    print("initialization done, starting continuous loop")
    
    # continuous loop
    loop = True
    while loop is True:
        client.check_msg()
        # if MQTT message received
        if MQTT_Rx:
            d_az = int(MQTT_Rx_msg[1:5])
            d_el = int(MQTT_Rx_msg[6:9])
            print(f"motion request: [{d_az:+04},{d_el:+03}]")
            if (az+d_az) < 0 or (az+d_az) > 359 or (el+d_el) < 0 or (el+d_el)> 90:
                raise Exception(f"main: motion request out of bounds, az: {az}, d_az: {d_az}, el: {el}, d_el: {d_el}")
            az_motor.move(round(d_az * az_motor.get_full_rot()/360))
            el_motor.move(round(d_el * el_motor.get_full_rot()/360))
            az += d_az
            el += d_el
            last_message = 0
            MQTT_Rx = False
            
        # send position to controller every 30 sec
        now = ticks_ms()
        # if last message more then 10 sec ago
        if ticks_diff(now, last_message) > 10000:
            client.publish("antenna/data", f"[{az:03},{el:02}]")
            last_message = now
            blinker.blink("GRN", 1)
            # print("message sent")

print("Finish")

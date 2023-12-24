###############################################################################
#
# AntennaController.py reads satellite information, Azimuth (az) and Elevation
# (el) from SatPC32 (DDE interface) and provides instruction to the 
# AntennaRotator via MQTT to point the antenna to the satellite.
#
# Ruud Kapteijn, 18-Dec-23
#
###############################################################################
from datetime import datetime
import random
import time
import win32ui
import dde
from paho.mqtt import client as mqtt
import PySimpleGUI as sg
import configparser


class OrbitTracker:  ##########################################################

    def __init__(self):
        # instance variables
        self._sat_avl = False               # is a satellite position known?
        self._sat_az = -1                   # az azimuth or compass heading of sattelite
        self._sat_el = -1                   # el elevation or angle above horizon of sattelite
        self._DDE_conn = False              # is DDE communication initialized succesfully
        self._DDE_str = "not connected"     # string received from DDE interface
        # initiate DDE communication
        try:
            self.server = dde.CreateServer()
            self.server.Create("MyServer")
            self.conversation = dde.CreateConversation(self.server)
            self.conversation.ConnectTo("SatPC32", "SatPcDdeConv")
            self._DDE_str = "connected"
            self._DDE_conn = True
        except:
            print(f"OrbitTracker._init__(): SatPC32 DDE initialization failed")
            self._DDE_conn = False

    def update(self):
        self._avl = False
        if self._DDE_conn:
            # Example: "SNAO-27 AZ286.6 EL13.9 UP145850654 UMFM DN436793042 DMFM MA115.7 RR1.3436095"
            self._DDE_str = self.conversation.Request("SatPcDdeItem")
            if not self._DDE_str.startswith("** NO SATELLITE **"):
                try:
                    az_srt = self._DDE_str.find(' AZ') + 3
                    az_end = self._DDE_str.find(' ', az_srt)
                    az_str = self._DDE_str[az_srt:az_end]
                    el_srt = az_end + 3
                    el_end = self._DDE_str.find(' ', el_srt)
                    el_str = self._DDE_str[el_srt:el_end]
                    self._sat_az = round(float(az_str))
                    self._sat_el = round(float(el_str))
                    self._sat_avl = True
                except:
                    print(f"OrbitTracker.update(): error deconding DDE string <{self._DDE_str}>")

    def get_str(self):
        return(self._DDE_str)

    def sat_avl(self):
        return(self._sat_avl)

    def get_az(self):
        return(self._sat_az)

    def get_el(self):
        return(self._sat_el)

## class OrbitTracker #########################################################

# global variables
MQTT_Rx = ""                           # 
MQTT_Rx_msg = ""                       # message received from Antenna via MQTT bus
antenna_ready = False                  # AntennaRotator has executed request and is ready for next
rotator_position = [0, 0]
state = ""

# decode MQTT message received from AntennaRotator [az, el]. Example: "[135,10]"
# range 0 <= az < 360, 0 <= el <= 90
def antenna_decode(str):
    try:
        list = str.split(',')
        az = int(list[0][1:])
        el = int(list[1][0:-1])
        if (az < 0 or az > 359 or el < 0 or el > 90):
            print(f"antenna_decode: az or el out of range. az: {az}, el: {el}")
            return([0, 0])
        return([az, el])
    except:
        print(f"antenna_decode: error decoding MQTT message: {str}")
        return([0, 0])


# MQTT Callback function is triggered when a message is received from the broker
def on_message(client, userdata, message):
    global MQTT_Rx, MQTT_Rx_msg, rotator_position, antenna_ready
    # AntennaRotator provides status information
    if message.topic == "antenna/info":
        window['-ANT-'].update(f"\n({datetime.now().strftime('%H:%M:%S')}) {message.payload.decode()}", append=True)
    # AntennaRotator provides position data. Request has been completed
    if message.topic == "antenna/data":
        antenna_ready = True
        # print("antenna_ready=True")
        # show position data in message box
        MQTT_Rx = datetime.now().strftime("%H:%M:%S")
        MQTT_Rx_msg = message.payload.decode()
        rotator_position = antenna_decode(MQTT_Rx_msg)

# main program
if __name__ == "__main__":

    cnf = configparser.ConfigParser()
    cnf.read('AntennaController.cnf')
    orbitTracker = OrbitTracker()

    # step 2, initiate MQTT communication
    MQTT_client = mqtt.Client(f'C{random.randint(0, 1000)}')
    MQTT_client.username_pw_set(cnf['MQTT']['uid'], cnf['MQTT']['pwd'])
    MQTT_client.on_message = on_message
    rc = MQTT_client.connect(cnf['MQTT']['server'], int(cnf['MQTT']['port']))
    if rc == 0:
        MQTT_client.subscribe("antenna/#")
        MQTT_client.loop_start()
        MQTTConn = True
    else:    
        print(f"main: MQTT initialization failed")
        MQTTConn = False

    # step 3, initiate GUI
    layout = [[sg.Push(), sg.Text('Time :'), sg.Text(size=(48,1), key='-TIME-')],
              [sg.Push(), sg.Text('SatPC32 :'), sg.Text(size=(48,1), key='-SatPC32-')],
              [sg.Push(), sg.Text('MQTT :'), sg.Text(size=(48,1), key='-MQTT-')],
              [sg.Push(), sg.Text('Rx :'), sg.Text(size=(48,1), key='-RX-')],
              [sg.Push(), sg.Text('Tx :'), sg.Text(size=(48,1), key='-TX-')],
              [sg.Push(), sg.Text('Mess :'), sg.Text(size=(48,1), key='-MESS-')],
              [sg.Multiline(size=(60, 8), key='-ANT-', autoscroll=True)],
              [sg.Button('Exit')]]
    window = sg.Window('Antenna Controller', layout, size=(500, 500), location=(3330, 5), finalize=True)

    # continuous loop
    while True:
        orbitTracker.update()

        # state 1, Idle
        if (not orbitTracker.sat_avl()) and (not antenna_ready):
            state = "State 1, Idle"

        # state 2, Waiting for rotator
        if orbitTracker.sat_avl() and (not antenna_ready):
            state = "State 2, Waiting for rotator"

        # state 3, Waiting for satellite
        if (not orbitTracker.sat_avl()) and antenna_ready:
            state = "State 3, Waiting for satellite"

        # state 4, Tracking
        if orbitTracker.sat_avl() and antenna_ready:
            state = "State 4, Tracking"
            d_az = orbitTracker.get_az() - rotator_position[0]
            d_el = orbitTracker.get_el() - rotator_position[1]
            # print(f"d_az: {d_az}, d_el: {d_el}")
            if abs(d_az) > 3 or abs(d_el) > 3:
                antenna_request = f"[{d_az:+04},{d_el:+03}]"
                rc = MQTT_client.publish("controller", antenna_request)
                if rc[0]!=0:
                    print(f"Failed to send {antenna_request}")
                window['-TX-'].update(f"{antenna_request} ({datetime.now().strftime('%H:%M:%S')})")
                antenna_ready = False

        # update window data
        window['-TIME-'].update(datetime.now().strftime("%H:%M:%S"))
        window['-SatPC32-'].update(orbitTracker.get_str())
        window['-MESS-'].update(state)
        if MQTTConn:
            window['-MQTT-'].update("connected")
            if MQTT_Rx != "":
                window['-RX-'].update(f'{MQTT_Rx_msg} ({MQTT_Rx})')
        else:
            window['-MQTT-'].update("no connection")

        event, values = window.read(timeout=200)
        if event in (sg.WIN_CLOSED, 'Exit'):
            break
        
        time.sleep(0.5)

    print('finish')

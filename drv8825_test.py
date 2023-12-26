###############################################################################
#
# simple program to demonstrate drv8825_stepper.py functions
#
# RKA, 26-Dec-23
#
###############################################################################
from machine import Pin
from time import sleep
from drv8825_stepper import Stepper

az_motor = Stepper(dir_pin=Pin(7, Pin.OUT), step_pin=Pin(8, Pin.OUT), full_rot=3200)
el_motor = Stepper(dir_pin=Pin(5, Pin.OUT), step_pin=Pin(6, Pin.OUT), full_rot=3200)

if __name__ == "__main__":
    print('start')

    az_motor.move(800)
    sleep(3)
    az_motor.move(-800)

    el_motor.move(200)
    sleep(2)
    el_motor.move(-200)
    sleep(2)

    print("finish")

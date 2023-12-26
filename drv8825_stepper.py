###############################################################################
#
# class Stepper provides wrapper for drv8825 motor driver and NEMA 17 stepper motor
# drv8825 is configured to 1/16 microstepping (3200 steps for a full rotation)
#
# RKA, 26-Dec-2023, V0.6
#
# TODO implement acceleration and de-accelleration
###############################################################################
from machine import Pin
from time import sleep_ms

class Stepper:   ##############################################################
    
    def __init__(self, dir_pin, step_pin, full_rot=200, enable_pin=None):
        
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        self.full_rot = full_rot
        self.steps = 0
        
    def set_zero(self):
        self.steps = 0
        
    def move(self, steps):
        if steps > 0:
            self.dir_pin.on()
        else:
            self.dir_pin.off()
        for i in range(abs(steps)):
            self.step_pin.off()
            sleep_ms(10)
            self.step_pin.on()
            sleep_ms(10)
    
    def get_full_rot(self):
        return(self.full_rot)
                       
##### class Stepper ###########################################################            

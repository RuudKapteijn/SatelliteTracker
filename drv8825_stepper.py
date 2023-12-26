###############################################################################
#
# drv8825 wripper/driver with fixed acceleration and decelleration
#
# RKA 26-Dec-23
#
###############################################################################
from time import sleep_ms
from math import floor

class Stepper:   ##############################################################
    # v 2, fixed acceleration and decelleration    
    
    def __init__(self, dir_pin, step_pin, full_rot=200, enable_pin=None):
        
        self.dir_pin = dir_pin
        self.step_pin = step_pin
        self.enable_pin = enable_pin
        self.full_rot = full_rot
        self.steps = 0
        
    def _calculate_pulsewidth(self, step, total_steps):
        # max 180 accerelation steps with pulse 20, 19, 18, ...., 2 (10 steps each)
        # max 180 deceleration steps with pulse 2, 3, 4, ......, 20 (10 steps each)
        
        if step < 0 or step >= total_steps:     # step out of range
            raise Exception(f"stepper._calculate_pulsewidth: step {step} out of bounds {total_steps}")
        
        a_steps = 180
        if total_steps < 360:		# max speed cannot be reached
            a_steps = floor(total_steps / 20) * 10
        else:
            a_steps = 180
        # print(f"_calculate_pulsewidth(a_steps: {a_steps}")
        
        if step <= a_steps:     # acceleration
            pulsewidth = 20 - floor(step / 10)
            return(pulsewidth)
        
        if step >= (total_steps - a_steps):     # deceleration
            pulsewidth = 20 -floor((total_steps - step) / 10)
            return(pulsewidth)
        
        pulsewidth = 20 - round(a_steps / 10)     # topspeed
        return(pulsewidth)

    def set_zero(self):
        self.steps = 0
        
    def move(self, steps):
        if steps > 0:
            self.dir_pin.on()
        else:
            self.dir_pin.off()

        for i in range(abs(steps)):
            pulsewidth = self._calculate_pulsewidth(i, abs(steps))
            if pulsewidth >=2 and pulsewidth <= 20:
                self.step_pin.off()
                sleep_ms(round(pulsewidth / 2))
                self.step_pin.on()
                sleep_ms(round(pulsewidth / 2))
            else:
                print(f"Error, pulsewidth: {pulsewidth}")
            
    def get_full_rot(self):
        return(self.full_rot)
                       
##### class Stepper ###########################################################            

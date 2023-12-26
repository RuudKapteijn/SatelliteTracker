class Blinker:
    # use GPIO pin numers (ref pinout diagram on docs.arduino.cc)
    # use Pin.on() and Pin.off() (high(), low() or toggle() will not work)
    # onboard led Red=46, Grn=00, Ble=45, on/off is inverted

    def __init__(self):
        self.red = Pin(46, Pin.OUT)
        self.grn = Pin(00, Pin.OUT)
        self.blu = Pin(45, Pin.OUT)
        self.red.on()
        self.grn.on()
        self.blu.on()

    def off(self):
        self.red.on()
        self.grn.on()
        self.blu.on()
        
    def blink(self, color, number):
        if color not in ("GRN", "RED", "BLU") or number not in range(1,25):
            return(-1)
        if color == "GRN":
            pin = self.grn
        if color == "RED":
            pin = self.red
        if color == "BLU":
            pin = self.blu
        for i in range(number):
            pin.off()
            sleep(0.3)
            pin.on()
            sleep(0.2)
        sleep(1)
        return(number)

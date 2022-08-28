import microcontroller
import rotaryio
import analogio
import keypad


# TODO: replace hardcoded use of encoder in motor.py with a module Encoder object
#       (will probably replace with a linear potentiometer in the future)
# TODO: replace hardcoded config values with those read from a config file
#       possibly pass them in from main/code.py

REF_VOLTAGE = 3.3
MIN_POS = 0
# MAX_POS = 65535 # TODO: read from config

class Slide:
    # TODO: add enable/disable pin instead of connecting directly to Vin
    def __init__(self, ain_pin: microcontroller.Pin):
        self.potentiometer = analogio.AnalogIn(ain_pin)
        self.potentiometer.reference_voltage = REF_VOLTAGE

        self.zeroed = True
        self.target = 0
        self.seeking = False
    
    @property
    def current(self):
        return self.potentiometer.value - MIN_POS
    
    def check_limit(self):
        if self.current() <= 0:
            return True
        else:
            return False


# number of encoder detents
ENC_DIVISOR = 2
# total length of travel in rotations
MAX_POS = 3000

class Encoder:
    def __init__(
        self,
        encoder_pin1: microcontroller.Pin,
        encoder_pin2: microcontroller.Pin,
        limit_pin: microcontroller.Pin
    ):
        self.encoder = rotaryio.IncrementalEncoder(encoder_pin1, encoder_pin2, ENC_DIVISOR)
        self.limiter = keypad.Keys((limit_pin,), value_when_pressed=True)

        self.zeroed = False
        self.target = 0
        self.seeking = False
    
    @property
    def current(self):
        return self.encoder.position
    
    def check_limit(self):
        event = self.limiter.events.get()
        if event and event.pressed:
            self.encoder.position = 0
            return True
        return False
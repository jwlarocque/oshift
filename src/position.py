import microcontroller
import rotaryio
import keypad


# TODO: replace hardcoded use of encoder in motor.py with a module Encoder object
#       (will probably replace with a linear potentiometer in the future)


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

        self.target = 0
        self.seeking = False
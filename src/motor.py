import asyncio
import pwmio
import rotaryio
import microcontroller


MAX_DUTY_CYCLE = 2 ** 16 - 1
MIN_DUTY_CYCLE = 2 ** 15 + 2 ** 14 # min "on" duty cycle
# once stable within this many many encoder ticks of the target,
TARGET_APPROACH = 50
# if the measured position diverges from the target by this many ticks,
# we will attempt to recenter on the target
TARGET_DEPARTURE = 100
# sleep time (seconds) between async iterations when moving
MOVE_SLEEP = 0.02
# sleep time (seconds) between async iterations when stopped
CHECK_SLEEP = 0.5

class Motor:
    def __init__(
        self,
        forward_pins: list[microcontroller.Pin],
        reverse_pins: list[microcontroller.Pin],
        encoder_pin1: microcontroller.Pin,
        encoder_pin2: microcontroller.Pin
    ):
        self.forward_pwms = []
        self.reverse_pwms = []
        for pin in forward_pins:
            self.forward_pwms.append(
                pwmio.PWMOut(pin, frequency=5000, duty_cycle=0))
        for pin in reverse_pins:
            self.reverse_pwms.append(
                pwmio.PWMOut(pin, frequency=5000, duty_cycle=0))
        self.encoder = rotaryio.IncrementalEncoder(encoder_pin1, encoder_pin2)
        self.target = 0
        self.seeking = False

    def set_target(self, new_target: int):
        if new_target == self.target:
            return
        self.seeking = True
        self.target = new_target

    def set_velocity(self, velocity: float):
        for output in self.forward_pwms:
            output.duty_cycle = 0
        for output in self.reverse_pwms:
            output.duty_cycle = 0
        if velocity == 0:
            return
        pwm_group = self.forward_pwms if velocity > 0 else self.reverse_pwms
        duty_cycle = int(
            abs(velocity) * (MAX_DUTY_CYCLE - MIN_DUTY_CYCLE) + MIN_DUTY_CYCLE)
        for output in pwm_group:
            output.duty_cycle = duty_cycle

    async def go(self):
        self.seeking = True
        counter = 0 # TODO: remove debug
        while True:
            # TODO: remove debug
            counter += 1
            if counter % 4 == 0:
                print(f"pos: {self.encoder.position}, target: {self.target}")
            if self.encoder.position > self.target + TARGET_APPROACH:
                self.set_velocity(1.0)
                self.seeking = True
            elif self.encoder.position < self.target - TARGET_APPROACH:
                self.set_velocity(-1.0)
                self.seeking = True
            else:
                self.set_velocity(0.0)
                self.seeking = False
            await asyncio.sleep(MOVE_SLEEP if self.seeking else CHECK_SLEEP)
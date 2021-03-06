import time
import asyncio
import pwmio
import rotaryio
import microcontroller


MAX_DUTY_CYCLE = 2 ** 16 - 1
MIN_DUTY_CYCLE = 2 ** 15 + 2 ** 14 # min "on" duty cycle
# once stable within this many many encoder ticks of the target,
TARGET_APPROACH = 5
# if the measured position diverges from the target by this many ticks,
# we will attempt to recenter on the target
TARGET_DEPARTURE = 100
# sleep time (seconds) between async iterations when moving
MOVE_SLEEP = 0.01
# sleep time (seconds) between async iterations when stopped
CHECK_SLEEP = 0.5
# PID gains
P = 0.08
I = 1.0
D = -0.03

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
        off_group = self.reverse_pwms + self.forward_pwms if velocity == 0 else (self.reverse_pwms if velocity > 0 else self.forward_pwms)
        for output in off_group:
            output.duty_cycle = 0
        if velocity == 0:
            return
        on_group = [] if velocity == 0 else (self.forward_pwms if velocity > 0 else self.reverse_pwms)
        duty_cycle = int(
            abs(velocity) * (MAX_DUTY_CYCLE - MIN_DUTY_CYCLE) + MIN_DUTY_CYCLE)
        for output in on_group:
            output.duty_cycle = duty_cycle

    # given distance to target, return normalized velocity
    # to request from motor
    # TODO: implement integral term?
    def apply_pid(self, dist, rate):
        return max(-1, min(1, P * dist + D * rate))

    async def goto(self, target):
        self.target = target
        if self.seeking:
            return
        self.seeking = True
        last_pos = self.encoder.position
        request_velocity = 0.0
        dist = self.target - self.encoder.position
        counter = 0 # TODO: remove debug
        
        while (
            abs(request_velocity) > 0.2 
            or abs(dist) > TARGET_APPROACH
        ):
            dist = self.target - self.encoder.position
            rate = (self.encoder.position - last_pos) / 0.1 # hardcode time TODO: convert to time.monotonic_ns()
            request_velocity = self.apply_pid(dist, rate)
            last_pos = self.encoder.position
            # last_time = time.monotonic_ns()
            self.set_velocity(request_velocity)
            if counter == 10:
                counter = 0
                print(
                    f"pos: {self.encoder.position}, "
                    + f"target: {self.target}, real_v: {rate}, "
                    + f"req_v: {request_velocity}, "
                    + f"req_duty: {int(abs(request_velocity) * (MAX_DUTY_CYCLE - MIN_DUTY_CYCLE) + MIN_DUTY_CYCLE)}")
            counter += 1
            await asyncio.sleep(0)
        print(self.encoder.position)
        self.seeking = False
        self.set_velocity(0.0)

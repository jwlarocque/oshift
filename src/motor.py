import time
import asyncio
import pwmio
import rotaryio
import keypad
import microcontroller


MAX_DUTY_CYCLE = 2 ** 16 - 1
MIN_DUTY_CYCLE = 2 ** 15 + 2 ** 14 # min "on" duty cycle
# once stable within this many many encoder ticks of the target, stop
TARGET_APPROACH = 5
# number of encoder detents
ENC_DIVISOR = 2
# total length of travel in rotations
MAX_POS = 3000
# distance to back off before starting to zero
ZERO_BACKOFF = 800
# velocity of fast zero
ZERO_VELOCITY_FAST = 0.8
# velocity of slow zero
ZERO_VELOCITY_SLOW = 0.2
# PID gains
P = 0.08
I = 1.0
D = -0.04

class Motor:
    def __init__(
        self,
        forward_pins: list[microcontroller.Pin],
        reverse_pins: list[microcontroller.Pin],
        encoder_pin1: microcontroller.Pin,
        encoder_pin2: microcontroller.Pin,
        limit_pin: microcontroller.Pin
    ):
        self.forward_pwms = []
        self.reverse_pwms = []
        for pin in forward_pins:
            self.forward_pwms.append(
                pwmio.PWMOut(pin, frequency=5000, duty_cycle=0))
        for pin in reverse_pins:
            self.reverse_pwms.append(
                pwmio.PWMOut(pin, frequency=5000, duty_cycle=0))
        self.encoder = rotaryio.IncrementalEncoder(encoder_pin1, encoder_pin2, ENC_DIVISOR)
        self.limiter = keypad.Keys((limit_pin,), value_when_pressed=True)

        self.target = 0
        self.seeking = False

    def __set_velocity(self, velocity: float):
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
    # TODO: PID really necessary?
    def __apply_pid(self, dist, rate):
        return max(-1, min(1, P * dist + D * rate))

    async def __zero_velocity(self, velocity):
        self.seeking = True
        self.__set_velocity(velocity)

        while True:
            event = self.limiter.events.get()
            if event and event.pressed:
                self.encoder.position = 0
                self.__set_velocity(0)
                break
            await asyncio.sleep(0)

        self.seeking = False
        self.target = 0

    async def zero(self):
        print(f"Zeroing")
        self.target = 0
        await self.__goto(self.encoder.position + ZERO_BACKOFF)
        await self.__zero_velocity(-1 * abs(ZERO_VELOCITY_FAST))
        await self.__goto(0.6 * ZERO_BACKOFF)
        await self.__zero_velocity(-1 * abs(ZERO_VELOCITY_SLOW))
        print(f"Done zeroing.  Current position: {self.encoder.position}")


    async def __goto(self, target):
        self.target = target
        if self.seeking:
            return
        self.seeking = True
        last_pos = self.encoder.position
        last_time = time.monotonic_ns()
        request_velocity = 0.0
        dist = self.target - self.encoder.position
        counter = 0 # TODO: remove debug
        
        while (
            abs(request_velocity) > 0.1 
            or abs(dist) > TARGET_APPROACH
        ):
            dist = self.target - self.encoder.position
            elapsed = time.monotonic_ns() - last_time
            # rate in encoder steps per 10 ms
            # (keeps floats in a sane place)
            rate = (self.encoder.position - last_pos) / (elapsed / 10000000)
            request_velocity = self.__apply_pid(dist, rate)
            last_pos = self.encoder.position
            last_time = time.monotonic_ns()
            self.__set_velocity(request_velocity)

            # check limit switch so as not to run off end of axis
            event = self.limiter.events.get()
            if event and event.pressed:
                self.encoder.position = 0
                self.__set_velocity(0)

            if counter % 10 == 0:
                print(
                    f"elapsed: {elapsed}, pos: {self.encoder.position}, "
                    + f"target: {self.target}, real_v: {rate}, "
                    + f"req_v: {request_velocity}, "
                    + f"req_duty: {int(abs(request_velocity) * (MAX_DUTY_CYCLE - MIN_DUTY_CYCLE) + MIN_DUTY_CYCLE)}")
            counter += 1
            await asyncio.sleep(0)
        print(self.encoder.position)
        self.seeking = False
        self.__set_velocity(0.0)

    async def goto(self, target):
        print(f"going to: {target}")
        if target > 0:
            await self.__goto(target)
        else:
            print(f"Target ({target}) less than zero.")

    def get_position(self):
        return self.encoder.position

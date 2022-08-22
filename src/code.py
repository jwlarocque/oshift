import board
import digitalio
import pwmio
import rotaryio
import time
import alarm
import keypad
import asyncio
import json

from motor import Motor
from comms import OShiftService
import config
import status

# -

# consts
SLEEP_AFTER = 5 # seconds to stay awake before going into light sleep

# pins
# buttons
B0 = board.P1_13 # limit switch (out/right)
B1 = board.P1_11 # in/left
B2 = board.P0_10 # out/right
B3 = board.P0_09 # conf button
# motor (h-bridge)
M0 = board.P1_00 # reverse 1
M1 = board.P0_11 # forward 1
M2 = board.P1_04 # reverse 2
M3 = board.P1_06 # forward 2
# encoder
E0 = board.P0_20
E1 = board.P0_22

MODE_TIME = 2 # time to hold button to switch modes, in milliseconds

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

motor = Motor([M0], [M1], E0, E1, B0)
keys = keypad.Keys((B1, B2, B3), value_when_pressed=True)

async def main():
    # zero and return to saved detent
    # await motor.zero()
    # handle_detent()
    # main (shifting) loop
    while True:
        event = keys.events.get()
        if event:
            if event.key_number in (0, 1):
                handle_shift_input(event)
            if event.key_number == 2 and event.pressed:
                hold_type = await await_release(2, [2, 5], True)
                if hold_type == 0:
                    await config_loop()
                    print("!!! SHIFT MODE !!!") # TODO: remove
                elif hold_type == 1:
                    await motor.zero()
                    handle_detent()

        await asyncio.sleep(0)


def handle_shift_input(event):
    if event.pressed:
        if event.key_number == 1:
            status.status["target_detent"] = min(
                status.status["target_detent"] + 1,
                len(config.config["axes"][0]["detents"]) - 1)
        else:
            status.status["target_detent"] = max(status.status["target_detent"] - 1, 0)
        handle_detent()


def handle_detent():
    target_position = config.config["axes"][0]["detents"][status.status["target_detent"]]["position"]
    asyncio.create_task(motor_goto(target_position))


async def motor_goto(target_position):
    await motor.goto(target_position)
    status.status["position"] = motor.get_position()
    status.save()


async def config_loop():
    print("!!! CONFIG MODE !!!") # TODO: remove
    # mode 0 -> global offset (barrel adjuster)
    # mode 1 -> current detent position
    # mode 2 -> number of detents
    mode = 0
    while True:
        event = keys.events.get()
        if event:
            if event.pressed:
                if event.key_number == 2:
                    hold_type = await await_release(2, [2], True)
                    if hold_type == -1:
                        mode = (mode + 1) % 3
                        print(f"Mode: {mode}")
                    else:
                        return
                else:
                    if mode == 0:
                        if event.key_number == 0:
                            config.decrement_offset()
                        elif event.key_number == 1:
                            config.increment_offset()
                        handle_detent()
                    elif mode == 1:
                        if event.key_number == 0:
                            config.decrement_detent(status.status["target_detent"])
                        elif event.key_number == 1:
                            config.increment_detent(status.status["target_detent"])
                    elif mode == 2:
                        if event.key_number == 0:
                            config.pop_detent()
                        elif event.key_number == 1:
                            config.append_detent()
        await asyncio.sleep(0)
            


async def await_release(
    key_num: int,
    timings: list = [],
    short_circuit: bool = False
) -> int:
    """ Awaits button release.
    
    Args:
        key_num: The number of the key (in global `keys`) to watch.
        timings: An ordered list of times in seconds.
        short_circuit: Whether to return immediately once the greatest timing
            is reached.

    Returns:
        -1 once the specified key is released, if no time in timings has
        elapsed. Otherwise, the index of the greatest time in timings which has
        elapsed.
    """
    entry_time = time.monotonic()
    while True:
        event = keys.events.get()
        if event and event.released and event.key_number == key_num:
            now = time.monotonic()
            if len(timings) == 0:
                return -1
            for i, timing in enumerate(timings):
                if now - entry_time < timing:
                    return i - 1
            return len(timings) - 1
        if (short_circuit
            and len(timings) > 1
            and time.monotonic() - entry_time > timings[-1]
        ):
            return len(timings) - 1
        await asyncio.sleep(0)


asyncio.run(main())

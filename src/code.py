import board
import digitalio
import pwmio
import rotaryio
import time
import alarm
import keypad
import asyncio

from motor import Motor

# consts
SLEEP_AFTER = 5 # seconds to stay awake before going into light sleep

# pins
# buttons
B0 = board.P1_13
B1 = board.P1_11
B2 = board.P0_10
B3 = board.P0_09
# motor (h-bridge)
M0 = board.P1_00 # reverse 1
M1 = board.P0_11 # forward 1
M2 = board.P1_04 # reverse 2
M3 = board.P1_06 # forward 2
# encoder
E0 = board.P0_20
E1 = board.P0_22

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

motor = Motor([M0], [M1], E0, E1)

# TODO: this is actually the main loop, just rename it
async def catch_button_transitions():
    keys = keypad.Keys((B0, B1, B2, B3), value_when_pressed=True)
    while True:
        event = keys.events.get()
        if event:
            # print(event)
            if event.key_number == 0 and event.pressed:
                asyncio.create_task(motor.goto(motor.target + 300))
            elif event.key_number == 1 and event.pressed:
                asyncio.create_task(motor.goto(motor.target - 300))
            # print(motor.target)
            # print(motor.seeking)
        await asyncio.sleep(0)


async def main():
    # motor_task = asyncio.create_task(motor.goto(100))
    input_task = asyncio.create_task(catch_button_transitions())
    await asyncio.gather(input_task)


asyncio.run(main())

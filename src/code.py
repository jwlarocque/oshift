import board
import digitalio
import pwmio
import rotaryio
import time
import alarm
import keypad
import asyncio
import json
from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService

from motor import Motor
from comms import OShiftService
import config

ble = BLERadio()
uart = UARTService()
oshift_service = OShiftService()
advertisement = ProvideServicesAdvertisement(oshift_service)

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


# == request handlers ========

def handle_num_axes(set: bool, b: bytes):
    if set:
        print("err: number of axes is read-only")
        oshift_service.response = b"\xFF".ljust(20, b'\x00')

def handle_detent(set: bool, b: bytes):
    axis = b[0]
    detent = b[1]
    if set:
        target_pos = config.config["axes"][axis]["detents"][detent]["position"]
        print(f"axis {axis} going to detent {detent}, {target_pos}")
        asyncio.create_task(motor.goto(target_pos))
    else:
        oshift_service.response = b"\x01\x23\x45".ljust(20, b'\x00')
        pass # TODO: return current detent


def printer(message: str):
    def ret(set, b):
        print(message)
    return ret

param_handlers = [
    printer("number of axes"),
    printer("axis length, mm"),
    printer("axis type"),
    printer("num detents"),
    printer("detent position"),
    printer("overshoot method"),
    printer("overshoot proportion"),
    printer("overshoot distance"),
    handle_detent,
    printer("position")
]

async def handle_request(req_bytes):
    set = False
    action_int = req_bytes[0]
    if action_int == 0:
        print("get")
    elif action_int == 1:
        print("set")
        set = True
    else:
        print("err")
        return

    parameter_int = req_bytes[1]
    if parameter_int < len(param_handlers):
        param_handlers[parameter_int](set, req_bytes[2:])
    else:
        print(f"error: no param {parameter_int}")


async def main():
    while True:
        ble.start_advertising(advertisement)
        print("waiting to connect...")
        while not ble.connected:
            pass
        print("connected!")
        asyncio.create_task(motor.goto(100))
        last_request = oshift_service.request
        while ble.connected:
            if oshift_service.request != last_request:
                last_request = oshift_service.request
                print(oshift_service.request)
                await handle_request(oshift_service.request)
            await asyncio.sleep(0.1)
        await asyncio.sleep(0.1)


            # before_read = time.monotonic_ns()
            # if uart.in_waiting:
            #     s = uart.read(nbytes=3)
            #     print(f"read took {(time.monotonic_ns() - before_read) / 1000000}ms")
            # else:
            #     s = None
            # if s:
            #     try:
            #         result = f"going to {int(s)}"
            #         asyncio.create_task(motor.goto(int(s)))
            #     except Exception as e:
            #         result = repr(e)
            #     print(result)
            #     uart.write(result.encode("utf-8"))
            # await asyncio.sleep(1)
        # await asyncio.sleep(0)
    # input_task = asyncio.create_task(catch_button_transitions())
    # await asyncio.gather(input_task)
    print("goodbye")


asyncio.run(main())

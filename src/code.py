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
B0 = board.P1_13
B1 = board.P1_11
B2 = board.P0_10
B3 = board.P0_09
M0 = board.P1_00
M1 = board.P0_11
M2 = board.P1_04
M3 = board.P1_06
E0 = board.P0_20
E1 = board.P0_22

led = digitalio.DigitalInOut(board.LED)
led.direction = digitalio.Direction.OUTPUT

motor = Motor([M1], [M0], E0, E1)

b0_high_alarm = alarm.pin.PinAlarm(pin=B0, value=True)
b0_low_alarm = alarm.pin.PinAlarm(pin=B0, value=False)
b1_high_alarm = alarm.pin.PinAlarm(pin=B1, value=True)
b1_low_alarm = alarm.pin.PinAlarm(pin=B1, value=False)
b2_high_alarm = alarm.pin.PinAlarm(pin=B2, value=True)
b2_low_alarm = alarm.pin.PinAlarm(pin=B2, value=False)
b3_high_alarm = alarm.pin.PinAlarm(pin=B3, value=True)
b3_low_alarm = alarm.pin.PinAlarm(pin=B3, value=False)


async def catch_button_transitions():
    wake_time = time.time()
    keys = keypad.Keys((B0, B1, B2, B3), value_when_pressed=True)
    while True:
        event = keys.events.get()
        if event:
            print(event)
            if event.key_number == 0 and event.pressed:
                motor.target += 300
            elif event.key_number == 1 and event.pressed:
                motor.target -= 300
        if not motor.seeking and time.time() - wake_time > SLEEP_AFTER:
            alarm.light_sleep_until_alarms(
                b0_high_alarm,
                b0_low_alarm,
                b1_high_alarm,
                b1_low_alarm,
                b2_high_alarm,
                b2_low_alarm,
                b3_high_alarm,
                b3_low_alarm)
            wake_time = time.time()
            keys = keypad.Keys((B0, B1, B2, B3), value_when_pressed=True)
        await asyncio.sleep(0)

async def main():
    motor.target = 100
    
    motor_task = asyncio.create_task(motor.go())
    input_task = asyncio.create_task(catch_button_transitions())
    await asyncio.gather(motor_task, input_task)

    # I don't know why we have to recreate this keypad object after waking from
    # sleep, but we do.
    # keys = keypad.Keys((B0, B1, B2, B3), value_when_pressed=True)

    # while True:
    #     print(encoder0.position)
    #     event = keys.events.get()
    #     if event:
    #         if event.key_number == 0:
    #             if event.pressed:
    #                 # motor on
    #                 motor0.duty_cycle = 2 ** 16 - 1
    #             else:
    #                 # motor off
    #                 motor0.duty_cycle = 0
    #         elif event.key_number == 1:
    #             if event.pressed:
    #                 # motor on reverse
    #                 motor1.duty_cycle = 2 ** 16 - 1
    #             else:
    #                 # motor off
    #                 motor1.duty_cycle = 0
    #         print(event)
    #         print(f"{len(keys.events)} events in keypad queue")
    #         wake_time = time.time()
    #     elif time.time() - wake_time > SLEEP_AFTER:
    #         print("sleeping...")
    #         return
    #     time.sleep(0.1)


while True:
    asyncio.run(main())

    alarm.light_sleep_until_alarms(
        b0_high_alarm,
        b0_low_alarm,
        b1_high_alarm,
        b1_low_alarm,
        b2_high_alarm,
        b2_low_alarm,
        b3_high_alarm,
        b3_low_alarm)

    # if button1.value:
    #     led.value = True
    # else:
    #     led.value = False
    # print(f"buttons pressed: {'1, ' if button1.value else ''}{'2, ' if button2.value else ''}{'3, ' if button3.value else ''}{'4, ' if button4.value else ''}")


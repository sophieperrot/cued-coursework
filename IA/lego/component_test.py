#!/usr/bin/env python3

import time
import matplotlib.pyplot as plt
from cued_ia_lego import *


# Connect to brick
try:
    brick = NXTBrick()
except Exception:
    exit()


# Initialise components
motor_drive = Motor(brick, PORT_A, power=-100, smoothstart=False,
                    speedreg=False)
motor_shift = Motor(brick, PORT_B, power=0, smoothstart=False, speedreg=True,
                    brake=True, hold=True)

touch_sensor = Touch(brick, PORT_1)
light_sensor = Light(brick, PORT_2, illuminated=True)


# Constants
NUM_GEARS = 2
PRESS_THRESHOLD = 3 # seconds
SHIFT_DEGREES = [] # degrees, list of NUM_GEARS-1 elements
SHIFT_POWER = 30
SHIFT_BACKLASH = 20

# Initialise variables
current_gear = 1
finished = False
last_shift = ""


# Start the drive motor
motor_drive.reset_position()
motor_drive.run()


# Gear change function
def change_gear(current_gear, last_shift):
    turn_degrees = SHIFT_DEGREES[current_gear + 1] if last_shift == "up" else SHIFT_DEGREES[current_gear - 1]

    if current_gear == 0 and last_shift == "down":
        last_shift = "up"
        turn_degrees += SHIFT_BACKLASH
    elif current_gear == NUM_GEARS-1 and last_shift == "up":
        last_shift = "down"
        turn_degrees -= SHIFT_BACKLASH

    current_gear = current_gear + 1 if last_shift == "up" else current_gear - 1
    power = SHIFT_POWER if last_shift == "up" else -SHIFT_POWER

    motor_shift.turn(turn_degrees, power)
    motor_shift.wait_for()
    brick.play_tone(1200, 200)


def demo_motor_power(motor, power):
    print("=== Motor speed demo ===")
    try:
        motor.run(power)
        print(f"power: {power}")
    except Exception as e:
        print(e)


def test_long_press():
    print("=== Long button hold test ===")
    try:
        while True:
            if touch_sensor.is_pressed():
                # End program if touch sensor is held down for PRESS_THRESHOLD seconds
                t_press_start = time.perf_counter()
                t_press_threshold = t_press_start + PRESS_THRESHOLD
                while touch_sensor.is_pressed():
                    if time.perf_counter() > t_press_threshold:
                        finished = True
                        break
                if finished:
                    break
                # Manually gear change (when button is pressed but not held down)
                change_gear(current_gear, last_shift)
                gear_changed = True
    except KeyboardInterrupt:
        print("FAIL")
    print("SUCCESS")


# Turn off components
motor_drive.idle()
motor_shift.idle()

light_sensor.set_illuminated(False)


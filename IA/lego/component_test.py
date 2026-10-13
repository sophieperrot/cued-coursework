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
PRESS_THRESHOLD = 2 # seconds
SHIFT_DEGREES = [1000] # degrees, list of NUM_GEARS-1 elements
SHIFT_POWER = 100
SHIFT_BACKLASH = 0
DRIVE_POWER = 100

# Initialise variables
current_gear = 0
finished = False
last_shift = "down"


# Start the drive motor
motor_drive.reset_position()
motor_drive.run(power=DRIVE_POWER)


# Gear change function
def change_gear(gear, shift):
    turn_degrees = SHIFT_DEGREES[gear - 1] if shift == "up" else SHIFT_DEGREES[gear - 1]

    if gear == 0 and shift == "down":
        next_shift = "up"
        next_gear = 1
        turn_degrees += SHIFT_BACKLASH
        print("!!!")
    elif gear == NUM_GEARS-1 and shift == "up":
        next_shift = "down"
        next_gear = NUM_GEARS-2
        turn_degrees -= SHIFT_BACKLASH
        print("...")
    else:
        next_shift = shift
        next_gear = gear + 1 if shift == "up" else gear - 1
    
    turn_degrees = -turn_degrees if last_shift == "down" else turn_degrees
    print("td", turn_degrees)
    motor_drive.idle()
    motor_shift.turn(turn_degrees, SHIFT_POWER)
    # motor_shift.wait_for()
    time.sleep(0.75)
    motor_drive.run()
    brick.play_tone(1200, 200)

    return next_gear, next_shift


def demo_motor_power(motor, power, called=True):
    if not called: print("\n=== Motor speed demo ===")
    try:
        motor.idle()
        motor.wait_for()
        motor.run(power)
        print(f"power: {power}")
    except Exception as e:
        print(f"ERROT: {e}\n")


def demo_motor_turn(motor, degrees, power=50, called=True):
    if not called: print("\n=== Motor speed demo ===")
    try:
        motor.turn(degrees, power)
        motor.wait_for()
        print(f"turned: {degrees}")
    except Exception as e:
        print(f"ERROT: {e}\n")


def calibrate_motor_power(motor):
    motor.idle()
    motor.wait_for()
    print("\n=== Motor speed calibration ===")
    while True:
        try:
            new_power = int(input(" >>> "))
            if new_power < -100 or 100 < new_power:
                print("out of range")
            else:
                demo_motor_power(motor, new_power)
        except KeyboardInterrupt:
            print("Manual exit\n")
            break
        except Exception as e:
            print(f"ERROR: {e}\n")
            break


def calibrate_shift_angles(motor, power=50):
    motor.idle()
    motor.wait_for()
    print("\n=== Motor shift calibration ===")
    while True:
        try:
            new_shift = int(input(" >>> "))
            # if new_shift < -360 or 360 < new_shift:
            #     print("out of range")
            demo_motor_turn(motor, new_shift, power)
            
        except KeyboardInterrupt:
            print("Manual exit\n")
            break
        except Exception as e:
            print(f"ERROR: {e}\n")
            break


def test_button_press():
    global current_gear, last_shift
    print("=== Button press test ===")
    finished = False
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
                    print("SUCCESS: long press detected")
                    break
                # Manually gear change (when button is pressed but not held down)
                print(f"currnet_gear {current_gear}, last_shift {last_shift}")
                current_gear, last_shift = change_gear(current_gear, last_shift)
                print("SUCCESS: gear changed")
                
    except KeyboardInterrupt:
        print("FAIL: manual exit")
    except Exception as e:
        print("FAIL")
        print(e)
    

# ===== RUN TESTS HERE ===== #
"""Uncomment the functions of the tests you want to run 
and change the parameters to desired values"""

# demo_motor_power(motor_drive, 100, called=False)
test_button_press()
# calibrate_motor_power(motor_drive)
# calibrate_shift_angles(motor_shift, power=100)
# ========================== #


# Turn off components
motor_drive.idle()
motor_shift.idle()

light_sensor.set_illuminated(False)
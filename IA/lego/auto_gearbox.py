#!/usr/bin/env python3

import time
import matplotlib.pyplot as plt
from cued_ia_lego import *


# Constants
NUM_GEARS = 2
PRESS_THRESHOLD = 2         # seconds
SHIFT_DEGREES = [1000]       # degrees, list of NUM_GEARS-1 elements
SHIFT_POWER = 100
SHIFT_BACKLASH = 0
DRIVE_POWER = 100
TURN_TOLERANCE = 0


# Connect to brick
try:
    brick = NXTBrick()
except Exception:
    exit()


# Initialise components
motor_drive = Motor(brick, PORT_A, power=DRIVE_POWER, smoothstart=False,
                    speedreg=False)
motor_shift = Motor(brick, PORT_B, power=SHIFT_POWER, smoothstart=False, speedreg=True,
                    brake=True, hold=True)

touch_sensor = Touch(brick, PORT_1)
light_sensor = Light(brick, PORT_2, illuminated=True)


# Initialise variables
current_gear = 0
finished = False
last_shift = "up"
pos_window = [0]*10


# Initialise plots
times = []
speed_record = []
light_record = []
plt.figure(2)
plt.clf()
plt.figure(3)
plt.clf()
plt.figure(1)
plt.clf()
plt.xlabel('time (s)')
plt.ylabel('drive motor speed (rpm)')
plt.grid()


# Start the drive motor
motor_drive.reset_position()
motor_drive.run()


# Gear change function
def change_gear(gear, shift):
    turn_degrees = SHIFT_DEGREES[gear - 1] if shift == "up" else SHIFT_DEGREES[gear - 1]

    if gear == 0 and shift == "down":
        next_shift = "up"
        next_gear = 1
        turn_degrees += SHIFT_BACKLASH
    elif gear == NUM_GEARS-1 and shift == "up":
        next_shift = "down"
        next_gear = NUM_GEARS-2
        turn_degrees -= SHIFT_BACKLASH
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



# Main loop
t_start = time.perf_counter()
while not finished:
    # Record light sensor reading
    gear_changed = False
    t_elapsed = time.perf_counter() - t_start
    times.append(t_elapsed)
    light_record.append(light_sensor.get_lightness())

    # Touch sensor
    if touch_sensor.is_pressed():

        # End program if touch sensor is held down for PRESS_THRESHOLD seconds
        t_press_start = time.perf_counter()
        t_press_threshold = t_press_start + PRESS_THRESHOLD
        while touch_sensor.is_pressed():
            if time.perf_counter() > t_press_threshold:
                finished = True
                break
        if finished:
            print("Terminating program")
            break

        # Manually gear change (when button is pressed but not held down)
        current_gear, last_shift = change_gear(current_gear, last_shift)
        gear_changed = True

    
    # Automatic gear change
    current_pos = motor_drive.get_position()
    pos_window.pop(0)
    pos_window.append(current_pos)
    print(f"current_pos: {current_pos}, pos_window: {pos_window}")
    if current_pos - TURN_TOLERANCE <= sum(pos_window) / len(pos_window) <= current_pos + TURN_TOLERANCE:
        # current_gear, last_shift = change_gear(current_gear, last_shift)
        # gear_changed = True
        print("CHANGE")


    if gear_changed:
        print(f"Gear change to: {current_gear}")


# Turn off components
motor_drive.idle()
motor_shift.idle()

light_sensor.set_illuminated(False)


if speed_record:
    plt.figure(1)
    plt.xlim(0, 1.1 * max(times))
    plt.ylim(0, 1.1 * max(speed_record))

    plt.show()
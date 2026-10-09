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


# Initialise variables
current_gear = 1
shift_power = 30 # TODO: no clue what this is or what it does
shift_backlash = 20 # TODO: no clue what this is or what it does
shift_degrees = [120] # our final demo only had two gears, add elements to the list for a project using more gears
finished = False
shift_direction = ""


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

        # End program if touch sensor is held down for 3 seconds
        t_press_start = time.perf_counter()
        t_press_threshold = time.perf_counter() + 3
        while touch_sensor.is_pressed():
            if time.perf_counter() > t_press_threshold:
                finished = True
                break
        if finished:
            break

        # Manually change gear ()
        

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


def change_gear(current_gear, last_shift):
    turn_degrees = shift_degrees[current_gear - 1]

    if current_gear == 0 and last_shift == "down":
        last_shift = "up"
        turn_degrees += shift_backlash
    elif current_gear == 2 and last_shift == "up":
        last_shift = "down"
        turn_degrees += shift_backlash

    current_gear = current_gear + 1 if last_shift == "up" else current_gear - 1
    

    motor_shift.turn(turn_degrees, shift_power)
    motor_shift.wait_for()
    brick.play_tone(1200, 200) # TODO: change to our desired notice tones
    gear_changed = True
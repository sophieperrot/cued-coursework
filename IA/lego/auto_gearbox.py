#!/usr/bin/env python3

import time
import matplotlib.pyplot as plt
import numpy as np
import pyfftw
import statistics
from cued_ia_lego import *


# Constants
NUM_GEARS = 2
PRESS_THRESHOLD = 2         # seconds
SHIFT_DEGREES = [1000]       # degrees, list of NUM_GEARS-1 elements
SHIFT_POWER = 100
SHIFT_BACKLASH = 0
DRIVE_POWER = 100
TURN_TOLERANCE = 50
WINDOW_LEN = 10
SOUND_THRESHOLD = 530


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
sound_sensor = Sound(brick, PORT_3, adjusted=True)


# Initialise variables
current_gear = 0
finished = False
last_shift = "up"
light_window = [0]*WINDOW_LEN


# Initialise plots
times = []
speed_record = []
light_record = []
sound_record = []
plt.figure(2)
plt.clf()
plt.figure(3)
plt.clf()
plt.figure(4)
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
    time.sleep(1)
    motor_drive.run()
    # brick.play_tone(1200, 200)

    time.sleep(2)

    return next_gear, next_shift


# Turn off components function
def turn_off_components():
    global motor_drive, motor_shift
    motor_drive.idle()
    motor_shift.idle()

    light_sensor.set_illuminated(False)

    plt.close(1)
    plt.close(2)
    plt.close(3)
    plt.close(4)


# Main loop
t_interval_start = time.perf_counter()
run_time = 0
while not finished:
    try:
        # Record light & sound sensors reading
        gear_changed = False
        interval_time = time.perf_counter() - t_interval_start
        times.append(run_time + interval_time)
        light_record.append(light_sensor.get_lightness())
        sound_record.append(sound_sensor.get_loudness())

        # Measure drive motor speed every second
        if interval_time >= 1:
            pos = motor_drive.get_position()
            current_speed = abs(pos / interval_time) * 60/360
            speed_record.append(current_speed)
            if len(speed_record) > 1:
                plt.figure(1)
                plt.plot([run_time, run_time + interval_time], speed_record[-2:], 'r')
                plt.xlim(0, 300)
                plt.ylim(0, 300)
                plt.pause(0.1)
            run_time += interval_time
            # motor_drive.reset_position()
            t_interval_time = time.perf_counter()

        # Measure sound every second
        if interval_time >= 1:
                    pos = motor_drive.get_position()
                    current_speed = abs(pos / interval_time) * 60/360
                    speed_record.append(current_speed)
                    if len(speed_record) > 1:
                        plt.figure(1)
                        plt.plot([run_time, run_time + interval_time], speed_record[-2:], 'r')
                        plt.xlim(0, 300)
                        plt.ylim(0, 300)
                        plt.pause(0.1)
                    run_time += interval_time
                    # motor_drive.reset_position()
                    t_interval_time = time.perf_counter()

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
        # current_pos = motor_drive.get_position()
        # pos_window.pop(0)
        # pos_window.append(current_pos)
        # print(f"current_pos: {current_pos}, pos_window: {pos_window}")
        # print(f"avg: {sum(pos_window) / len(pos_window)}")
        # current_light = light_sensor.get_lightness()
        # light_window.pop(0)
        # light_window.append(current_light)
        # print(f"current_light: {current_light}, light_window: {light_window}")
        # print(f"avg: {sum(light_window) / len(light_window)}")
        # if len(times) > WINDOW_LEN and not (current_light - TURN_TOLERANCE <= sum(light_window) / len(light_window) <= current_light + TURN_TOLERANCE):
        if sound_record[-1] > SOUND_THRESHOLD:
            current_gear, last_shift = change_gear(current_gear, last_shift)
            gear_changed = True
            # print("CHANGE\n")


        if gear_changed:
            print(f"Gear change to: {current_gear}")

        if gear_changed and len(times) > 100:
            samples = [l - statistics.mean(light_record) for l in light_record]
            sampling_frequency = 1 / statistics.median(diff(times))
            Y = pyfftw.interfaces.numpy_fft.rfft(samples)
            power = abs(Y) ** 2
            freq = (sampling_frequency / 2) * np.linspace(0, 1, len(Y))

            plt.figure(2)
            plt.clf()
            plt.plot(times, samples)
            plt.grid()
            plt.xlabel("times (s)")
            plt.ylabel("light sensor reading")
            plt.pause(0.1)

            plt.figure(3)
            plt.clf()
            plt.plot(freq, power)
            plt.grid()
            plt.xlabel("frequency (Hz)")
            plt.ylabel("power")
            plt.title("Power spectrum of light sensor reading")
            plt.pause(0.1)

            light_record = []
            times = []

        if sound_record:
            plt.figure(4)
            plt.plot(times, sound_record)
            plt.grid(True)
            plt.xlabel('time (s)')
            plt.ylabel('sound sensor reading')

            plt.pause(0.1)
        
    except KeyboardInterrupt:
        turn_off_components()
        break

    except Exception as e:
        print(f"ERROR: {e}")
        turn_off_components()
        break


# Turn off components
turn_off_components()

if speed_record:
    plt.figure(1)
    plt.xlim(0, 1.1 * max(times))
    plt.ylim(0, 1.1 * max(speed_record))

    plt.show()
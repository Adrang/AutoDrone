"""
@title
@description
"""
import argparse

import CoDrone


def get_sensor_state(drone):
    sensor_vals = {
        'accel': drone.get_accelerometer(),
        'ang_speed': drone.get_angular_speed(),
        'battery': drone.get_battery_percentage(),
        'battery_voltage': drone.get_battery_voltage(),
        'temp': drone.get_drone_temp(),
        'gyor_angles': drone.get_gyro_angles(),
        'height': drone.get_height(),
        'opt_flow_position': drone.get_opt_flow_position(),
        'pressure': drone.get_pressure(),
        'state': drone.get_state(),
        'trim': drone.get_trim(),
    }
    return sensor_vals


def main(main_args):
    #  CoDrone has a 50ms delay between commands and will disconnect if too many
    #  commands are sent at once and too fast.
    codrone = CoDrone.CoDrone()
    try:
        # When paired, your BLE LED and CoDrone tail LED should both be solid green.
        codrone.pair(codrone.Nearest)
        trim = codrone.get_trim()
        print(f'pitch:      {trim.PITCH}')
        print(f'roll:       {trim.ROLL}')
        print(f'yaw:        {trim.YAW}')
        print(f'throttle:   {trim.THROTTLE}')
        codrone.calibrate()
        CoDrone.time.sleep(5)
        trim = codrone.get_trim()
        print(f'pitch:      {trim.PITCH}')
        print(f'roll:       {trim.ROLL}')
        print(f'yaw:        {trim.YAW}')
        print(f'throttle:   {trim.THROTTLE}')

        # take off the drone if state is not on flight
        state = codrone.get_state()
        print(f'State: {state}')
        if state != 'FLIGHT':
            codrone.takeoff()
        codrone.hover(3)
        sensor_vals = get_sensor_state(codrone)
        for each_key, each_val in sensor_vals.items():
            print(f'{each_key}: {each_val}')

        # drone.set() will prepare the CoDrone to move in a certain direction and speed,
        # while drone.move() will actually move the CoDrone in the air.
        codrone.set_pitch(30)  # Set positive pitch to 30% power
        codrone.set_roll(-30)  # Set negative roll to 30% power
        codrone.move(2)  # forward and right for 2 seconds
    except Exception as e:
        print(e)
    finally:
        codrone.land()
        codrone.disconnect()
        codrone.close()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

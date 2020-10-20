"""
@title
@description
"""
import argparse
import os
import time

from auto_drone import DATA_DIR
from auto_drone.event_controls.eye_tracker import EyeTracker


def main(main_args):
    log_id = main_args.get('log_id', None)
    log_dir = main_args.get('log_dir', os.path.join(DATA_DIR, 'eye_tracking'))
    run_length = main_args.get('run_length', 10)
    #####################################################################
    eye_tracker = EyeTracker(log_dir=log_dir, log_id=log_id)
    print('starting listener')
    eye_tracker.start_listener()
    time.sleep(run_length)
    print('stopping listener')
    eye_tracker.cleanup()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

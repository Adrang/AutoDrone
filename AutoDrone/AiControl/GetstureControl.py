"""
@title
@description
"""
import argparse
import os
import threading
import time
from queue import Queue

from Andrutil.ObserverObservable import Observable, Observer

from AutoDrone.Drone.TelloDrone import TelloDrone
from AutoDrone.ObservableVideo import ObservableVideo


class GestureControl(Observer, Observable):

    def __init__(self, sub_list: list):
        Observer.__init__(self, sub_list)
        Observable.__init__(self)

        self.frame_queue = Queue()
        self.running = False
        self.process_thread = None
        return

    def start_process_thread(self):
        self.process_thread = threading.Thread(target=self.__process_frame_queue, daemon=True)
        self.process_thread.start()
        return

    def __process_frame_queue(self):
        self.running = True
        while self.running:
            try:
                next_frame = self.frame_queue.get_nowait()
                self.set_changed_message({'timestamp': time.time(), 'type': 'frame', 'value': next_frame})
            except Exception as e:
                self.set_changed_message({'timestamp': time.time(), 'type': 'error', 'value': e})
        return

    def update(self, source, update_message):
        if isinstance(source, TelloDrone):
            message_type = update_message['type']
            message_value = update_message['value']
            if message_type == 'video':
                # todo
                self.set_changed_message({'timestamp': time.time(), 'type': 'video', 'value': message_value})
        return


def main(main_args):
    from AutoDrone.ImageObserver import ImageObserver
    from AutoDrone.PrintObserver import PrintObserver
    ###################################
    send_delay = main_args.get('send_delay', 0.1)
    scan_delay = main_args.get('scan_delay', 0.1)
    playback_file = main_args.get('playback_file', os.path.join())
    ###################################
    tello_drone = TelloDrone(adapter_name='Wi-Fi')
    tello_drone.NETWORK_SCAN_DELAY = scan_delay
    tello_drone.SEND_DELAY = send_delay
    tello_drone.connect()
    ###################################
    observable_video = ObservableVideo(video_fname=playback_file)
    gesture_control = GestureControl(sub_list=[tello_drone])

    print_observer = PrintObserver(sub_list=[gesture_control])
    image_observer = ImageObserver(sub_list=[gesture_control])
    ###################################
    time.sleep(10)
    tello_drone.cleanup()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--send_delay', type=float, default=1,
                        help='')
    parser.add_argument('--scan_delay', type=float, default=1,
                        help='')
    parser.add_argument('--playback_file', type=str,
                        help='')

    args = parser.parse_args()
    main(vars(args))

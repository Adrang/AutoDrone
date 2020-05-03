"""
@title
@description
"""
import argparse
import os
import threading
import time
from queue import Queue

import cv2
from Andrutil.ObserverObservable import Observer
import numpy as np

from AutoDrone import DATA_DIR


class GestureControl(Observer):

    def __init__(self, observable_list: list):
        Observer.__init__(self, observable_list=observable_list)

        self.frame_queue = Queue()
        self.running = False
        self.process_thread = None
        self.window_name = 'Gesture Control'

        self.raw_history = []
        self.processed_history = []
        return

    def start_process_thread(self):
        self.process_thread = threading.Thread(target=self.__process_frame_queue, daemon=True)
        self.process_thread.start()
        return

    def __process_frame_queue(self):
        """
        track the optical flow for these corners
        https://docs.opencv.org/3.0-beta/modules/imgproc/doc/feature_detection.html#goodfeaturestotrack

        :return:
        """
        num_delay = 10
        raw_scale_factor = 0.25
        bg_history = 20
        bg_thresh = 50
        morph_kernel_size = (3, 3)
        gauss_kernel_size = (3, 3)

        shi_tomasi_params = {'maxCorners': 300, 'qualityLevel': 0.2, 'minDistance': 2, 'blockSize': 7}
        lucas_kanade_params = {
            'winSize': (15, 15),
            'maxLevel': 2,
            'criteria': (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        }
        draw_color = (0, 255, 0)

        '''
        History is the number of the last frames that are taken into consideration (by default 120).
        The threshold value is the value used when computing the difference to extract the background.
        A lower threshold will find more differences with the advantage of a more noisy image.
        Detectshadows is a function of the algorithm that can remove the shadows if enabled.
        '''
        # bg_subtractor_mog2 = cv2.createBackgroundSubtractorMOG2(
        #     history=bg_history,
        #     varThreshold=bg_thresh,
        #     detectShadows=True
        # )
        # morph_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, morph_kernel_size)

        # use first frame to compute image characteristics
        first_frame = self.frame_queue.get(block=True)
        frame_width = int(first_frame.shape[1] * raw_scale_factor)
        frame_height = int(first_frame.shape[0] * raw_scale_factor)
        frame_dims = (frame_width, frame_height)
        first_gray = cv2.cvtColor(first_frame, cv2.COLOR_BGR2GRAY)
        prev = cv2.goodFeaturesToTrack(first_gray, mask=None, **shi_tomasi_params)
        mask = np.zeros_like(first_frame)

        for idx in range(num_delay):
            intial_frame = self.frame_queue.get(block=True)
            intial_frame = cv2.resize(intial_frame, frame_dims, interpolation=cv2.INTER_AREA)
            self.raw_history.append(intial_frame)

        delayed_frame = self.raw_history[-1 * num_delay]
        self.running = True
        while self.running:
            next_frame = self.frame_queue.get(block=True)
            next_frame = cv2.resize(next_frame, frame_dims, interpolation=cv2.INTER_AREA)
            self.raw_history.append(next_frame)

            # gray_frame = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
            # gray_frame = cv2.GaussianBlur(gray_frame, ksize=gauss_kernel_size, sigmaX=0, sigmaY=0)
            # 
            # fg_mask_mog2 = bg_subtractor_mog2.apply(gray_frame)
            # fg_mask_mog2 = cv2.morphologyEx(fg_mask_mog2, cv2.MORPH_CLOSE, morph_kernel)
            # fg_mask_mog2 = cv2.morphologyEx(fg_mask_mog2, cv2.MORPH_OPEN, morph_kernel)
            # 
            # # masked frame
            # res = cv2.bitwise_and(next_frame, next_frame, mask=fg_mask_mog2)
            # 
            # fg_frame_mog2 = cv2.cvtColor(fg_mask_mog2, cv2.COLOR_GRAY2RGB)
            # gray_frame = cv2.cvtColor(gray_frame, cv2.COLOR_GRAY2RGB)
            # top_layer = np.concatenate((delayed_frame, next_frame), axis=1)
            # bottom_layer = np.concatenate((gray_frame, fg_frame_mog2), axis=1)
            # frame_stack = np.concatenate((top_layer, bottom_layer), axis=0)

            cv2.imshow(self.window_name, next_frame)
            cv2.waitKey(1)

            delayed_frame = self.raw_history[-1 * num_delay]
        cv2.destroyWindow(self.window_name)
        return

    def update(self, source, update_message):
        message_type = update_message['type']
        message_value = update_message['value']
        if message_type == 'video':
            self.frame_queue.put(message_value)
        return


def main(main_args):
    from AutoDrone.ObservableVideo import ObservableVideo
    from AutoDrone.PrintObserver import PrintObserver
    ###################################
    playback_file = main_args.get('playback_file', os.path.join(DATA_DIR, 'video', 'simple_0.mp4'))
    video_length = main_args.get('length', 20)
    ###################################
    observable_video = ObservableVideo(video_fname=playback_file)
    ###################################
    gesture_control = GestureControl(observable_list=[observable_video])
    gesture_control.start_process_thread()
    PrintObserver(observable_list=[gesture_control])
    PrintObserver(observable_list=[observable_video])
    ###################################
    observable_video.start_video_thread()
    time.sleep(video_length)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--playback_file', type=str, default=os.path.join(DATA_DIR, 'video', 'simple_0.mp4'),
                        help='')
    parser.add_argument('--length', type=int, default=21,
                        help='')

    args = parser.parse_args()
    main(vars(args))

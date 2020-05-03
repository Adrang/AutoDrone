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
        self.feature_history = []
        self.vector_history = []
        return

    def start_process_thread(self):
        self.process_thread = threading.Thread(target=self.__process_frame_queue, daemon=True)
        self.process_thread.start()
        return

    def __process_frame_queue(self):
        """
        track the optical flow for these corners
        https://docs.opencv.org/3.0-beta/modules/imgproc/doc/feature_detection.html
        https://docs.opencv.org/3.0-beta/modules/video/doc/motion_analysis_and_object_tracking.html

        :return:
        """
        num_initial = 10
        raw_scale_factor = 0.25
        draw_color = (0, 255, 0)
        text_color = (0, 0, 255)
        text_font = cv2.FONT_HERSHEY_SIMPLEX
        text_scale = 0.45
        text_spacing = 14
        text_thickness = 1
        text_x0 = 0
        text_y0 = text_spacing * 2
        text_dy = text_spacing * 1
        start_arrow = (text_spacing * 1, text_spacing * 1)
        arrow_len = text_spacing * 1
        vector_smoothing_factor = 7  # todo smooth vector based on past number of points

        st_max_corners = 5
        st_quality_level = 0.2
        st_min_dist = 2
        st_blocksize = 7

        lk_win_size = (15, 15)
        lk_max_level = 2
        lk_criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)

        shi_tomasi_params = {
            'maxCorners': st_max_corners,
            'qualityLevel': st_quality_level,
            'minDistance': st_min_dist,
            'blockSize': st_blocksize
        }
        lucas_kanade_params = {
            'winSize': lk_win_size,
            'maxLevel': lk_max_level,
            'criteria': lk_criteria
        }

        # use first frame to compute image characteristics
        first_frame = self.frame_queue.get(block=True)
        frame_width = int(first_frame.shape[1] * raw_scale_factor)
        frame_height = int(first_frame.shape[0] * raw_scale_factor)
        frame_dims = (frame_width, frame_height)

        # build a set of initial frames
        for idx in range(num_initial):
            intial_frame = self.frame_queue.get(block=True)
            intial_frame = cv2.resize(intial_frame, frame_dims, interpolation=cv2.INTER_AREA)
            self.raw_history.append(intial_frame)

        prev_frame = self.raw_history[-1]
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        prev_features = cv2.goodFeaturesToTrack(prev_gray, mask=None, **shi_tomasi_params)
        total_mask = np.zeros_like(prev_frame)
        base_angle = [1, 0]
        self.running = True
        while self.running:
            next_frame = self.frame_queue.get(block=True)
            next_frame = cv2.resize(next_frame, frame_dims, interpolation=cv2.INTER_AREA)
            next_mask = np.zeros_like(prev_frame)

            next_gray = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
            next_features, status, error = cv2.calcOpticalFlowPyrLK(
                prev_gray, next_gray, prev_features, None, **lucas_kanade_params
            )

            good_features_old = prev_features[status == 1]
            good_features_new = next_features[status == 1]

            first_feature_old = good_features_old[0, :]
            first_feature_new = good_features_new[0, :]

            old_x, old_y = first_feature_old.ravel()
            new_x, new_y = first_feature_new.ravel()
            delta_list = []

            # Draws line between new and old position with green color and 2 thickness
            total_mask = cv2.line(total_mask, (new_x, new_y), (old_x, old_y), draw_color, 2)
            # Draws filled circle (thickness of -1) at new position with green color and radius of 3
            next_mask = cv2.circle(next_mask, (new_x, new_y), 3, draw_color, -1)
            for new_point, old_point in zip(good_features_new, good_features_old):
                new_x, new_y = new_point.ravel()
                old_x, old_y = old_point.ravel()

                delta_x = new_x - old_x
                delta_y = new_y - old_y
                delta_list.append((delta_x, delta_y))

            total_delta = np.average(delta_list, axis=0)
            total_mag = np.linalg.norm(total_delta)

            total_unit = total_delta / np.linalg.norm(total_mag)
            dot_product = np.dot(base_angle, total_unit)
            total_angle = np.arccos(dot_product)

            text_list = [
                {'field': f'Magnitude', 'value': f'{total_mag:0.2f}'},
                {'field': f'Angle', 'value': f'{np.degrees(total_angle):0.2f}'},
            ]
            overlay_frame = cv2.add(next_frame, total_mask)

            x_end = int(start_arrow[0] + arrow_len * total_unit[0])
            y_end = int(start_arrow[1] + arrow_len * total_unit[1])

            cv2.arrowedLine(overlay_frame, start_arrow, (x_end, y_end), text_color, text_thickness)
            for idx, each_line in enumerate(text_list):
                text_field = each_line['field']
                text_val = each_line['value']
                cv2.putText(
                    img=overlay_frame, text=f'{text_field}: {text_val}', org=(text_x0, text_y0 + text_dy * (idx + 1)),
                    fontFace=text_font, fontScale=text_scale, color=text_color, thickness=text_thickness
                )
            prev_gray = next_gray.copy()
            prev_features = good_features_new.reshape(-1, 1, 2)

            top_layer = np.concatenate((next_frame, overlay_frame), axis=1)
            bottom_layer = np.concatenate((next_mask, total_mask), axis=1)
            frame_stack = np.concatenate((top_layer, bottom_layer), axis=0)

            self.raw_history.append(next_frame)
            self.processed_history.append(overlay_frame)
            self.feature_history.append(good_features_new)
            self.vector_history.append(delta_list)

            cv2.imshow(self.window_name, frame_stack)
            cv2.waitKey(1)
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

"""
@title
@description
"""
import argparse
import threading
import time

import cv2
from Andrutil.ObserverObservable import Observable


class ObservableVideo(Observable):
    def __init__(self, video_fname):
        Observable.__init__(self)

        self.video_fname = video_fname
        self.video_thread = None

        self.frame_delay =30
        self.frame_history = []
        return

    def start_video_thread(self):
        self.video_thread = threading.Thread(target=self.__read_video, daemon=True)
        self.video_thread.start()
        return

    def __read_video(self):
        self.video_capture = cv2.VideoCapture(self.video_fname)
        if not self.video_capture.isOpened():
            self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                      'value': f'Could not open video stream'})
            return

        fps = round(float(self.video_capture.get(cv2.CAP_PROP_FPS)), 2)
        self.frame_delay = int(1000 / fps)
        self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                  'value': f'Frames per second: {fps} | Frame delay: {self.frame_delay}'})

        # discard first read and make sure all is reading correctly
        read_success, video_frame = self.video_capture.read()
        if not read_success:
            self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                      'value': f'Error reading from video stream'})
            return

        while self.video_capture.isOpened():
            read_success, video_frame = self.video_capture.read()
            if read_success:
                self.set_changed_message({
                    'timestamp': time.time(), 'type': 'video',
                    'frame_delay': self.frame_delay, 'value': video_frame
                })
                self.frame_history.append(video_frame)
            cv2.waitKey(self.frame_delay)
        self.video_capture.release()
        cv2.destroyAllWindows()
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

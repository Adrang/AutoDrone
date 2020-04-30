"""
@title
@description
"""
import argparse
import threading

from Andrutil.ObserverObservable import Observable


class ObservableVideo(Observable):

    def __init__(self, video_fname):
        Observable.__init__(self)

        self.video_fname = video_fname
        self.video_thread = None
        return

    def start_video_thread(self):
        self.video_thread = threading.Thread(target=self.__read_video, daemon=True)
        self.video_thread.start()
        return

    def __read_video(self):
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

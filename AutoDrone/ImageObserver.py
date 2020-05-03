"""
@title
@description
"""
import argparse

import cv2
from Andrutil.ObserverObservable import Observer


class ImageObserver(Observer):

    def __init__(self, observable_list: []):
        Observer.__init__(self, observable_list=observable_list)
        self.window_name = 'ImageObserver'
        # self.window = cv2.namedWindow(self.window_name)
        return

    def update(self, source, update_message):
        if update_message['type'] in ['frame', 'image', 'video']:
            cv2.imshow(self.window_name, update_message['value'])
            cv2.waitKey(1)
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

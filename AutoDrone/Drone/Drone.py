"""
@title
@description
"""
import argparse
from enum import Enum, auto


class RotateDirection(Enum):
    CLOCKWISE = auto()
    COUNTER_CLOCKWISE = auto()


class MoveDirection(Enum):
    FORWARD = auto()
    BACK = auto()
    LEFT = auto()
    RIGHT = auto()
    UP = auto()
    DOWN = auto()


class Drone:

    def __init__(self, name):
        self.name = name
        return

    def connect(self):
        return

    def disconnect(self):
        return

    def move(self, distance: int, direction: MoveDirection):
        return

    def rotate(self, degrees: int, direction: RotateDirection):
        return

    def set_speed(self, amount: int, direction: MoveDirection):
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

"""
@title
@description
"""
import argparse
from enum import Enum


class TurnDirection(Enum):
    LEFT = 0
    RIGHT = 0


class MoveDirection(Enum):
    FORWARD = 0
    BACK = 0
    LEFT = 0
    RIGHT = 0
    UP = 0
    DOWN = 0


class Drone:

    def __init__(self, name):
        self.name = name
        return

    def connect(self):
        return

    def disconnect(self):
        return

    def move(self, amount: float, direction: MoveDirection):
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

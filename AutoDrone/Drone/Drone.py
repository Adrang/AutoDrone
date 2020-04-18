"""
@title
@description
"""
import argparse
from abc import ABC, abstractmethod
from enum import Enum


class RotateDirection(Enum):
    CLOCKWISE = 'cw'
    COUNTER_CLOCKWISE = 'ccw'


class MoveDirection(Enum):
    FORWARD = 'forward'
    BACK = 'back'
    LEFT = 'left'
    RIGHT = 'right'
    UP = 'up'
    DOWN = 'down'


class Drone(ABC):

    def __init__(self, name: str, timeout: float = 0.5):
        self.name = name
        self.timeout = timeout

        self.message_history = []
        return

    @abstractmethod
    def connect(self, scan_delay: int = 1):
        return

    @abstractmethod
    def disconnect(self):
        return

    # @abstractmethod
    # def listen(self):
    #     return

    @abstractmethod
    def send_command(self, message: str):
        return

    @abstractmethod
    def move(self, distance: float, direction: MoveDirection):
        return

    @abstractmethod
    def rotate(self, degrees: float, direction: RotateDirection):
        return

    @abstractmethod
    def set_speed(self, amount: float):
        return

    def get_status(self):
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

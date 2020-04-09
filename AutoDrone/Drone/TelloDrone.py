"""
@title
@description
"""
import argparse

from AutoDrone.Drone.Drone import Drone


class TelloDrone(Drone):

    def __init__(self):
        Drone.__init__(self)
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

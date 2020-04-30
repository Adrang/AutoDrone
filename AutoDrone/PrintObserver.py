"""
@title
@description
"""
import argparse

from Andrutil.ObserverObservable import Observer


class PrintObserver(Observer):

    def __init__(self, sub_list: []):
        Observer.__init__(self, sub_list=sub_list)
        return

    def update(self, source, update_message):
        print(f'{source.__repr__}: {update_message}')


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

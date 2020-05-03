"""
@title
@description
"""
import argparse

from Andrutil.ObserverObservable import Observer


class PrintObserver(Observer):

    def __init__(self, observable_list: []):
        Observer.__init__(self, observable_list=observable_list)
        return

    def update(self, source, update_message):
        if update_message['type'] in ['print', 'error', 'status']:
            print(f'{source.__class__.__name__}: {update_message["value"]}')
        return


def main(main_args):
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

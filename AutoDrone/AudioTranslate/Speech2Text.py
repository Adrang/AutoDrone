"""
@title
@description
"""
import argparse
import sys
import threading
import time
from time import sleep

import speech_recognition as sr

from Andrutil.ObserverObservable import Observable


class Speech2Text(Observable):

    def __init__(self, input_delay: float = 0.1):
        """
        get input from mic
        translate signal to words
        update observers
        """
        Observable.__init__(self)
        self.subscriber_list = []

        self.input_delay = input_delay
        self.mic_history = []
        self.listening = False
        self.listen_mic_thread = None
        self.recognizer = None
        return

    def start_listener(self):
        """

        :return:
        """
        self.listening = True
        self.listen_mic_thread = threading.Thread(target=self.__listen_microphone, daemon=True)
        self.listen_mic_thread.start()
        return

    def __listen_microphone(self):
        """

        :return:
        """
        self.recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while self.listening:
                audio = self.recognizer.listen(source)
                try:
                    audio_text = self.recognizer.recognize_google(audio)
                    self.mic_history.append(audio_text)
                    self.set_changed_message({'timestamp': time.time(), 'type': 'decode', 'value': audio_text})
                    sleep(self.input_delay)
                except sr.UnknownValueError as uve:
                    self.set_changed_message({'timestamp': time.time(), 'type': 'error', 'value': f'{uve}'})
                except Exception as e:
                    self.set_changed_message({'timestamp': time.time(), 'type': 'error', 'value': f'{e}'})
        return

    def stop_listener(self):
        self.listening = False
        return

    def save_history(self):
        """
        todo

        :return:
        """
        return


def main(main_args):
    input_delay = main_args.get('input_delay', 0.1)
    run_len = main_args.get('run_len', 5)
    #######################################
    speech_text = Speech2Text(input_delay=input_delay)
    speech_text.start_listener()

    sleep(run_len)
    speech_text.stop_listener()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--input_delay', type=float, default=5,
                        help='')
    parser.add_argument('--run_len', type=float, default=10,
                        help='')

    args = parser.parse_args()
    main(vars(args))

"""
@title
@description
"""
import argparse
import json
import os
import threading
import time
from datetime import datetime
from time import sleep

import speech_recognition as sr

from AutoDrone import DATA_DIR


class Speech2Text:

    def __init__(self, input_delay: float = 0.1):
        """
        get input from mic
        translate signal to words
        """
        current_time = time.time()
        date_time = datetime.fromtimestamp(time.time())
        time_str = date_time.strftime("%Y-%m-%d-%H-%M-%S")

        # identification information
        self.name = 'google_sr'
        self.id = f'{self.name}_{time_str}_{int(current_time)}'
        self.event_log = []
        self.save_directory = os.path.join(DATA_DIR, 'speech', f'{self.id}')
        self.save_fname = os.path.join(self.save_directory, 'message_history.json')
        if not os.path.isdir(self.save_directory):
            os.makedirs(self.save_directory)

        self.input_delay = input_delay
        self.mic_history = []
        self.listening = False
        self.listen_mic_thread = None
        self.recognizer = None
        return

    def cleanup(self):
        self.stop_listener()
        self.save_history()
        return

    def get_message_idx(self, message_idx: int):
        """
        todo make into iterator using queue

        :param message_idx:
        :return:
        """
        message = self.mic_history[message_idx] if len(self.mic_history) > message_idx else None
        return message

    def get_last_message(self):
        last_translate = self.mic_history[-1] if len(self.mic_history) > 0 else None
        return last_translate

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
                    sleep(self.input_delay)
                except sr.UnknownValueError as uve:
                    # self.mic_history.append(f'{uve}')
                    pass
                except sr.RequestError as re:
                    # self.mic_history.append(f'{re}')
                    pass
        return

    def stop_listener(self):
        self.listening = False
        return

    def save_history(self):
        """

        :return:
        """
        with open(self.save_fname, 'w+') as save_file:
            json.dump(fp=save_file, obj=self.mic_history, indent=2)
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

"""
@title
@description
"""
import logging
import os
import threading
import time

from pynput.keyboard import Listener


class KeyLogger:

    def __init__(self, log_dir: str, log_id=None, callback_list=None):
        self.history = []
        self.callback_list = callback_list if callback_list is not None else []
        self.listen_thread = None
        self.listening = False

        self.key_listener = Listener(on_press=self.on_press)
        start_time = time.time()

        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)

        if log_id:
            self.log_fname = os.path.join(log_dir, f'log_{log_id}_{start_time}.txt')
        else:
            self.log_fname = os.path.join(log_dir, f'log_{start_time}.txt')
        return

    def on_press(self, key):
        self.history.append(key)
        logging.info(str(key))

        read_time = time.time()
        for each_callback in self.callback_list:
            if callable(each_callback):
                each_callback({'timestamp': read_time, 'data': key})
        return

    def start_listener(self):
        self.listen_thread = threading.Thread(target=self.__listen, daemon=True)
        self.listen_thread.start()
        return

    def __listen(self):
        self.listening = True
        logging.basicConfig(filename=self.log_fname, level=logging.DEBUG, format='%(asctime)s: %(message)s')
        self.key_listener.start()
        while self.listening:
            pass
        return

    def stop_listener(self):
        self.listening = False
        return

    def cleanup(self):
        self.stop_listener()
        self.listen_thread.join()

        self.key_listener.stop()
        self.listen_thread.join()
        return

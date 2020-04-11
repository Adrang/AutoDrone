"""
@title
@description
"""
import argparse
import socket
import threading
from time import sleep

from AutoDrone.Drone.Drone import Drone


class TelloConnection:
    BUFF_SIZE = 1024

    def __init__(self, name, address):
        """
        todo make implement observer from Andrutil

        :param name:
        :param address:
        """
        self.listening = False
        self.name = name
        self.address = address
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket.settimeout(0)
        self.listen_thread = threading.Thread(
            target=self.start_listening,
            args=(),
            daemon=True
        )
        return

    def start_listening(self):
        print(f'Starting {self.name} thread...')
        self.listening = True

        while self.listening:
            try:
                data, server = self.socket.recvfrom(self.BUFF_SIZE)
                print(data.decode(encoding='utf-8'))
            except BlockingIOError:
                # no data has been received from connection
                pass

        print(f'Exiting {self.name} thread...')
        return

    def close(self):
        self.listening = False

        # wait for thread to exit
        sleep(0.2)
        self.socket.close()
        return


class TelloDrone(Drone):
    LOCAL_HOST = '0.0.0.0'
    STATE_PORT = 8890
    BASE_PORT = 8889
    VIDEO_PORT = 11111

    TELLO_IP = '192.168.10.1'
    TELLO_PORT = 8889

    def __init__(self):
        Drone.__init__(self, 'Tello')

        self.tello_address = (self.TELLO_IP, self.TELLO_PORT)
        self.connection_dict = {
            'state': TelloConnection(name='state', address=(self.LOCAL_HOST, self.STATE_PORT)),
            'base': TelloConnection(name='base', address=(self.LOCAL_HOST, self.BASE_PORT)),
            'video': TelloConnection(name='video', address=(self.LOCAL_HOST, self.VIDEO_PORT)),
        }
        self.listening = False
        self.connected = False
        return

    def __str__(self):
        return f'Name: {self.name} | Connected: {self.connected} | Listening: {self.listening}'

    def connect(self):
        """

        :return:
        """
        self.connected = True

        for conn_type, conn_entry in self.connection_dict.items():
            self.send('command', conn_entry.socket)
        return

    def listen(self):
        """

        :return:
        """
        self.listening = True

        for conn_type, conn_entry in self.connection_dict.items():
            conn_entry.listen_thread.start()
        return

    def send(self, message: str, send_socket=None):
        """

        :param message:
        :param send_socket:
        :return:
        """
        if self.connected:
            msg = message.encode(encoding='utf-8')
            sent = send_socket.sendto(msg, self.tello_address)
            if sent == 0:
                raise RuntimeError('socket connection broken')
            print(f'Sent {sent} bytes')
        return

    def disconnect(self):
        """

        :return:
        """
        self.connected = False

        for conn_type, conn_entry in self.connection_dict.items():
            conn_entry.close()
        return


def main(main_args):
    """

    :param main_args:
    :return:
    """
    tello_drone = TelloDrone()
    tello_drone.connect()
    tello_drone.listen()

    print(tello_drone)
    sleep(5)

    # print('Tello Python3 Demo.')
    # print(
    #     '\ttakeoff\n'
    #     '\tland\n'
    #     '\tflip\n'
    #     '\tforward\n'
    #     '\tback\n'
    #     '\tleft\n'
    #     '\tright\n'
    #     '\t--------\n'
    #     '\tup\n'
    #     '\tdown\n'
    #     '\tcw\n'
    #     '\tccw\n'
    #     '\tspeed\n'
    #     '\tspeed?'
    # )
    # print('end -- quit demo.')
    #
    # msg = input()
    # while 'end' not in msg:
    #     msg = input()
    #     try:
    #         tello_drone.send(msg)
    #     except KeyboardInterrupt:
    #         break
    tello_drone.disconnect()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

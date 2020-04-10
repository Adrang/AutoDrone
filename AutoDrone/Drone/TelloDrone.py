"""
@title
@description
"""
import argparse
import socket
import threading

from AutoDrone.Drone.Drone import Drone


class TelloDrone(Drone):
    LOCAL_HOST = '0.0.0.0'
    LOCAL_PORT = 8890

    TELLO_IP = '192.168.10.1'
    TELLO_PORT = 8889

    MTU = 1518

    def __init__(self):
        Drone.__init__(self, 'Tello')

        self.local_addr = (self.LOCAL_HOST, self.LOCAL_PORT)
        self.tello_address = (self.TELLO_IP, self.TELLO_PORT)
        self.sock = None

        self.recv_thread = None
        self.listening = False
        return

    def connect(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(self.local_addr)

        # send 'command' to initiate SDK mode
        self.send('command')
        return

    def state(self):
        return

    def listen(self):
        recv_thread = threading.Thread(target=self.receive, daemon=True)
        recv_thread.start()
        return

    def receive(self):
        self.listening = True
        while self.listening:
            try:
                data, server = self.sock.recvfrom(self.MTU)
                print(data.decode(encoding='utf-8'))
            except Exception as e:
                print(f'{e}')
        print(f'Exiting Tello listener...')
        return

    def send(self, message: str):
        msg = message.encode(encoding='utf-8')
        sent = self.sock.sendto(msg, self.tello_address)
        return

    def disconnect(self):
        self.sock.close()
        return


def main(main_args):
    """

    :param main_args:
    :return:
    """
    tello_drone = TelloDrone()
    print(tello_drone.name)

    print('Tello Python3 Demo.')
    print(
        '\ttakeoff\n'
        '\tland\n'
        '\tflip\n'
        '\tforward\n'
        '\tback\n'
        '\tleft\n'
        '\tright\n'
        '\t--------\n'
        '\tup\n'
        '\tdown\n'
        '\tcw\n'
        '\tccw\n'
        '\tspeed\n'
        '\tspeed?'
    )
    print('end -- quit demo.')

    msg = ''
    while 'end' not in msg:
        msg = input()
        try:
            tello_drone.send(msg)
        except KeyboardInterrupt:
            break
    tello_drone.disconnect()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

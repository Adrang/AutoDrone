"""
@title
@description

https://github.com/damiafuentes/DJITelloPy
https://github.com/microlinux/tello

https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf
https://dl-cdn.ryzerobotics.com/downloads/Tello/20180404/Tello_User_Manual_V1.2_EN.pdf
"""
import argparse
import socket
import time
from time import sleep

from AutoDrone.Drone.Drone import Drone, MoveDirection, RotateDirection
from AutoDrone.NetworkConnect import netsh_find_ssid_list, netsh_connect_network, netsh_toggle_adapter


class TelloDrone(Drone):
    BASE_SSID = 'TELLO-'

    LOCAL_HOST = ''
    BASE_PORT = 9000
    STATE_PORT = 8890
    VIDEO_PORT = 11111

    TELLO_IP = '192.168.10.1'
    TELLO_PORT = 8889

    def __init__(self, send_delay: float = 0.1, timeout: float = 1.0):
        """
        todo keep track of receive timings
        todo make observer from Andrutil
        todo use a send queue to enforce message order/spacing

        :param send_delay:
        :param timeout:
        """
        Drone.__init__(self, 'Tello', timeout)

        self.send_delay = send_delay

        self.drone_ssid = None
        self.network_connected = False

        self.send_address = (self.TELLO_IP, self.TELLO_PORT)
        self.socket_dict = {
            'base': {'address': (self.LOCAL_HOST, self.BASE_PORT),
                     'socket': socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                     'listen_thread': None,
                     'listening': None},
            'video': {'address': (self.LOCAL_HOST, self.VIDEO_PORT),
                      'socket': socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                      'listen_thread': None,
                      'listening': None},
            'state': {'address': (self.LOCAL_HOST, self.STATE_PORT),
                      'socket': socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                      'listen_thread': None,
                      'listening': None},
        }
        return

    def __str__(self):
        return f'Name: {self.name} | State: {self.state()}'

    def connect(self, scan_delay: float = 1):
        """
        Assumes only one drone network - if multiple, uses first one listed

        :return:
        """
        print(f'Attempting to establish connection to wifi network: {self.name}')

        while not self.drone_ssid:
            netsh_toggle_adapter(adapter_name='Wi-Fi')

            ssid_list = netsh_find_ssid_list(mode='bssid')
            for each_ssid in ssid_list:
                if each_ssid.startswith(self.BASE_SSID):
                    self.drone_ssid = each_ssid
                    break
            else:
                sleep(scan_delay)

        print(f'Drone network discovered: {self.drone_ssid}')

        while not self.network_connected:
            connection_results, connection_success = netsh_connect_network(network_name=self.drone_ssid)
            if connection_success:
                self.network_connected = True

        print(f'Connection to drone network established: {self.name}')
        ################################################################
        print(f'Attempting to establish connection to drone: {self.name}')

        for connection_name, connection_info in self.socket_dict.items():
            connection_socket = connection_info['socket']
            connection_address = connection_info['address']
            connection_socket.bind(connection_address)

        print(f'Network connections established with drone: {self.name}')
        ################################################################
        print(f'Initializing SDK mode of drone: {self.name}')

        self.send_command(command='command')
        print(f'SDK mode enabled: {self.name}')
        return

    def disconnect(self):
        """

        :return:
        """
        if self.state == 'flying':
            pass

        self.send_command('land')

        for connection_name, connection_info in self.socket_dict.items():
            connection_socket = connection_info['socket']
            connection_socket.close()
        return

    def state(self):
        return

    def send_command(self, command: str):
        """

        :param command:
        :return:
        """
        # adding a slight delay before sending the message seems to make the tello drone happy
        sleep(self.send_delay)
        base_connection = self.socket_dict['base']
        base_socket = base_connection['socket']

        msg = command.encode(encoding='utf-8')
        print(f'Sending message: {msg}')
        start_time = time.time()
        sent = base_socket.sendto(msg, self.send_address)
        end_time = time.time()
        send_time = end_time - start_time

        start_time = time.time()
        response = base_socket.recvfrom(1518)
        end_time = time.time()
        receive_time = end_time - start_time

        self.message_history.append({
            'sent': msg, 'response': response, 'send_time': send_time, 'receive_time': receive_time
        })

        if sent == 0:
            raise RuntimeError('socket connection broken')
        return

    def move(self, distance: float, direction: MoveDirection):
        """
        The unit of distance is centimeters.
        The SDK accepts distances of 1 to 500 centimeters.
        This translates to 0.1 to 5 meters, or 0.7 to 16.4 feet.

        :param distance:
        :param direction:
        :return:
        """
        command = f'{direction.value} {int(distance)}'
        self.send_command(command)
        return

    def rotate(self, degrees: float, direction: RotateDirection):
        """
        The SDK accepts values from 1 to 360.
        Responses are 'OK' or 'FALSE'.

        :param degrees:
        :param direction:
        :return:
        """
        command = f'{direction.value} {int(degrees)}'
        self.send_command(command)
        return

    def set_speed(self, amount: float):
        """
        The unit of speed is cm/s.
        The SDK accepts speeds from 1 to 100 centimeters/second.
        This translates to 0.1 to 3.6 KPH, or 0.1 to 2.2 MPH.
        Responses are 'OK' or 'FALSE'.

        :param amount:
        :return:
        """
        command = f'speed {int(amount)}'
        self.send_command(command)
        return

    def get_status(self):
        """
        Get current speed in KPH
        Get percent battery life remaining
        Get elapsed flight time in seconds

        :return:
        """
        speed_command = 'speed?'
        time_command = 'time?'
        battery_command = 'battery?'

        self.send_command(speed_command)
        self.send_command(time_command)
        self.send_command(battery_command)
        return


def main(main_args):
    """

    :param main_args:
    :return:
    """
    send_delay = main_args.get('send_delay', 1)
    tout = main_args.get('timeout', 20)
    scan_delay = main_args.get('scan_delay', 1)
    ###################################
    tello_drone = TelloDrone(send_delay=send_delay, timeout=tout)
    tello_drone.connect(scan_delay=scan_delay)

    start_time = time.time()
    tello_drone.send_command(command='takeoff')
    command_time = time.time()
    print(f'{command_time - start_time}')

    tello_drone.send_command(command='land')
    land_time = time.time()
    print(f'{land_time - start_time}')
    print(f'{land_time - command_time}')

    sleep(10)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--send_delay', type=float, default=0.5,
                        help='')
    parser.add_argument('--timeout', type=float, default=20,
                        help='')
    parser.add_argument('--scan_delay', type=float, default=1,
                        help='')

    args = parser.parse_args()
    main(vars(args))

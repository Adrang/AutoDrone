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
import threading
from time import sleep

import cv2
from Andrutil.Misc import time_function

from AutoDrone.NetworkConnect import netsh_find_ssid_list, netsh_connect_network, netsh_toggle_adapter


# def set_wifi_credentials(self, ssid, password):
#     """Set the Wi-Fi SSID and password. The Tello will reboot afterwords.
#     Returns:
#         bool: True for successful, False for unsuccessful
#     """
#     return self.send_control_command('wifi %s %s' % (ssid, password))
#
# def connect_to_wifi(self, ssid, password):
#     """Connects to the Wi-Fi with SSID and password.
#     Returns:
#         bool: True for successful, False for unsuccessful
#     """
#     return self.send_control_command('ap %s %s' % (ssid, password))
#
# def get_wifi(self):
#     """Get Wi-Fi SNR
#     Returns:
#         False: Unsuccessful
#         str: snr
#     """
#     return self.send_read_command('wifi?')
#
# def get_sdk_version(self):
#     """Get SDK Version
#     Returns:
#         False: Unsuccessful
#         str: SDK Version
#     """
#     return self.send_read_command('sdk?')
#
# def get_serial_number(self):
#     """Get Serial Number
#     Returns:
#         False: Unsuccessful
#         str: Serial Number
#     """
#     return self.send_read_command('sn?')
#
# def move(self, distance: float, direction: MoveDirection):
#     """
#     The unit of distance is centimeters.
#     The SDK accepts distances of 1 to 500 centimeters.
#     This translates to 0.1 to 5 meters, or 0.7 to 16.4 feet.
#
#     :param distance:
#     :param direction:
#     :return:
#     """
#     command = f'{direction.value} {int(distance)}'
#     self.send_command(command)
#     return
#
# def panic(self):
#     return
#
# def rotate(self, degrees: float, direction: RotateDirection):
#     """
#     The SDK accepts values from 1 to 360.
#     Responses are 'OK' or 'FALSE'.
#
#     :param degrees:
#     :param direction:
#     :return:
#     """
#     command = f'{direction.value} {int(degrees)}'
#     self.send_command(command)
#     return
#
# def set_speed(self, amount: float):
#     """
#     The unit of speed is cm/s.
#     The SDK accepts speeds from 1 to 100 centimeters/second.
#     This translates to 0.1 to 3.6 KPH, or 0.1 to 2.2 MPH.
#     Responses are 'OK' or 'FALSE'.
#
#     :param amount:
#     :return:
#     """
#     command = f'speed {int(amount)}'
#     self.send_command(command)
#     return

class TelloState:

    def __init__(self):
        self.state_vars = {
            'pitch': -1, 'roll': -1, 'yaw': -1,
            'speed_x': -1, 'speed_y': -1, 'speed_z': -1,
            'temperature_lowest': -1, 'temperature_highest': -1, 'barometer': -1.0,
            'distance_tof': -1, 'height': -1,
            'battery': -1, 'flight_time': -1.0,
            'acceleration_x': -1.0, 'acceleration_y': -1.0, 'acceleration_z': -1.0,
        }
        return


class TelloDrone:
    BASE_SSID = 'TELLO-'

    # Send and receive commands socket
    CLIENT_HOST = '192.168.10.1'
    CLIENT_PORT = 8889

    ANY_HOST = '0.0.0.0'
    # stream constants
    STATE_PORT = 8890
    STATE_DELAY = 0.1
    MIN_STATE_COUNT = 2

    VIDEO_UDP_URL = 'udp://0.0.0.0:11111'
    FRAME_DELAY = 1
    MIN_FRAME_COUNT = 5

    BUFFER_SIZE = 1024

    def __init__(self, send_delay: float = 0.1):
        """
        todo    add logging
        todo    build state baseline from first n values
        todo    fix issue
                    ...
                    [h264 @ 00000269a35be080] non-existing PPS 0 referenced
                    [h264 @ 00000269a35be080] decode_slice_header error
                    [h264 @ 00000269a35be080] no frame!
                    ...
        todo    break send/receive logic
        todo    make observer from Andrutil
        todo    use a send queue to enforce message order/spacing
        todo    rl agent to handle send rate - minimize time to react after sending command
        todo    add check before sending land to make sure the drone is established
                seems to react better if the drone is stable before sending next command

        :param send_delay:
        """
        self.name = 'Tello'
        self.message_history = []
        self.send_delay = send_delay

        self.drone_ssid = None
        self.network_connected = False

        # To send comments
        self.tello_address = (self.CLIENT_HOST, self.CLIENT_PORT)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind((self.ANY_HOST, self.CLIENT_PORT))

        # receive state messages
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind((self.ANY_HOST, self.STATE_PORT))

        # state information
        self.state_running = False
        self.state_history = []
        self.state_baseline = {}

        # drone streams
        self.video_capture = None
        self.frame_history = []
        return

    def connect(self, scan_delay: float = 1):
        """
        Assumes only one drone network - if multiple, uses first one listed

        :return:
        """
        print(f'Attempting to discover drone SSID: {self.name}')
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
        ################################################################
        print(f'Attempting to establish connection to wifi network: {self.drone_ssid}')
        while not self.network_connected:
            connection_results, connection_success = netsh_connect_network(network_name=self.drone_ssid)
            if connection_success:
                self.network_connected = True
        print(f'Connection to drone network established: {self.drone_ssid}')
        ################################################################
        print(f'Initializing SDK mode of drone: {self.name}')
        message_response = self.__send_command('command')
        if message_response != 'OK' and message_response != 'ok':
            raise RuntimeError('Unable to connect to drone')
        print(f'SDK mode enabled: {self.name}')
        ################################################################
        print(f'Starting state thread from drone: {self.name}')
        video_thread = threading.Thread(target=self.state_stream, args=(), daemon=True)
        video_thread.start()
        while len(self.state_history) < self.MIN_STATE_COUNT:
            sleep(0.1)
        print(f'State stream established: {self.name}')
        ################################################################
        print(f'Starting video thread from drone: {self.name}')
        video_thread = threading.Thread(target=self.video_stream, args=(), daemon=True)
        video_thread.start()
        while len(self.frame_history) < self.MIN_FRAME_COUNT:
            sleep(0.1)
        print(f'Video stream established: {self.name}')
        return

    def state_stream(self):
        self.state_running = True
        while self.state_running:
            try:
                state_bytes, _ = self.state_socket.recvfrom(self.BUFFER_SIZE)
                state_str = state_bytes.decode('utf-8').strip()
                state_val_list = state_str.split(';')
                state_dict = {
                    state_entry.split(':')[0]: state_entry.split(':')[1]
                    for state_entry in state_val_list
                    if len(state_entry) > 0
                }
                # todo add lock
                self.state_history.append(state_dict)
            except Exception as e:
                print(f'{e}')
            sleep(self.STATE_DELAY)
        return

    def video_stream(self):
        message_response = self.__send_command('streamon')
        if message_response != 'OK' and message_response != 'ok':
            raise RuntimeError('Could not start video stream')

        self.video_capture = cv2.VideoCapture(self.VIDEO_UDP_URL, cv2.CAP_FFMPEG)
        if not self.video_capture.isOpened():
            self.video_capture.open(self.VIDEO_UDP_URL)

        while self.video_capture.isOpened():
            read_success, video_frame = self.video_capture.read()
            if read_success:
                cv2.imshow('frame', video_frame)
                self.frame_history.append(video_frame)
            cv2.waitKey(self.FRAME_DELAY)
        self.video_capture.release()
        cv2.destroyAllWindows()

        message_response = self.__send_command('streamoff')
        if message_response != 'OK' and message_response != 'ok':
            raise RuntimeError('Could not start video stream')
        return

    def __send_command(self, command: str):
        """

        :param command:
        :return:
        """
        try:
            # adding a slight delay before sending the message seems to make the tello drone happy
            sleep(self.send_delay)

            msg = command.encode(encoding='utf-8')
            func_args = (msg, self.tello_address)
            _, send_time = time_function(self.client_socket.sendto, *func_args)

            func_args = (self.BUFFER_SIZE,)
            (response_bytes, _), receive_time = time_function(self.client_socket.recvfrom, *func_args)
            response_str = response_bytes.decode('utf-8')

            self.message_history.append({
                'sent': msg, 'response': response_str, 'send_time': send_time, 'receive_time': receive_time
            })
        except UnicodeDecodeError:
            response_str = 'error'
        return response_str

    def takeoff(self):
        message_response = self.__send_command('takeoff')
        return message_response != 'OK' and message_response != 'ok'

    def land(self):
        message_response = self.__send_command('land')
        return message_response != 'OK' and message_response != 'ok'

    def get_state(self):
        return self.state_history[-1]


def main(main_args):
    """

    :param main_args:
    :return:
    """
    send_delay = main_args.get('send_delay', 1)
    scan_delay = main_args.get('scan_delay', 1)
    ###################################
    tello_drone = TelloDrone(send_delay=send_delay)
    tello_drone.connect(scan_delay=scan_delay)

    tello_state = tello_drone.get_state()
    for state_name, state_val in tello_state.items():
        print(f'{state_name}:{state_val}')

    # start_time = time.time()
    # tello_drone.takeoff()
    # command_time = time.time()
    # print(f'{command_time - start_time}')
    #
    tello_state = tello_drone.get_state()
    for state_name, state_val in tello_state.items():
        print(f'{state_name}:{state_val}')

    sleep(2)

    # tello_drone.land()
    # land_time = time.time()
    # print(f'{land_time - start_time}')
    # print(f'{land_time - command_time}')

    sleep(10)
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--send_delay', type=float, default=1,
                        help='')
    parser.add_argument('--scan_delay', type=float, default=1,
                        help='')

    args = parser.parse_args()
    main(vars(args))

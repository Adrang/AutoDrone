"""
@title
@description

https://github.com/damiafuentes/DJITelloPy
https://github.com/microlinux/tello

https://dl-cdn.ryzerobotics.com/downloads/Tello/Tello%20SDK%202.0%20User%20Guide.pdf
https://dl-cdn.ryzerobotics.com/downloads/Tello/20180404/Tello_User_Manual_V1.2_EN.pdf
"""
import argparse
import json
import os
import socket
import threading
import time
from datetime import datetime
from time import sleep

import cv2
from Andrutil.Misc import time_function

from AutoDrone import DATA_DIR
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
    # Network constants
    BASE_SSID = 'TELLO-'
    NETWORK_SCAN_DELAY = 0.5

    # Send and receive commands socket
    CLIENT_HOST = '192.168.10.1'
    CLIENT_PORT = 8889
    SEND_DELAY = 0.1

    # receive constants
    BUFFER_SIZE = 1024
    ANY_HOST = '0.0.0.0'

    # state stream constants
    STATE_PORT = 8890
    STATE_DELAY = 0.1

    # video stream constants
    VIDEO_UDP_URL = 'udp://0.0.0.0:11111'
    FRAME_DELAY = 1

    def __init__(self):
        """
        todo    fix issue
                    ...
                    [h264 @ 00000269a35be080] non-existing PPS 0 referenced
                    [h264 @ 00000269a35be080] decode_slice_header error
                    [h264 @ 00000269a35be080] no frame!
                    ...
        todo    make observer from Andrutil
        todo    rl agent to handle send rate - minimize time to react after sending command
        todo    add check before sending land to make sure the drone is established
                seems to react better if the drone is stable before sending next command
        """
        current_time = time.time()
        date_time = datetime.fromtimestamp(time.time())
        time_str = date_time.strftime("%Y-%m-%d-%H-%M-%S")

        self.name = 'Tello'
        self.id = f'{self.name}_{time_str}_{int(current_time)}'
        self.save_directory = os.path.join(DATA_DIR, 'tello', f'{self.id}')
        if not os.path.isdir(self.save_directory):
            os.makedirs(self.save_directory)

        # wifi network info
        self.drone_ssid = None
        self.network_connected = False
        self.metadata_fname = os.path.join(self.save_directory, f'metadata_{self.id}.json')

        # To send comments
        self.tello_address = (self.CLIENT_HOST, self.CLIENT_PORT)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_socket.bind((self.ANY_HOST, self.CLIENT_PORT))

        # receive state messages
        self.state_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.state_socket.bind((self.ANY_HOST, self.STATE_PORT))

        # send and receive message logging
        self.message_history = []
        self.message_history_fname = os.path.join(self.save_directory, f'messages_{self.id}.json')

        # state information
        self.state_stream_running = False
        self.state_history = []
        self.state_baseline = {}
        self.state_history_fname = os.path.join(self.save_directory, f'states_{self.id}.json')

        # video stream
        self.frame_history = []
        self.video_capture = None
        self.video_writer = None
        self.video_fname = os.path.join(self.save_directory, f'{self.id}.avi')
        return

    def connect(self):
        """

        :return:
        """
        self.connect_wifi()
        ################################################################
        self.connect_drone()
        ################################################################
        self.start_state_thread()
        self.start_video_thread()
        return

    def cleanup(self):
        self.set_video_stream_off()
        self.state_stream_running = False

        # slight delay to make sure all threads end properly
        sleep(1)

        # todo    build state baseline from first n values
        meta_data = {
            'id': self.id, 'ssid': self.drone_ssid,
            'num_messages': len(self.message_history),
            'num_states': len(self.state_history),
            'num_frames': len(self.frame_history),
        }
        with open(self.metadata_fname, 'w+') as save_file:
            json.dump(fp=save_file, obj=meta_data, indent=2)

        with open(self.message_history_fname, 'w+') as save_file:
            json.dump(fp=save_file, obj=self.message_history, indent=2)

        with open(self.state_history_fname, 'w+') as save_file:
            json.dump(fp=save_file, obj=self.state_history, indent=2)
        return

    def connect_drone(self):
        print(f'Initializing SDK mode of drone: {self.name}')
        message_response = self.__send_command('command', wait_for_response=True)
        if message_response != 'OK' and message_response != 'ok':
            raise RuntimeError('Unable to connect to drone')
        print(f'SDK mode enabled: {self.name}')
        return

    def connect_wifi(self):
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
                sleep(self.NETWORK_SCAN_DELAY)
        print(f'Drone network discovered: {self.drone_ssid}')
        ################################################################
        print(f'Attempting to establish connection to wifi network: {self.drone_ssid}')
        while not self.network_connected:
            connection_results, connection_success = netsh_connect_network(network_name=self.drone_ssid)
            if connection_success:
                self.network_connected = True
        print(f'Connection to drone network established: {self.drone_ssid}')
        return

    def start_state_thread(self):
        print(f'Starting state thread from drone: {self.name}')
        video_thread = threading.Thread(target=self.state_stream, args=(), daemon=True)
        video_thread.start()
        while not self.state_stream_running:
            sleep(0.1)
        print(f'State stream established: {self.name}')
        return

    def state_stream(self):
        self.state_stream_running = True
        while self.state_stream_running:
            try:
                state_bytes, _ = self.state_socket.recvfrom(self.BUFFER_SIZE)
                initial_time = time.time()
                state_str = state_bytes.decode('utf-8').strip()
                state_val_list = state_str.split(';')
                state_dict = {
                    state_entry.split(':')[0]: state_entry.split(':')[1]
                    for state_entry in state_val_list
                    if len(state_entry) > 0
                }
                # todo add lock
                state_dict['timestamp'] = initial_time
                self.state_history.append(state_dict)
            except Exception as e:
                print(f'{e}')
            sleep(self.STATE_DELAY)
        return

    def start_video_thread(self):
        print(f'Starting video thread from drone: {self.name}')
        video_thread = threading.Thread(target=self.video_stream, args=(), daemon=True)
        video_thread.start()
        while not self.video_stream_running():
            sleep(0.1)
        print(f'Video stream established: {self.name}')
        return

    def video_stream(self):
        self.set_video_stream_on()

        self.video_capture = cv2.VideoCapture(self.VIDEO_UDP_URL, cv2.CAP_FFMPEG)
        if not self.video_capture.isOpened():
            raise RuntimeError('Could not open video stream')

        # discard first read and make sure all is reading correctly
        read_success, video_frame = self.video_capture.read()
        if not read_success:
            raise RuntimeError('Error reading from video stream')

        # save capture width and height for later when saving the video
        fps = 30
        frame_width = int(self.video_capture.get(3))
        frame_height = int(self.video_capture.get(4))
        codec_str = 'MJPG'
        self.video_writer = cv2.VideoWriter(
            self.video_fname, cv2.VideoWriter_fourcc(*codec_str),
            fps, (frame_width, frame_height)
        )

        window_name = 'Video feed'
        cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
        while self.video_capture.isOpened():
            read_success, video_frame = self.video_capture.read()
            if read_success:
                cv2.imshow(window_name, video_frame)
                self.video_writer.write(video_frame.astype('uint8'))
                self.frame_history.append(video_frame)
            cv2.waitKey(self.FRAME_DELAY)
        self.video_capture.release()
        self.video_writer.release()
        cv2.destroyAllWindows()
        self.set_video_stream_off()
        return

    def video_stream_running(self):
        return self.video_capture and self.video_capture.isOpened()

    def __send_command(self, command: str, wait_for_response: bool):
        """
        todo    use a send queue to enforce message order/spacing

        :param command:
        :param wait_for_response:
        :return:
        """
        try:
            # adding a slight delay before sending the message seems to make the tello drone happy
            sleep(self.SEND_DELAY)

            initial_time = time.time()
            msg = command.encode(encoding='utf-8')
            func_args = (msg, self.tello_address)
            _, send_time = time_function(self.client_socket.sendto, *func_args)

            response_str = None
            receive_time = None
            if wait_for_response:
                func_args = (self.BUFFER_SIZE,)
                (response_bytes, _), receive_time = time_function(self.client_socket.recvfrom, *func_args)
                response_str = response_bytes.decode('utf-8')

            self.message_history.append({
                'timestamp': initial_time,
                'sent': command, 'send_time': send_time,
                'response': response_str, 'receive_time': receive_time
            })
        except UnicodeDecodeError:
            response_str = 'error'
        return response_str

    def takeoff(self):
        message_response = self.__send_command('takeoff', wait_for_response=True)
        return message_response != 'OK' and message_response != 'ok'

    def land(self):
        message_response = self.__send_command('land', wait_for_response=True)
        return message_response != 'OK' and message_response != 'ok'

    def set_video_stream_off(self):
        message_response = self.__send_command('streamoff', wait_for_response=True)
        if message_response != 'OK' and message_response != 'ok':
            raise RuntimeError('Could not stop video stream')
        return

    def set_video_stream_on(self):
        message_response = self.__send_command('streamon', wait_for_response=True)
        if message_response != 'OK' and message_response != 'ok':
            raise RuntimeError('Error when starting stream from drone')
        return

    def get_state(self):
        return self.state_history[-1]


def main(main_args):
    """

    :param main_args:
    :return:
    """
    send_delay = main_args.get('send_delay', 0.1)
    scan_delay = main_args.get('scan_delay', 0.1)
    ###################################
    tello_drone = TelloDrone()
    tello_drone.NETWORK_SCAN_DELAY = scan_delay
    tello_drone.SEND_DELAY = send_delay
    ###################################
    tello_drone.connect()
    #
    # start_time = time.time()
    # tello_drone.takeoff()
    # command_time = time.time()
    # print(f'{command_time - start_time}')
    #
    # sleep(2)
    #
    # tello_drone.land()
    # land_time = time.time()
    # print(f'{land_time - start_time}')
    # print(f'{land_time - command_time}')
    #
    sleep(5)
    tello_drone.cleanup()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--send_delay', type=float, default=1,
                        help='')
    parser.add_argument('--scan_delay', type=float, default=1,
                        help='')

    args = parser.parse_args()
    main(vars(args))

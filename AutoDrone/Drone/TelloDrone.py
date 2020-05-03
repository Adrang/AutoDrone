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
import math
import os
import socket
import subprocess
import threading
import time
from datetime import datetime
from enum import Enum
from time import sleep

import cv2
from Andrutil.Misc import time_function
from Andrutil.ObserverObservable import Observable

from AutoDrone import DATA_DIR, TERMINAL_COLUMNS
from AutoDrone.NetworkConnect import netsh_find_ssid_list, netsh_connect_network, netsh_toggle_adapter


class MoveDirection(Enum):
    """

    """
    UP = 'up'
    DOWN = 'down'
    LEFT = 'left'
    RIGHT = 'right'
    FORWARDS = 'forwards'
    BACK = 'back'


class RotateDirection(Enum):
    """

    """
    CLOCKWISE = 'cw'
    COUNTER_CLOCKWISE = 'ccw'


class FlipDirection(Enum):
    """

    """
    LEFT = 'l'
    RIGHT = 'r'
    FORWARDS = 'f'
    BACK = 'b'


class TelloDrone(Observable):
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
    NUM_BASELINE_VALS = 10

    # video stream constants
    VIDEO_UDP_URL = f'udp://0.0.0.0:11111'
    # VIDEO_UDP_URL = 'udp://0.0.0.0:11111'
    FRAME_DELAY = 1

    def __init__(self, adapter_name: str, receive_timeout: float = 4.0):
        """
        The Tello SDK connects to the aircraft through a Wi-Fi UDP port, allowing users to control the
        drone with text commands

        If no command is received for 15 seconds, the tello will land automatically.
        Long press Tello for 5 seconds while Tello is on, and the indicator light will turn off and then
        flash yellow. When the indicator light shows a flashing yellow light, the Wi-Fi SSID and password
        will be reset to the factory settings, and there is no password by default.
        For Tello use SDK 1.3 for Tello EDU SDK 2.0.

        Commands can be broken down into three sets:
            Control
                Returns 'ok' if the command was successful
                Returns 'error' or an informational result code if the command failed
            Set
                Sets new sub-parameter values
                Returns 'ok' if the command was successful
                Returns 'error' or an informational result code if the command failed
            Read
                Returns the current value of the sub-parameter
        todo remove observable patterns
        """
        Observable.__init__(self)
        current_time = time.time()
        date_time = datetime.fromtimestamp(time.time())
        time_str = date_time.strftime("%Y-%m-%d-%H-%M-%S")

        # identification information
        self.name = 'Tello'
        self.id = f'{self.name}_{time_str}_{int(current_time)}'

        self.save_directory = os.path.join(DATA_DIR, 'tello', f'{self.id}')
        if not os.path.isdir(self.save_directory):
            os.makedirs(self.save_directory)

        # wifi network info
        self.adapter_name = adapter_name
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
        self.receive_timeout = receive_timeout

        # send and receive message logging
        self.message_history = []
        self.message_history_fname = os.path.join(self.save_directory, f'messages_{self.id}.json')
        self.message_lock = threading.Lock()

        # state information
        self.state_stream_running = False
        self.state_history = []
        self.state_lock = threading.Lock()
        self.state_baseline = {}
        self.state_history_fname = os.path.join(self.save_directory, f'states_{self.id}.json')

        # video stream
        self.frame_history = []
        self.video_lock = threading.Lock()
        self.video_capture = None
        self.video_writer = None
        self.video_fname = os.path.join(self.save_directory, f'{self.id}.avi')

        # drone status
        self.sdk_mode = False
        self.is_flying = False
        return

    def __send_command(self, command: str):
        """
        todo    use a send queue to enforce message order/spacing

        :param command:
        :return:
        """
        if not self.network_connected:
            return 'drone is not connected'

        initial_time = None
        send_time = None
        receive_time = None
        try:
            # adding a slight delay before sending the message seems to make the tello drone happy
            sleep(self.SEND_DELAY)

            msg = command.encode(encoding='utf-8')
            initial_time = time.time()
            func_args = (msg, self.tello_address)
            _, send_time = time_function(self.client_socket.sendto, *func_args)

            self.client_socket.settimeout(self.receive_timeout)
            func_args = (self.BUFFER_SIZE,)
            response, receive_time = time_function(self.client_socket.recvfrom, *func_args)
            if isinstance(response, Exception):
                response_str = str(response)
            else:
                (response_bytes, _) = response
                response_str = response_bytes.decode('utf-8')
        except UnicodeDecodeError:
            response_str = 'error'
        with self.message_lock:
            self.message_history.append({
                'timestamp': initial_time,
                'sent': command, 'send_time': send_time,
                'response': response_str, 'receive_time': receive_time
            })
        return response_str

    def __connect_wifi(self):
        """
        Assumes only one drone network - if multiple, uses first one listed
        This is a mess, but it works.
        todo Break into two parts
                discover ssid
                connect to wifi


        :return:
        """
        self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                  'value': f'Attempting to discover drone SSID: {self.name}'})
        while not self.drone_ssid:
            netsh_toggle_adapter(adapter_name=self.adapter_name)
            ssid_list = netsh_find_ssid_list(mode='bssid')
            for each_ssid in ssid_list:
                if each_ssid.startswith(self.BASE_SSID):
                    self.drone_ssid = each_ssid
                    break
            else:
                sleep(self.NETWORK_SCAN_DELAY)
        self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                  'value': f'Drone network discovered: {self.drone_ssid}'})
        ################################################################
        self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                  'value': f'Attempting to establish connection to wifi network: {self.drone_ssid}'})
        while not self.network_connected:
            connection_results, connection_success = netsh_connect_network(
                network_name=self.drone_ssid, interface=self.adapter_name
            )
            if connection_success:
                self.network_connected = True
        self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                  'value': f'Connection to drone network established: {self.drone_ssid}'})
        return

    def __init_sdk_mode(self):
        """

        :return:
        """
        self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                  'value': f'Initializing SDK mode of drone: {self.name}'})
        message_response = self.__send_command('command')
        if message_response == 'ok':
            self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                      'value': f'SDK mode enabled: {self.name}'})
            self.start_video_thread()
            self.start_state_thread()
        return message_response == 'ok'

    def connect(self):
        """

        :return:
        """
        max_sdk_attempts = 5
        while not self.sdk_mode:
            while not self.network_connected:
                try:
                    self.__connect_wifi()
                except subprocess.SubprocessError as se:
                    self.set_changed_message({'timestamp': time.time(), 'type': 'rte', 'value': f'{se}'})
                sleep(self.NETWORK_SCAN_DELAY)

            for attempt_count in range(max_sdk_attempts):
                try:
                    if self.__init_sdk_mode():
                        self.sdk_mode = True
                        self.set_changed_message({'timestamp': time.time(), 'type': 'connect', 'value': True})
                        break
                except RuntimeError as rte:
                    self.set_changed_message({'timestamp': time.time(), 'type': 'rte', 'value': f'{rte}'})
                sleep(self.SEND_DELAY)
        return

    def cleanup(self):
        """

        :return:
        """
        self.control_streamoff()
        self.state_stream_running = False

        # slight delay to make sure all threads end properly
        sleep(1)

        meta_data = {
            'id': self.id, 'ssid': self.drone_ssid,
            'num_messages': len(self.message_history),
            'num_states': len(self.state_history),
            'num_frames': len(self.frame_history),
        }
        with open(self.metadata_fname, 'w+') as save_file:
            json.dump(fp=save_file, obj=meta_data, indent=2)

        with self.message_lock:
            with open(self.message_history_fname, 'w+') as save_file:
                json.dump(fp=save_file, obj=self.message_history, indent=2)

        with self.state_lock:
            with open(self.state_history_fname, 'w+') as save_file:
                json.dump(fp=save_file, obj=self.state_history, indent=2)
        return

    def start_state_thread(self):
        """

        :return:
        """
        # self.set_changed_message({'timestamp': time.time(), 'type': 'status',
        #                           'value': f'Starting state thread from drone: {self.name}'})
        video_thread = threading.Thread(target=self.listen_state, args=(), daemon=True)
        video_thread.start()
        while not self.state_stream_running:
            sleep(0.1)
        # self.set_changed_message({'timestamp': time.time(), 'type': 'status',
        #                           'value': f'State stream established: {self.name}'})
        return

    def listen_state(self):
        """

        :return:
        """
        baseline_list = []
        for idx in range(0, self.NUM_BASELINE_VALS):
            state_bytes, _ = self.state_socket.recvfrom(self.BUFFER_SIZE)
            state_str = state_bytes.decode('utf-8').strip()
            state_val_list = state_str.split(';')
            state_dict = {
                state_entry.split(':')[0]: state_entry.split(':')[1]
                for state_entry in state_val_list
                if len(state_entry) > 0
            }
            baseline_list.append(state_dict)
        state_keys = baseline_list[0].keys()
        for each_key in state_keys:
            running_val = 0
            for each_entry in baseline_list:
                entry_val = float(each_entry[each_key])
                running_val += entry_val
            average_val = running_val / len(baseline_list)
            self.state_baseline[each_key] = average_val

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
                state_dict['timestamp'] = initial_time
                with self.state_lock:
                    self.state_history.append(state_dict)
                # todo add messages to queue
                self.set_changed_message({'timestamp': time.time(), 'type': 'state', 'value': state_dict})
            except Exception as e:
                self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                          'value': f'{e}'})
            sleep(self.STATE_DELAY)
        return

    def is_state_listening(self):
        """

        :return:
        """
        return self.state_stream_running

    def get_last_state(self):
        """
        Gets the latest state information from the stream to port 8890.

        pitch:  %d:     attitude pitch, degrees
        roll:   %d:     attitude roll, degrees
        yaw:    %d:     attitude yaw, degrees
        vgx:    %d:     speed x
        vgy:    %d:     speed y
        vgz:    %d:     speed z
        templ:  %d:     lowest temperature, degrees celsius
        temph:  %d:     highest temperature, degrees celsius
        tof:    %d:     distance from point of takeoff, centimeters
        h:      %d:     height from ground, centimeters
        bat:    %d:     current battery level, percentage
        baro:   %0.2f:  pressure measurement, cm
        time:   %d:     time motors have been on, seconds
        agx:    %0.2f:  acceleration x
        agy:    %0.2f:  acceleration y
        agz:    %0.2f:  acceleration z

        :return:
        """
        last_state = self.state_history[-1] if len(self.state_history) > 0 else None
        return last_state

    def start_video_thread(self):
        """

        :return:
        """
        self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                  'value': f'Starting video thread from drone: {self.name}'})
        video_thread = threading.Thread(target=self.listen_video, args=(), daemon=True)
        video_thread.start()
        while not self.is_video_listening():
            sleep(0.1)
        self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                  'value': f'Video stream established: {self.name}'})
        return

    def listen_video(self):
        """
        always on

        :return:
        """
        self.control_streamoff()
        self.control_streamon()

        self.video_capture = cv2.VideoCapture(self.VIDEO_UDP_URL, cv2.CAP_FFMPEG)
        if not self.video_capture.isOpened():
            self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                      'value': f'Could not open video stream'})
            return

        # discard first read and make sure all is reading correctly
        read_success, video_frame = self.video_capture.read()
        if not read_success:
            self.set_changed_message({'timestamp': time.time(), 'type': 'status',
                                      'value': f'Error reading from video stream'})
            return

        # save capture width and height for later when saving the video
        fps = 30
        frame_width = int(self.video_capture.get(3))
        frame_height = int(self.video_capture.get(4))

        codec_str = 'MJPG'
        self.video_writer = cv2.VideoWriter(
            self.video_fname, cv2.VideoWriter_fourcc(*codec_str),
            fps, (frame_width, frame_height)
        )

        while self.video_capture.isOpened():
            read_success, video_frame = self.video_capture.read()
            if read_success:
                self.set_changed_message({'timestamp': time.time(), 'type': 'video', 'value': video_frame})
                self.frame_history.append(video_frame)
                self.video_writer.write(video_frame.astype('uint8'))
            cv2.waitKey(self.FRAME_DELAY)

        self.video_capture.release()
        self.video_writer.release()
        cv2.destroyAllWindows()
        return

    def is_video_listening(self):
        """

        :return:
        """
        return self.video_capture and self.video_capture.isOpened()

    def get_last_frame(self):
        """
        Gets the latest video frame from the stream to port 11111.

        :return:
        """
        last_frame = self.frame_history[-1] if len(self.frame_history) > 0 else None
        return last_frame

    def control_command(self):
        """
        command

        puts the drone into SDK mode

        ok, error

        :return:
        """
        command_str = f'command'
        message_response = self.__send_command(command_str)
        return message_response

    def control_takeoff(self):
        """
        takeoff

        auto-takeoff

        ok, error

        :return:
        """
        command_str = f'takeoff'
        message_response = self.__send_command(command_str)
        return message_response

    def control_land(self):
        """
        lland

        auto-land

        ok, error

        :return:
        """
        command_str = f'land'
        message_response = self.__send_command(command_str)
        return message_response

    def control_streamon(self):
        """
        streamon

        sets the video stream on

        ok, error

        :return:
        """
        command_str = f'streamon'
        message_response = self.__send_command(command_str)
        return message_response

    def control_streamoff(self):
        """
        streamoff

        sets the video stream off

        ok, error

        :return:
        """
        command_str = f'streamoff'
        message_response = self.__send_command(command_str)
        return message_response

    def control_emergency(self):
        """
        emergency

        immediately stops all motors

        ok, error

        :return:
        """
        command_str = f'emergency'
        message_response = self.__send_command(command_str)
        return message_response

    def control_up(self, distance_cm):
        """
        up x

        fly up a distance of x centimeters
        x: 20 - 500

        ok, error

        :return:
        """
        command_str = f'up {int(distance_cm)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_down(self, distance_cm):
        """
        down x

        fly down a distance of x centimeters
        x: 20 - 500

        ok, error

        :return:
        """
        command_str = f'down {int(distance_cm)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_left(self, distance_cm):
        """
        left x

        fly left a distance of x centimeters
        x: 20 - 500

        ok, error

        :return:
        """
        command_str = f'left {int(distance_cm)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_right(self, distance_cm):
        """
        right x

        fly right a distance of x centimeters
        x: 20 - 500

        ok, error

        :return:
        """
        command_str = f'right {int(distance_cm)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_forward(self, distance_cm):
        """
        forward x

        fly forward a distance of x centimeters
        x: 20 - 500

        ok, error

        :return:
        """
        command_str = f'forward {int(distance_cm)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_back(self, distance_cm):
        """
        back x

        fly backwards a distance of x centimeters
        x: 20 - 500

        ok, error

        :return:
        """
        command_str = f'back {int(distance_cm)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_cw(self, degrees: float):
        """
        cw x

        rotate x degrees clockwise
        x: 1 - 3600

        ok, error

        :return:
        """
        command_str = f'cw {int(degrees)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_ccw(self, degrees: float):
        """
        cxw x

        rotate x degrees counter clockwise
        x: 1 - 3600

        ok, error

        :return:
        """
        command_str = f'ccw {int(degrees)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_flip(self, direction: FlipDirection):
        """
        flip x

        perform a flip
        l: left
        r: right
        f: forward
        b: back

        ok, error

        :return:
        """
        command_str = f'flip {direction.value}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_go(self, x_end: int, y_end: int, z_end: int, speed_cms: float):
        """
        go x y z speed

        fly to position (x,y,z) at speed (cm/s)
        x: 20-500
        y: 20-500
        z: 20-500
        speed: 10-100

        ok, error

        :return:
        """
        command_str = f'go {x_end} {y_end} {z_end} {int(speed_cms)}'
        message_response = self.__send_command(command_str)
        return message_response

    def control_curve(self, x_start, y_start, z_start, x_end, y_end, z_end, speed_cms):
        """
        curve x1 y1 z1 x2 y2 z2 speed

        fly a curve defined by the starting and ending vector positions at speed (cm/s)
        x1, x2: 20-500
        y1, y2: 20-500
        z1, z2: 20-500
        Note:
            The arc radius must be within the range of 0.5-10 meters.
            x/y/z can’t be between -20 – 20 at the same time.

        ok, error

        :return:
        """
        command_str = f'curve {x_start} {y_start} {z_start} {x_end} {y_end} {z_end} {int(speed_cms)}'
        message_response = self.__send_command(command_str)
        return message_response

    def set_speed(self, speed_cms):
        """
        speed x

        set speed to x (cm/s)
        x: 10-100

        ok, error

        :param speed_cms:
        :return:
        """
        command_str = f'speed {int(speed_cms)}'
        message_response = self.__send_command(command_str)
        return message_response

    def set_rc(self, left_right, forward_back, up_down, yaw):
        """
        Send RC control via four channels.

        left/right (-100~100)
        forward/backward (-100~100)
        up/down (-100~100)
        yaw (-100~100)

        ok
        error

        :return:
        """
        command_str = f'rc {left_right} {forward_back} {up_down} {yaw}'
        message_response = self.__send_command(command_str)
        return message_response

    def get_speed(self):
        """
        speed?

        get current speed (cm/s)

        x: 1-100

        :return:
        """
        last_state = self.get_last_state()
        vgx = float(last_state['vgx'])
        vgy = float(last_state['vgy'])
        vgz = float(last_state['vgz'])

        radicand = (vgx ** 2) + (vgy ** 2) + (vgz ** 2)
        total = math.sqrt(radicand)
        value = {
            'vgx': vgx,
            'vgy': vgy,
            'vgz': vgz,
            'total': total
        }
        return value

    def get_battery(self):
        """
        battery?

        get current battery percentage

        x: 0-100

        :return:
        """
        last_state = self.get_last_state()
        value = float(last_state['bat'])
        return value

    def get_time(self):
        """
        time?

        get current fly time (s)

        time
        :return:
        """
        last_state = self.get_last_state()
        value = float(last_state['time'])
        return value

    def get_wifi(self):
        """
        wifi?

        get Wi-Fi SNR

        snr

        :return:
        """
        command_str = f'wifi?'
        message_response = self.__send_command(command_str)
        return message_response

    def get_height(self):
        """

        height?

        get height (cm)

        x: 0-3000

        :return:
        """
        last_state = self.get_last_state()
        value = float(last_state['h'])
        return value

    def get_temp(self):
        """
        temp?

        get temperature (C)

        x: 0-90

        :return:
        """
        last_state = self.get_last_state()
        temp_low = float(last_state['templ'])
        temp_high = float(last_state['temph'])
        value = {
            'templ': temp_low,
            'temph': temp_high,
            'range': temp_high - temp_low
        }
        return value

    def get_attitude(self):
        """
        attitude?

        get IMU attitude data

        pitch roll yaw

        :return:
        """
        last_state = self.get_last_state()
        pitch = float(last_state['pitch'])
        roll = float(last_state['roll'])
        yaw = float(last_state['yaw'])
        value = {
            'pitch': pitch,
            'roll': roll,
            'yaw': yaw
        }
        return value

    def get_baro(self):
        """
        baro?

        get barometer value (m)

        x

        :return:
        """
        last_state = self.get_last_state()
        value = float(last_state['baro'])
        return value

    def get_acceleration(self):
        """
        acceleration?

        get IMU angular acceleration data (0.001g)

        x y z

        :return:
        """
        last_state = self.get_last_state()
        agx = float(last_state['agx'])
        agy = float(last_state['agy'])
        agz = float(last_state['agz'])

        radicand = (agx ** 2) + (agy ** 2) + (agz ** 2)
        total = math.sqrt(radicand)
        value = {
            'agx': agx,
            'agy': agy,
            'agz': agz,
            'total': total
        }
        return value

    def get_tof(self):
        """
        tof?

        get distance value from point of takeoff (cm)

        x: 30-1000

        :return:
        """
        last_state = self.get_last_state()
        value = float(last_state['tof'])
        return value


def main(main_args):
    """

    :param main_args:
    :return:
    """
    from AutoDrone.PrintObserver import PrintObserver
    from AutoDrone.ImageObserver import ImageObserver
    ###################################
    send_delay = main_args.get('send_delay', 0.1)
    scan_delay = main_args.get('scan_delay', 0.1)
    ###################################
    tello_drone = TelloDrone(adapter_name='Wi-Fi')
    PrintObserver(observable_list=[tello_drone])
    ImageObserver(observable_list=[tello_drone])
    ###################################
    tello_drone.NETWORK_SCAN_DELAY = scan_delay
    tello_drone.SEND_DELAY = send_delay
    tello_drone.connect()
    ###################################
    battery = tello_drone.get_battery()
    speed = tello_drone.get_speed()
    time_aloft = tello_drone.get_time()
    wifi = tello_drone.get_wifi()
    height = tello_drone.get_height()
    accel = tello_drone.get_acceleration()
    attitude = tello_drone.get_attitude()
    baro = tello_drone.get_baro()
    temp = tello_drone.get_temp()
    tof = tello_drone.get_tof()
    state = tello_drone.get_last_state()

    print('-' * TERMINAL_COLUMNS)
    print(f'Battery:        {battery}')
    print(f'wifi info:      {wifi}')
    print('-' * TERMINAL_COLUMNS)
    print(f'Speed:          {speed}')
    print(f'height:         {height}')
    print(f'attitude:       {attitude}')
    print(f'time aloft:     {time_aloft}')
    print(f'time of flight: {tof}')
    print(f'acceleration:   {accel}')
    print(f'barometer:      {baro}')
    print(f'temperature:    {temp}')
    print('-' * TERMINAL_COLUMNS)
    for each_key, each_val in state.items():
        print(f'{each_key}: {each_val}')
    print('-' * TERMINAL_COLUMNS)

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

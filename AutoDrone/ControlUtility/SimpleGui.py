"""
@title
@description
"""
import argparse
import os
import threading

# noinspection PyPep8Naming
import PySimpleGUI as sg
import cv2
from Andrutil.ObserverObservable import Observer

from AutoDrone import IMAGE_RESOURCES_DIR
from AutoDrone.AiControl.AutoControl import AutoControl
from AutoDrone.AiControl.GetstureControl import GestureControl
from AutoDrone.AudioTranslate.Speech2Text import Speech2Text
from AutoDrone.Drone.TelloDrone import TelloDrone


class ControlGui(Observer):
    FULL_THEME_LIST = sg.theme_list()
    DEFAULT_PIXELS_TO_CHARS_SCALING = (10, 26)

    def __init__(self, title: str, drone: TelloDrone,
                 auto_control: AutoControl, gesture_control: GestureControl, speech_translator: Speech2Text):
        Observer.__init__(self, observable_list=[drone, auto_control, gesture_control, speech_translator])
        auto_control.subscribe(self)

        self.title = title
        self.window = None
        self.layout = None
        self.run_mode = None
        self.speed = 20

        self.drone = drone
        self.auto_control = auto_control
        self.gesture_control = gesture_control
        self.speech_text = speech_translator
        self.speech_text.start_listener()

        self.color_connected = ('white', 'black')
        self.color_disconnected = ('black', 'white')

        self.screen_width, self.screen_height = sg.Window.get_screen_size()
        self.window_width = 100
        self.window_height = 100

        self.video_scale_factor = 0.75
        self.video_height = int(720 * self.video_scale_factor)
        self.video_width = int(960 * self.video_scale_factor)

        self.button_direction_list = ['up', 'down', 'left', 'right']
        self.run_mode_list = ['manual', 'auto', 'gesture']

        self.build_layout()
        self.create_window()
        return

    def build_layout(self):
        """
        All the stuff inside your window.

        :return:
        """
        # pad - pixels - ((left, right), (top, bottom))
        title_pad = ((0, 0), (0, 0))

        simple_control_pad = ((0, 0), (0, 0))

        mid_top_pad = ((35, 35), (100, 0))
        mid_bot_pad = ((35, 35), (0, 100))
        mid_left_pad = ((10, 0), (0, 0))
        mid_right_pad = ((0, 10), (0, 0))

        image_up = os.path.join(IMAGE_RESOURCES_DIR, f'up.png')
        image_down = os.path.join(IMAGE_RESOURCES_DIR, f'down.png')
        image_left = os.path.join(IMAGE_RESOURCES_DIR, f'left.png')
        image_right = os.path.join(IMAGE_RESOURCES_DIR, f'right.png')
        image_not_found = os.path.join(IMAGE_RESOURCES_DIR, f'image-not-found.png')
        image_size = (55, 55)
        panel_settings = {'disabled': True, 'image_size': image_size}
        tab_image_pad = ((149, 0), (27, 0))

        gui_title_layer = [
            sg.Button('Connect', size=(20, 1), pad=title_pad, key='button_drone', metadata={'function': 'connect'}),
            sg.Column(
                [[sg.Text('Battery:', size=(10, 1), pad=title_pad)],
                 [sg.Text('N/A', pad=title_pad, size=(20, 1), key='text_battery')]]),
            sg.Column(
                [[sg.Text('Wi-fi:', size=(10, 1), pad=title_pad)],
                 [sg.Text('N/A', pad=title_pad, size=(20, 1), key='text_wifi')]]),
            sg.Button('Update', size=(20, 1), pad=title_pad, disabled=True, key='button_update_title'),
            sg.Button('Exit', size=(20, 1), pad=title_pad, key='button_exit', metadata={'connected': False}),
        ]

        left_control_panel = [
            [sg.Button(image_filename=image_up, pad=mid_top_pad, key='button_left_up', **panel_settings)],
            [sg.Button(image_filename=image_left, pad=mid_left_pad, key='button_left_left', **panel_settings),
             sg.Button(image_filename=image_right, pad=mid_right_pad, key='button_left_right', **panel_settings)],
            [sg.Button(image_filename=image_down, pad=mid_bot_pad, key='button_left_down', **panel_settings)],
        ]
        right_control_panel = [
            [sg.Button(image_filename=image_up, pad=mid_top_pad, key='button_right_up', **panel_settings)],
            [sg.Button(image_filename=image_left, pad=mid_left_pad, key='button_right_left', **panel_settings),
             sg.Button(image_filename=image_right, pad=mid_right_pad, key='button_right_right', **panel_settings)],
            [sg.Button(image_filename=image_down, pad=mid_bot_pad, key='button_right_down', **panel_settings)],
        ]

        tab_manual = [
            [sg.Button('Takeoff', size=(20, 1), pad=simple_control_pad, disabled=True, key='button_takeoff'),
             sg.Button('Land', size=(20, 1), pad=simple_control_pad, disabled=True, key='button_land'),
             sg.Button('Speech', size=(20, 1), pad=simple_control_pad, disabled=True, key='button_speech_toggle')],
            [sg.Column(left_control_panel, pad=(0, 0)),
             sg.Image(filename=image_not_found, size=(self.video_width, self.video_height), key='image_manual'),
             sg.Column(right_control_panel, pad=(0, 0))]
        ]
        tab_auto = [
            [sg.Image(filename=image_not_found, pad=tab_image_pad, key='image_auto')]
        ]
        tab_gesture = [
            [sg.Image(filename=image_not_found, pad=tab_image_pad, key='image_gesture')]
        ]

        tabgroup_layer = [
            sg.TabGroup([
                [sg.Tab('Manual', tab_manual),
                 sg.Tab('Auto', tab_auto),
                 sg.Tab('Gesture', tab_gesture)]
            ], key='tabgroup_run_mode'),
            sg.Multiline(size=(30, 20), pad=(0, 0), disabled=True, autoscroll=False, key='multiline_state')
        ]

        log_layer = [
            sg.Multiline(size=(152, 10), disabled=True, autoscroll=True, key='multiline_log')
        ]

        self.layout = [
            gui_title_layer,
            tabgroup_layer,
            log_layer
        ]
        return

    def create_window(self):
        self.window = sg.Window('Window Title', self.layout, size=(self.screen_width, self.screen_height),
                                location=(0, 0), return_keyboard_events=True, resizable=True, finalize=True)
        self.color_connected = (self.window.ButtonColor[0], self.window.ButtonColor[1])
        self.color_disconnected = (self.window.ButtonColor[1], self.window.ButtonColor[0])

        for direction in self.button_direction_list:
            for side in ['left', 'right']:
                button_key = f'button_{side}_{direction}'
                button_elem = self.window[button_key]
                button_elem.update(disabled=True)

        for mode_type in self.run_mode_list:
            image_key = f'image_{mode_type}'
            image_elem = self.window[image_key]
            image_fname = image_elem.Filename
            image_frame = cv2.imread(image_fname)
            resized_frame = cv2.resize(image_frame, dsize=(self.video_width, self.video_height))
            frame_bytes = cv2.imencode('.png', resized_frame)[1].tobytes()
            image_elem.update(data=frame_bytes)
        return

    def update_battery_wifi(self):
        battery = self.drone.get_battery()
        wifi_snr = self.drone.get_wifi()

        text_battery = self.window['text_battery']
        text_wifi = self.window['text_wifi']

        text_battery.update(battery)
        text_wifi.update(wifi_snr)
        return

    def update(self, source, update_message):
        message_type = update_message['type']
        message_value = update_message['value']

        if isinstance(source, TelloDrone):
            if message_type == 'connect' and message_value:
                button_drone = self.window['button_drone']
                # button_drone.update(disabled=False)
                # button_drone.update('Panic')
                # button_drone.metadata['function'] = 'Panic'
                #
                # button_update_title = self.window['button_update_title']
                # button_takeoff = self.window['button_takeoff']
                # button_land = self.window['button_land']
                #
                # button_update_title.update(disabled=False)
                # button_takeoff.update(disabled=False)
                # button_land.update(disabled=False)
                #
                # for direction in self.button_direction_list:
                #     for side in ['left', 'right']:
                #         button_key = f'button_{side}_{direction}'
                #         button_elem = self.window[button_key]
                #         button_elem.update(disabled=False)
                #
                # update_thread = threading.Thread(target=self.update_battery_wifi, daemon=True)
                # update_thread.start()
        return

    def run_gui(self):
        button_function_dict = {
            'button_left_up': self.action_left_up,
            'button_left_down': self.action_left_down,
            'button_left_right': self.action_left_right,
            'button_left_left': self.action_left_left,

            'button_right_up': self.action_right_up,
            'button_right_down': self.action_right_down,
            'button_right_right': self.action_right_right,
            'button_right_left': self.action_right_left,

            'button_drone': self.action_drone,  # acts as the panic button
            'button_update_title': self.action_update_title,
            'button_takeoff': self.action_takeoff,
            'button_land': self.action_land,
            'button_speech_toggle': self.action_speech_toggle
        }

        key_func_dict = {
            'w': self.action_left_up,
            's': self.action_left_down,
            'd': self.action_left_right,
            'a': self.action_left_left,

            'Right:39': self.action_right_up,
            'Left:37': self.action_right_down,
            'Down:40': self.action_right_right,
            'Up:38': self.action_right_left,

            'p': self.action_drone,  # acts as the panic button
            'u': self.action_update_title,
            't': self.action_takeoff,
            'l': self.action_land,
            'r': self.action_speech_toggle
        }
        # Event Loop to process "events" and get the "values" of the inputs
        self.run_mode = 'Manual'
        while self.run_mode:
            event, values = self.window.read(timeout=10)
            if event in [None, 'button_exit']:  # if user closes window or clicks cancel
                self.run_mode = None
            elif event in button_function_dict.keys():
                button_func = button_function_dict[event]
                button_func(event=event, values=values)
            elif event in key_func_dict.keys():
                key_func = key_func_dict[event]
                key_func(event=event, values=values)
            elif event == '__TIMEOUT__':
                self.action_timeout(event=event, values=values)
        return

    def destroy(self):
        self.window.close()
        self.drone.cleanup()
        self.speech_text.stop_listener()
        return

    def action_timeout(self, **kwargs):
        if 'values' not in kwargs:
            return

        last_frame = None
        last_state = None

        self.run_mode = kwargs['values']['tabgroup_run_mode']
        if self.run_mode == 'Manual':
            last_frame = self.drone.get_last_frame()
            last_state = self.drone.get_last_state()

        if last_state is not None:
            state_elem = self.window['multiline_state']
            state_elem.update(value=f'', append=False)
            for each_key, each_val in last_state.items():
                state_elem.update(value=f'{each_key}: {each_val}\n', append=True)

        if last_frame is not None:
            image_elem = self.window[f'image_{self.run_mode.lower()}']
            resized_frame = cv2.resize(last_frame, dsize=(self.video_width, self.video_height))
            frame_bytes = cv2.imencode('.png', resized_frame)[1].tobytes()
            image_elem.update(data=frame_bytes)
        return

    def action_left_up(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to move forward\n', append=True)
        move_args = (0, self.speed, 0, 0)
        response = self.drone.set_rc(*move_args)
        log_elem.update(value=f'Move forward: {response}\n', append=True)
        return

    def action_left_down(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to move back\n', append=True)
        move_args = (0, -1 * self.speed, 0, 0)
        response = self.drone.set_rc(*move_args)
        log_elem.update(value=f'Move back: {response}\n', append=True)
        return

    def action_left_right(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to rotate clockwise\n', append=True)
        move_args = (0, 0, 0, -1 * self.speed)
        response = self.drone.set_rc(*move_args)
        log_elem.update(value=f'Rotate clockwise: {response}\n', append=True)
        return

    def action_left_left(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to rotate counter clockwise\n', append=True)
        move_args = (0, 0, 0, self.speed)
        response = self.drone.set_rc(*move_args)
        log_elem.update(value=f'Rotate counter clockwise: {response}\n', append=True)
        return

    def action_right_up(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to move up\n', append=True)
        move_args = (0, 0, self.speed, 0)
        response = self.drone.set_rc(*move_args)
        log_elem.update(value=f'Move up: {response}\n', append=True)
        return

    def action_right_down(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to move down\n', append=True)
        move_args = (0, 0, -1 * self.speed, 0)
        response = self.drone.set_rc(*move_args)
        log_elem.update(value=f'Move down: {response}\n', append=True)
        return

    def action_right_right(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to move left\n', append=True)
        move_args = (self.speed, 0, 0, 0)
        response = self.drone.set_rc(*move_args)
        log_elem.update(value=f'Move right: {response}\n', append=True)
        return

    def action_right_left(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to move right\n', append=True)
        move_args = (-1 * self.speed, 0, 0, 0)
        response = self.drone.set_rc(*move_args)
        log_elem.update(value=f'Move left: {response}\n', append=True)
        return

    def action_drone(self, **kwargs):
        button_drone = self.window['button_drone']
        drone_function = button_drone.metadata['function']
        if drone_function == 'connect':
            log_elem = self.window['multiline_log']
            log_elem.update(value=f'Attempting to connect to drone\n', append=True)
            log_elem.update(value=f'This may take some time...\n', append=True)
            button_drone.update(disabled=True)
            response = self.drone.connect()
            button_drone.update(disabled=False)
            log_elem.update(value=f'Connected: {response}\n', append=True)

            button_drone.update('Panic')
            button_drone.metadata['function'] = 'Panic'

            button_update_title = self.window['button_update_title']
            button_takeoff = self.window['button_takeoff']
            button_land = self.window['button_land']

            button_update_title.update(disabled=False)
            button_takeoff.update(disabled=False)
            button_land.update(disabled=False)

            for direction in self.button_direction_list:
                for side in ['left', 'right']:
                    button_key = f'button_{side}_{direction}'
                    button_elem = self.window[button_key]
                    button_elem.update(disabled=False)

            self.update_battery_wifi()
        elif drone_function == 'panic':
            log_elem = self.window['multiline_log']
            log_elem.update(value=f'PANICKING!\n', append=True)
            button_drone.update(disabled=True)
            response = self.drone.control_emergency()
            button_drone.update(disabled=False)
            log_elem.update(value=f'Panic: {response}\n', append=True)
        return

    def action_update_title(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Updating battery and wifi levels\n', append=True)
        self.update_battery_wifi()
        return

    def action_takeoff(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to takeoff\n', append=True)
        response = self.drone.control_takeoff()
        log_elem.update(value=f'Takeoff: {response}\n', append=True)
        return

    def action_land(self, **kwargs):
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Attempting to land\n', append=True)
        response = self.drone.control_land()
        log_elem.update(value=f'Land: {response}\n', append=True)
        return

    def action_speech_toggle(self, **kwargs):
        """
        todo

        :param kwargs:
        :return:
        """
        log_elem = self.window['multiline_log']
        log_elem.update(value=f'Speech recognition is \n', append=True)
        return


def main(main_args):
    title = 'Drone Gui'
    send_delay = main_args.get('send_delay', 0.1)
    scan_delay = main_args.get('scan_delay', 0.1)
    #############################
    tello_drone = TelloDrone(adapter_name='Wi-Fi', receive_timeout=4.0)
    tello_drone.NETWORK_SCAN_DELAY = scan_delay
    tello_drone.SEND_DELAY = send_delay
    #############################
    auto_control = AutoControl(sub_list=[tello_drone])
    gesture_control = GestureControl(sub_list=[tello_drone])
    speech_text = Speech2Text()
    #############################
    simple_gui = ControlGui(title=title, drone=tello_drone,
                            auto_control=auto_control, gesture_control=gesture_control, speech_translator=speech_text)
    simple_gui.run_gui()
    simple_gui.destroy()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')
    parser.add_argument('--send_delay', type=float, default=1,
                        help='')
    parser.add_argument('--scan_delay', type=float, default=1,
                        help='')

    args = parser.parse_args()
    main(vars(args))

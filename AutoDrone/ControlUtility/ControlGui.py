"""
@title
@description
"""
import argparse

import PySimpleGUI as sg


class ControlGui:

    def __init__(self, title: str, theme: str = 'DarkAmber'):
        self.theme = None
        self.layout = None
        self.window = None
        self.title = title

        self.set_theme(theme)
        self.set_layout()
        self.create_window()
        return

    def set_theme(self, theme: str = 'DarkAmber'):
        self.theme = theme
        sg.theme(self.theme)  # Add a touch of color
        return

    def set_layout(self):
        """
        All the stuff inside your window.

        :return:
        """
        self.layout = [
            [sg.Text('Some text on Row 1')],
            [sg.Text('Enter something on Row 2'), sg.InputText()],
            [sg.Button('Ok'), sg.Button('Cancel')]
        ]
        return

    def create_window(self):
        # Create the Window
        self.window = sg.Window('Window Title', self.layout)
        return

    def listen(self):
        # Event Loop to process "events" and get the "values" of the inputs
        while True:
            event, values = self.window.read()
            if event in (None, 'Cancel'):  # if user closes window or clicks cancel
                break
            print('You entered ', values[0])
        return

    def destroy(self):
        self.window.close()
        return


def main(main_args):
    title = 'Drone Gui'
    theme = 'DarkAmber'
    #############################
    control_gui = ControlGui(title=title, theme=theme)
    control_gui.listen()
    control_gui.destroy()
    return


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='')

    args = parser.parse_args()
    main(vars(args))

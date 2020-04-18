"""
@title
@description
"""
import argparse

import PySimpleGUI as sg
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from numpy.random import rand


# ------------------------------- MATPLOTLIB CODE HERE -------------------------------
def draw_figure(canvas, figure):
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side='top', fill='both', expand=1)
    return figure_canvas_agg


# -------------------------------------------------------------------------------------


class ControlGui:
    FULL_THEME_LIST = sg.theme_list()

    def __init__(self, title: str, theme: str = 'DarkAmber'):
        self.layout = None
        self.window = None
        self.theme = None
        self.title = title

        self.figure_height, self.figure_width = 640, 480
        self.figure_dims = (self.figure_width, self.figure_width)

        self.set_theme(theme)
        self.set_layout()
        self.create_window()
        return

    def set_theme(self, theme: str = 'DarkAmber'):
        if theme in self.FULL_THEME_LIST:
            sg.theme(theme)  # Add a touch of color
            self.theme = theme
            sg.change_look_and_feel(self.theme)
        else:
            sg.theme(self.FULL_THEME_LIST[0])  # Add a touch of color
        return

    def set_layout(self):
        """
        All the stuff inside your window.

        :return:
        """
        self.layout = [
            [sg.Text('Row 1', size=(10, 1), key='text_row1')],
            [sg.Text('Row 2', size=(10, 1), key='text_row2'),
             sg.InputText(size=(10, 1), focus=True, key='inputtext_row2', enable_events=False),
             sg.Button('Row2 button', size=(10, 1), key='button_row2')],
            [sg.Text('Theme', size=(10, 1), key='text_theme'),
             sg.Combo(self.FULL_THEME_LIST, size=(10, 1), key='combo_theme', default_value=self.theme),
             sg.Button('Theme button', size=(10, 1), key='button_theme')],
            [sg.Canvas(size=self.figure_dims, key='canvas')],
            [sg.Cancel(size=(10, 1), key='button_cancel')],
        ]
        return

    def create_window(self):
        # Create the Window
        self.window = sg.Window('Window Title', self.layout, return_keyboard_events=True, finalize=True)
        return

    def listen(self):
        canvas_elem = self.window['canvas']
        canvas = canvas_elem.TKCanvas

        # draw the initial scatter plot
        fig, ax = plt.subplots()
        ax.grid(True)
        fig_agg = draw_figure(canvas, fig)

        # Event Loop to process "events" and get the "values" of the inputs
        while True:
            event, values = self.window.read(timeout=10)
            if event in (None, 'button_cancel'):  # if user closes window or clicks cancel
                break
            elif event == 'button_theme':
                combo_theme_element = self.window['combo_theme']
                theme_name = values['combo_theme']
                if theme_name in self.FULL_THEME_LIST:
                    print(f'set theme: {theme_name}')
                else:
                    print(f'invalid theme name: {theme_name}')
                    combo_theme_element.update(self.theme)
            elif event == 'inputtext_row2':
                input_text = values['inputtext_row2']
                print(input_text)
            elif event == 'button_row2':
                dropdown_element = self.window['inputtext_row2']
                input_text = values['inputtext_row2']
                if len(input_text) > 0:
                    print(f'clearing text from inputtext_row2 element: {input_text}')
                    dropdown_element.update('')
                else:
                    print(f'no text in input textbox')
            elif event == '__TIMEOUT__':
                pass
            else:
                print(f'event: {event}\nvalues: {values}')
                pass

            ax.cla()
            ax.grid(True)
            for color in ['red', 'green', 'blue']:
                n = 50
                x, y = rand(2, n)
                scale = 200.0 * rand(n)
                ax.scatter(x, y, c=color, s=scale, label=color, alpha=0.3, edgecolors='none')
            # ax.legend()
            fig_agg.draw()
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

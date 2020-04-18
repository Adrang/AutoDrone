import PySimpleGUI as sg
import cv2 as cv2
from matplotlib import style


def main():
    style.use('ggplot')
    window_title = 'AutoDrone'
    sg.ChangeLookAndFeel('LightGreen')

    # define the window layout
    layout = [
        [sg.Text('OpenCV Demo', size=(40, 1), justification='center', font='Helvetica 20')],
        [sg.Image(filename='', key='image')],
        [sg.Cancel('Exit', size=(10, 1), font='Helvetica 14')]
    ]

    # create the window and show it without the plot
    window = sg.Window(window_title, layout=layout, location=(0, 0))
    window.Finalize()

    # locate the elements we'll be updating. Does the search only 1 time
    image_elem = window['image']

    # ---===--- Event LOOP Read and display frames, operate the GUI --- #
    gui_running = True
    cap = cv2.VideoCapture(0)
    while gui_running:
        event, values = window.read(timeout=0)

        if event in ('Exit', None):
            gui_running = False
        else:
            ret, frame = cap.read()
            if ret:
                encode_success, encoded_image = cv2.imencode('.png', frame)
                if encode_success:
                    image_bytes = encoded_image.tobytes()
                    image_elem.Update(data=image_bytes)
            else:
                gui_running = False
    return


if __name__ == '__main__':
    main()

#
# Tello Python3 Control Demo 
#
# http://www.ryzerobotics.com/
#
# 1/1/2018

import socket
import threading
import cv2 as cv2

host = ''
port = 9000
video_port = 11111

tello_address = ('192.168.10.1', 8889)
locaddr = (host, port)
# vid_addr = (host, video_port)

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(locaddr)

# vid_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# vid_sock.bind(vid_addr)


# def vid_recv():
#     count = 0
#     while True:
#         try:
#             data, server = vid_sock.recvfrom(1518)
#
#             # frame_read = tello.get_frame_read()
#             #
#             # frame = frame_read.frame
#             # gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
#             # cv2.imshow("Video", frame)
#             # faces = face_cascade.detectMultiScale(gray, 1.3, 5)
#         except Exception as e:
#             print(f'{e}')
#             break


def recv():
    count = 0
    while True:
        try:
            data, server = sock.recvfrom(1518)
            print(data.decode(encoding="utf-8"))
        except Exception as e:
            print(f'{e}')
            break


# recvThread = threading.Thread(target=recv)
# recvThread.start()
#
# vidThread = threading.Thread(target=vid_recv)
# vidThread.start()

msg = 'command'.encode(encoding="utf-8")
sock.sendto(msg, tello_address)
data, server = sock.recvfrom(1518)
print(data)

# msg = 'streamoff'.encode(encoding="utf-8")
# sock.sendto(msg, tello_address)

while True:

    try:
        msg = input("enter msg: ")

        if not msg:
            break

        if 'end' in msg:
            print('...')
            sock.close()
            break

        # Send data
        msg = msg.encode(encoding="utf-8")
        sent = sock.sendto(msg, tello_address)
    except KeyboardInterrupt:
        print('\n . . .\n')
        sock.close()
        break

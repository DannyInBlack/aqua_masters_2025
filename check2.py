# camera_tcp_receiver.py
import cv2
import socket
import struct
import pickle

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect(('192.168.152.250', 8485))  # Use your Pi's IP
data = b""
payload_size = struct.calcsize(">L")

while True:
    while len(data) < payload_size:
        data += client_socket.recv(4096)

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4096)

    frame_data = data[:msg_size]
    data = data[msg_size:]

    frame = pickle.loads(frame_data)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)

    if frame is not None:
        cv2.imshow('ZED (UVC) Camera Stream', frame)

    if cv2.waitKey(1) == 27:
        break

client_socket.close()
cv2.destroyAllWindows()
import math
import serial
import zmq
import threading
import time
import cv2
import socket
import struct
import pickle


class VideoFeed:
    def __init__(self):
        while True:
            try:
                self.cap = cv2.VideoCapture(0)  # Replace 0 with correct index if needed
                print("CAMERA SOCKET")
                server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                server_socket.bind(('0.0.0.0', 8486))
                server_socket.listen(1)
                print("Waiting for connection...")
                self.conn, self.addr = server_socket.accept()
                print("Connected by", self.addr)
                break
            except:
                print("Couldn't connect to camera, trying again in 1 second...")
                time.sleep(1)


    def receive(self):
        while True:
            ret, frame = self.cap.read()
            if not ret:
                continue

            _, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEGXL_QUALITY), 80])
            data = pickle.dumps(buffer)
            size = len(data)

            try:
                self.conn.sendall(struct.pack(">L", size) + data)
            except Exception as e:
                print(e)
                break


        self.cap.release()
        self.conn.close()
        self.__init__()


class Controls:
    def __init__(self, pc_ip = "192.168.1.2"):
        while True:
            try:
                context = zmq.Context()
                print("Connecting to control socket....")
                self.control_socket = context.socket(zmq.SUB)
                self.control_socket.connect(f'tcp://{pc_ip}:5556')  # Surface Laptop IP
                self.control_socket.setsockopt(zmq.SUBSCRIBE, b"")
                print("Connected to control socket!")
                break
            except Exception as e:
                print("Failed to connect to PC: ", end='')
                print(e)
                print("Trying again in 1 second...")
                time.sleep(1)

        while True:
            try:
                self.esp = serial.Serial('/dev/ttyS0', 115200, timeout=1)
                break
            except Exception as e:
                print("Failed to connect to serial port: ", end='')
                print(e)
                print("Trying again in 1 second...")
                time.sleep(1)


    # convert values from -1 to 1 into 1000 to 2000
    def convert_to_int(self, value):
        return int(((value * -1 + 1) / 2) * 1000 + 1000)

    def get_magnitude(self, x, y):
        max_magnitude = math.sqrt(2)

        # Normalize magnitude to range -1 to 1
        x /= max_magnitude
        y /= max_magnitude

        # Combine tilts: Up/Down (y), Left/Right (x)
        thrusters = [
            -x + y,  # Front-left
            x + y,  # Front-right
            -x - y,  # Rear-left
            x - y  # Rear-right
        ]

        # Do not exceed limits of motor activation
        return [min(max(i, -1), 1) for i in thrusters]

    def map_joystick_to_thrusters(self, x, y, tilt, power, pov):
        # [1, 4, 5, 8]
        float_thrusters = [1, 0, 0, 1] # 1 and 8 are unidirectional (so is 2, but we don't use it) (1 = Off)
        # [2, 3, 6, 7]
        direction_thrusters = [0, 0, 0, 0]

        if abs(x) < 0.3:
            x = 0
        if abs(y) < 0.1:
            y = 0

        # float_thrusters = get_magnitude(x, y)

        # Handle movement forward or backward
        direction_thrusters = [0, 0, y, y]

        # Handle rotation right or left
        if x > 0 or x < 0:
            direction_thrusters = [0, -x, x, 0]


        # Handle floating movement (POV up/down)
        if power > 0:
            float_thrusters = [1, power, power, 1]
        else:
            float_thrusters = [power, power, power, power]

        motors = [
            float_thrusters[0],
            direction_thrusters[0],
            direction_thrusters[1],
            float_thrusters[1],
            float_thrusters[2],
            direction_thrusters[2],
            direction_thrusters[3],
            float_thrusters[3]
        ]

        for i in range(len(motors)):
            motors[i] = self.convert_to_int(motors[i])

        motors[5] = min(motors[5], 1800)
        motors[5] = max(motors[5], 1200)

        return motors


    def receive_joystick(self):
        while True:
            try:
                joystick_data = self.control_socket.recv_json()
                # print("Received Joystick Data:", joystick_data)
                if joystick_data:
                    thruster_values = self.map_joystick_to_thrusters(
                        joystick_data['x'],
                        joystick_data['y'],
                        joystick_data['tilt'],
                        joystick_data['power'],
                        joystick_data['pov'],
                    )

                    # Send thruster values to ESP32 over UART
                    thruster_command = " ".join(map(str, thruster_values)) + "\n"
                    self.esp.write(thruster_command.encode())
                    print("Sent Thruster Data:", thruster_command)
            except Exception as e:
                print("Error receiving joystick data:", e)



controls = Controls()
threading.Thread(target=controls.receive_joystick, daemon=False).start()
video_feed = VideoFeed()
threading.Thread(target=video_feed.receive, daemon=True).start()

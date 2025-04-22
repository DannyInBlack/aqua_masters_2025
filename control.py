import threading
import serial
import zmq
import cv2
import socket
import struct
import pickle

context = zmq.Context()
pc_ip = "192.168.72.211"

cap = cv2.VideoCapture(0)  # Replace 0 with correct index if needed

print("CAMERA SOCKET")
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind(('0.0.0.0', 8486))
server_socket.listen(1)
print("Waiting for connection...")
conn, addr = server_socket.accept()
print("Connected by", addr)


print("Control SOCKET")
control_socket = context.socket(zmq.SUB)
control_socket.connect(f'tcp://{pc_ip}:5556')  # Surface Laptop IP
control_socket.setsockopt(zmq.SUBSCRIBE, b"")
ser = serial.Serial('/dev/ttyS0', 115200, timeout=1)

# convert values from -1 to 1 into 1000 to 2000
def convert_to_int(value):
    return int(((value * -1 + 1) / 2) * 1000 + 1000)

def map_joystick_to_thrusters(x, y, tilt, power, pov):
	dead_zone = 0.1
	float_thrusters = [1, 0, 0, 1]
	direction_thrusters = [0, 0, 0, 0]
	# if abs(x) < dead_zone:
	# 	x = 0
	# if abs(y) < dead_zone:
	# 	y = 0
	if abs(tilt) < 0.3:
		tilt = 0
	if abs(power) < dead_zone:
		power = 0

    # # Calculate magnitude
    # max_magnitude = math.sqrt(2)
    # magnitude = math.sqrt(x ** 2 + y ** 2)
    #
    # # Normalize magnitude to range -1 to 1
    #
    # x /= max_magnitude
    # y /= max_magnitude
    #
    # # Combine tilts: Up/Down (y), Left/Right (x)
    # float_thrusters = [
    #     -x + y,  # Front-left
    #     x + y,  # Front-right
    #     -x - y,  # Rear-left
    #     x - y  # Rear-right
    # ]
    #
    # float_thrusters = [min(max(i, -1), 1) for i in float_thrusters]

    # Handle movement forward or backward
	direction_thrusters = [0, 0, -power, -power]

	if tilt > 0 or tilt < 0:
        # Handle movement forward or backward
		direction_thrusters = [-tilt, tilt, tilt, tilt]

    # Handle floating movement (POV up/down)
	if pov == 1:
		float_thrusters = [1, 1, 1, 1]  # Move up
	elif pov == -1:
		float_thrusters = [-1, -1, -1, -1]  # Move down

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
		motors[i] = convert_to_int(motors[i])

	motors[5] = min(motors[5], 1800)
	motors[5] = max(motors[5], 1200)

	return motors


def receive_joystick():
	# print("receive joystick fun")
	while True:
		try:
			joystick_data = control_socket.recv_json()
			# print("Received Joystick Data:", joystick_data)
			if joystick_data:
				thruster_values = map_joystick_to_thrusters(
					joystick_data['x'],
					joystick_data['y'],
					joystick_data['tilt'],
					joystick_data['power'],
					joystick_data['pov'],
				)

				# Send thruster values to ESP32 over UART
				thruster_command = " ".join(map(str, thruster_values)) + "\n"
				ser.write(thruster_command.encode())
				print("Sent Thruster Data:", thruster_command)
		except Exception as e:
			print("Error receiving joystick data:", e)

threading.Thread(target=receive_joystick, daemon=True).start()

while True:
	# receive_joystick()

	ret, frame = cap.read()
	if not ret:
		continue

	_, buffer = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEGXL_QUALITY), 80])
	data = pickle.dumps(buffer)
	size = len(data)

	try:
		conn.sendall(struct.pack(">L", size) + data)
	except BrokenPipeError:
		print("Client disconnected")
		break

cap.release()
conn.close()

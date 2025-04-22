# Code used to send and receive data from the Pi - currently up to date

import tkinter as tk
import random
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image, ImageTk
import zmq
import pygame
import cv2
import socket
import struct
import pickle

# Raspberry Pi IP
RASPBERRY_PI_IP = "192.168.72.250"

# Define window size
WINDOW_WIDTH = 1920
WINDOW_HEIGHT = 1080
VIDEO_WIDTH, VIDEO_HEIGHT = 1400, 400  # Camera feed size
NO_CONN = True
# CONTROLS = True
BAR_HEIGHT = 165

# Initialize Tkinter window
root = tk.Tk()
root.title("ROV Control Interface")
root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

# Initialize Pygame for joystick control
pygame.init()
pygame.joystick.init()

# socket used for video data
context = zmq.Context()

if not NO_CONN:
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((RASPBERRY_PI_IP, 8486))  # Use your Pi's IP
    data = b""
    payload_size = struct.calcsize(">L")

# Initialize ZeroMQ socket for joystick data
control_socket = context.socket(zmq.PUB)
control_socket.bind("tcp://*:5556")  # Send joystick data from this port

# Detect joystick
if pygame.joystick.get_count() > 0:
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"Joystick Connected: {joystick.get_name()}")
else:
    joystick = None
    print("No Joystick Detected!")

# Create Frames
left_frame = tk.Frame(root, padx=20, pady=20, bg="lightblue")
left_frame.grid(row=1, column=0, sticky="n")

video_frame = tk.Frame(root)
video_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

right_frame = tk.Frame(root, padx=20, pady=20, bg="lightgray")
right_frame.grid(row=1, column=1, sticky="n")

# Temperature Graph Setup
fig, ax = plt.subplots(figsize=(3, 2))  # Reduce size
ax.set_title("Temperature Trends")
ax.set_xlabel("Time")
ax.set_ylabel("Temperature (°C)")
temp_canvas = FigureCanvasTkAgg(fig, master=left_frame)
temp_canvas.get_tk_widget().pack()
temp_data = [[]]  # Store temperature data

# Updates sensor graph GUI
def update_graph():
    ax.clear()
    ax.plot(temp_data[0][-20:], label="Sensor 1", color='red')
    ax.legend()
    temp_canvas.draw()


# Thruster Power Bar Indicator
thruster_label = tk.Label(right_frame, text="Thruster Power", bg="lightgray")
thruster_label.grid(row=0, column=0, padx=10)
thruster_bar = tk.Canvas(right_frame, width=20, height=BAR_HEIGHT, bg="white")
thruster_bar.grid(row=1, column=0, pady=(10, 0), padx=10)


# Updates thruster GUI
def update_thruster(power):
    thruster_bar.delete("all")
    thruster_bar.create_rectangle(0, BAR_HEIGHT - power * BAR_HEIGHT, 20, BAR_HEIGHT, fill="green")


# Battery Monitoring
battery_label = tk.Label(right_frame, text="Battery Level", bg="lightgray")
battery_label.grid(row=0, column=1, padx=10)
battery_bar = tk.Canvas(right_frame, width=20, height=BAR_HEIGHT, bg="white")
battery_bar.grid(row=1, column=1, pady=(10, 0), padx=10)


# Updates battery GUI
def update_battery(level):
    battery_bar.delete("all")
    battery_bar.create_rectangle(0, 0, 20, level, fill="blue")


# Joystick Movement Graph Setup
fig_joystick, ax_joystick = plt.subplots(figsize=(3, 2))  # Reduce size
ax_joystick.set_xlim(-100, 100)
ax_joystick.set_ylim(-100, 100)
ax_joystick.set_title("Joystick Movement")
joystick_canvas = FigureCanvasTkAgg(fig_joystick, master=right_frame)
joystick_canvas.get_tk_widget().grid(row=0, column=2, rowspan=2, padx=10)
joystick_point, = ax_joystick.plot([0], [0], "ro", markersize=8)


# Updates joystick graph GUI
def update_joystick_graph(x, y):
    joystick_point.set_xdata([x])  # Wrap x in a list
    joystick_point.set_ydata([y])  # Wrap y in a list
    ax_joystick.draw_artist(joystick_point)
    joystick_canvas.draw()

tilt_and_gripper = tk.Frame(right_frame)
tilt_and_gripper.grid(row=0, column=3, padx=10, rowspan=2)

# Tilting Controller (X-axis rotation)
tilt_label = tk.Label(tilt_and_gripper, text="Tilt Angle", bg="lightgray")
tilt_label.grid(column=0, row=0)
tilt_canvas = tk.Canvas(tilt_and_gripper, width=165, height=20, bg="white")
tilt_canvas.grid(column=0, row=1)


# Updates tilt GUI
def update_tilt(angle):
    tilt_canvas.delete("all")
    center_x = 165 / 2  # Center of the canvas
    pos_x = int(center_x + (angle * 165 / 2))  # Scale -1 to 1 range into canvas space
    tilt_canvas.create_line(center_x, 10, pos_x, 10, fill="orange", width=5)

# Gripper Status Box
gripper_label = tk.Label(tilt_and_gripper, text="Gripper Status", bg="lightgray")
gripper_label.grid(column=0, row=2)
gripper_canvas = tk.Canvas(tilt_and_gripper, width=50, height=50, bg="white")
gripper_canvas.grid(column=0, row=3)

def update_gripper(status):
    gripper_canvas.delete("all")
    color = "green" if status in ["open", "opening"] else "red"
    gripper_canvas.create_rectangle(0, 0, 50, 50, fill=color)


# Video feed frame
video_label = tk.Label(video_frame)
video_label.pack()

# Runs asynchronously to update
def receive_video_feed():
    """Run in a background thread to handle receiving video frames from the socket."""

    if NO_CONN:
        fakedata = np.random.randint(0, 255, size=(VIDEO_HEIGHT, VIDEO_WIDTH, 3), dtype=np.uint8)
        fakedata = ImageTk.PhotoImage(Image.fromarray(fakedata))
        video_label.config(image=fakedata)
        video_label.image = fakedata
        root.after(500, receive_video_feed)
        return

    global data
    # Ensure enough data is received for the packet size
    while len(data) < payload_size:
        data += client_socket.recv(4096)

    # Extract the payload size
    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack(">L", packed_msg_size)[0]

    # Receive the complete frame data
    while len(data) < msg_size:
        data += client_socket.recv(4096)

    # Deserialize and decode the frame
    frame_data = data[:msg_size]
    data = data[msg_size:]
    frame = pickle.loads(frame_data)
    frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
    frame = cv2.resize(frame, (VIDEO_WIDTH, VIDEO_HEIGHT))

    # Add the frame to the queue for processing in the main thread
    if frame is not None:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frame = ImageTk.PhotoImage(Image.fromarray(frame))
        video_label.config(image=frame)
        video_label.image = frame

    root.after(1, receive_video_feed)


# Data Update Function
def update_data():
    pygame.event.pump()
    sensor1 = round(random.uniform(20, 30), 1)
    # print(joystick.get_axis(3))
    x, y = round(joystick.get_axis(0), 2) * 100, round(joystick.get_axis(1) * -1, 2) * 100
    thruster_power = round(1 - (joystick.get_axis(3) + 1) / 2, 2)
    # battery_level = random.randint(0, 100)
    battery_level = 0
    # gripper_status = random.choice(["open", "closed", "opening", "closing"])
    gripper_status = "open" if joystick.get_button(0) else "closed"
    tilt_angle = round(joystick.get_axis(2), 2)

    # print(joystick.get_axis(3) * -1)

    joystick_data = {
        "x": round(joystick.get_axis(0), 2),  # Left/Right
        "y": round(joystick.get_axis(1), 2),  # Forward/Backward
        "tilt": round(joystick.get_axis(2), 2),  # Speed Control
        "power": round(joystick.get_axis(3) * -1, 2),  # Rotation
        "pov": joystick.get_hat(0)[1], # Float up or down
        "gripper": joystick.get_button(0) # Gripper open or closed
    }

    # if not NO_CONN:
        # Send data as JSON
    control_socket.send_json(joystick_data)

    temp_data[0].append(sensor1)
    update_graph()
    update_joystick_graph(x, y)
    update_thruster(thruster_power)
    update_battery(battery_level)
    update_gripper(gripper_status)
    update_tilt(tilt_angle)

    # with open(log_file, "a", newline="") as file:
    #     writer = csv.writer(file)
    #     writer.writerow([random.randint(0, 1000), sensor1, x, y, thruster_power, battery_level, tilt_angle])

    root.after(50, update_data)



# Start Updates
receive_video_feed()
update_data()
root.mainloop()


root.destroy()
client_socket.close()
cv2.destroyAllWindows()


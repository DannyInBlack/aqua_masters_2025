# Used for testing camera for issues - kept for reference

import zmq
import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
import threading
import pygame
import json

# Raspberry Pi IP
RASPBERRY_PI_IP = "192.168.152.250"

# Initialize ZeroMQ for video feed
context = zmq.Context()
video_socket = context.socket(zmq.SUB)
video_socket.connect(f"tcp://{RASPBERRY_PI_IP}:5555")
video_socket.setsockopt(zmq.SUBSCRIBE, b"")

# Initialize ZeroMQ for joystick data
control_socket = context.socket(zmq.PUB)
control_socket.bind("tcp://*:5556")  # Send joystick data from this port

# GUI setup
root = tk.Tk()
root.title("ROV Camera & Controller")

# Label for displaying camera feed
camera_label = tk.Label(root)
camera_label.pack()

latest_frame = None  # Store latest frame globally

# Function to receive and display camera feed
def receive_camera_feed():
    global latest_frame
    while True:
        try:
            frame_data = video_socket.recv()
            np_frame = np.frombuffer(frame_data, dtype=np.uint8)
            frame = cv2.imdecode(np_frame, cv2.IMREAD_COLOR)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            latest_frame = ImageTk.PhotoImage(Image.fromarray(frame))
        except Exception as e:
            print("Camera feed error:", e)

# Function to update GUI
def update_gui():
    if latest_frame:
        camera_label.config(image=latest_frame)
        camera_label.image = latest_frame
    root.after(30, update_gui)

# Start background threads
threading.Thread(target=receive_camera_feed, daemon=True).start()

# Start GUI loop
update_gui()
root.mainloop()
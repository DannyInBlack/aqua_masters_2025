# TODO: Finish implementing GUI and Control class (for refactoring)
import threading
import time
import tkinter as tk
from gripper_test import Gripper
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

class Control:
    def __init__(self):
        # detect joystick if connected
        self.joystick = None
        if pygame.joystick.get_count() != 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print("Joystick connected!")
        else:
            print("No joystick found, sticking to keyboard controls")
    
    def get_joystick_data(self):
        if self.joystick == None:
            return None
        
        x, y = (
            round(self.joystick.get_axis(0), 2),
            round(self.joystick.get_axis(1) * -1, 2),
        )
        
        pov = round(self.joystick.get_axis(3) * -1, 2)
        gripper = self.joystick.get_button(0)

        joystick_data = {
            "x": x,  # rotation right (+ve)/ left (-ve)
            "y": y,  # forward (+ve)/ backward (-ve) 
            "pov": pov,  # float down (+ve) or up (-ve)
            "gripper": gripper # gripper closed (0) or open (1)
        }

        return joystick_data
    
    def get_keyboard_data(self):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_UP] and not keys[pygame.K_DOWN]:
            y = 1.0
        elif not keys[pygame.K_UP] and keys[pygame.K_DOWN]:
            y = -1.0

        if keys[pygame.K_RIGHT] and not keys[pygame.K_LEFT]:
            x = 1.0
        elif not keys[pygame.K_RIGHT] and keys[pygame.K_LEFT]:
            x = -1.0

        

        x, y = (
            round(pygame.key.get_pressed())
        )

class GUI:
    def __init__(
            self, 
            window_width = 1920, 
            window_height = 1080,
            video = True,
            video_width = 720,
            video_height = 480,
            bar_height = 165,
            pi_ip = "192.168.1.3"
            ):
        self.window_width = window_width
        self.window_height = window_height
        self.video = video
        self.video_width = video_width,
        self.video_height = video_height,
        self.bar_height = bar_height
        self.pi_ip = pi_ip

        # Initialize Tkinter window
        self.root = tk.Tk()
        self.root.title("ROV Control Interface")
        self.root.geometry(f"{self.window_width}x{self.window_width}")

        # Initialize Pygame for joystick control
        pygame.init()

        # socket used for video data
        context = zmq.Context()

        if video:
            print("Initalizing video socket connection...")
            self.video_socket = context.socket(zmq.SUB)
            self.video_socket.setsockopt(zmq.LINGER, 0)
            self.video_socket.setsockopt(zmq.SNDHWM, 10000)
            self.video_socket.setsockopt(zmq.RCVHWM, 10000)
            self.video_socket.setsockopt(zmq.IMMEDIATE, 1)
            self.video_socket.setsockopt(zmq.RCVTIMEO, 1000)
            self.video_socket.setsockopt(zmq.SNDTIMEO, 1000)
            self.video_socket.connect(f'udp://{pi_ip}:5555')
            print("Connected to video socket!")

        # Initialize ZeroMQ socket for joystick data
        self.control_socket = context.socket(zmq.PUB)
        self.control_socket.bind("tcp://*:5556")  # Send joystick data from this port

        # Create Frames
        self.left_frame = tk.Frame(self.root, padx=20, pady=20, bg="lightblue")
        self.left_frame.grid(row=1, column=0, sticky="n")

        self.video_frame = tk.Frame(self.root)
        self.video_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10)

        self.right_frame = tk.Frame(self.root, padx=20, pady=20, bg="lightgray")
        self.right_frame.grid(row=1, column=1, sticky="n")


        # Temperature Graph Setup
        fig, self.ax = plt.subplots(figsize=(3, 2))  # Reduce size
        self.ax.set_title("Temperature Trends")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Temperature (°C)")
        self.temp_canvas = FigureCanvasTkAgg(fig, master=self.left_frame)
        self.temp_canvas.get_tk_widget().pack()
        self.temp_data = [[]]  # Store temperature data

        # Thruster Power Bar Indicator
        float_label = tk.Label(self.right_frame, text="Float", bg="lightgray")
        float_label.grid(row=0, column=2, padx=10)
        float_bar = tk.Canvas(self.right_frame, width=20, height=self.bar_height, bg="white")
        float_bar.grid(row=1, column=2, pady=(10, 0), padx=10)

        # Joystick Movement Graph Setup
        fig_joystick, ax_joystick = plt.subplots(figsize=(3, 2))  # Reduce size
        ax_joystick.set_xlim(-100, 100)
        ax_joystick.set_ylim(-100, 100)
        ax_joystick.set_title("Joystick Movement")
        joystick_canvas = FigureCanvasTkAgg(fig_joystick, master=self.right_frame)
        joystick_canvas.get_tk_widget().grid(row=0, column=3, rowspan=2, padx=10)
        (joystick_point,) = ax_joystick.plot([0], [0], "ro", markersize=8)

        tilt_and_gripper = tk.Frame(self.right_frame)
        tilt_and_gripper.grid(row=0, column=4, padx=10, rowspan=2)

        # Tilting Controller (X-axis rotation)
        tilt_label = tk.Label(tilt_and_gripper, text="Tilt Angle", bg="lightgray")
        tilt_label.grid(column=0, row=0)
        tilt_canvas = tk.Canvas(tilt_and_gripper, width=165, height=20, bg="white")
        tilt_canvas.grid(column=0, row=1)

        # Gripper Status Box
        gripper_label = tk.Label(tilt_and_gripper, text="Gripper Status", bg="lightgray")
        gripper_label.grid(column=0, row=2)
        gripper_canvas = tk.Canvas(tilt_and_gripper, width=50, height=50, bg="white")
        gripper_canvas.grid(column=0, row=3)

        # Video feed frame
        video_label = tk.Label(self.video_frame)
        video_label.pack()

    # Updates sensor graph GUI
    def update_graph(self):
        self.ax.clear()
        self.ax.plot(self.temp_data[0][-20:], label="Sensor 1", color="red")
        self.ax.legend()
        self.temp_canvas.draw()

    def update_float(self, level):
        self.float_bar.delete("all")
        self.float_bar.create_rectangle(
            0, self.BAR_HEIGHT / 2 - level * BAR_HEIGHT / 2, 20, BAR_HEIGHT / 2, fill="blue"
        )

    # Updates joystick graph GUI
    def update_joystick_graph(self, x, y):
        self.joystick_point.set_xdata([x])  # Wrap x in a list
        self.joystick_point.set_ydata([y])  # Wrap y in a list
        self.ax_joystick.draw_artist(self.joystick_point)
        self.joystick_canvas.draw()


    # Updates tilt GUI
    def update_tilt(self, angle):
        self.tilt_canvas.delete("all")
        center_x = 165 / 2  # Center of the canvas
        pos_x = int(center_x + (angle * 165 / 2))  # Scale -1 to 1 range into canvas space
        self.tilt_canvas.create_line(center_x, 10, pos_x, 10, fill="orange", width=5)


    def update_gripper(self, status):
        self.gripper_canvas.delete("all")
        color = "green" if status in ["open", "opening"] else "red"
        self.gripper_canvas.create_rectangle(0, 0, 50, 50, fill=color)


    def fake_frame(self):
        return ImageTk.PhotoImage(Image.fromarray(np.random.randint(0, 1, size=(self.video_height, self.video_width, 1), dtype=np.bool)))

    # Runs asynchronously to update
    def receive_video_feed(self):
        """Run in a background thread to handle receiving video frames from the socket."""
        while True:
            if not self.video:
                self.update_video(self.fake_frame())
                return

            frame = self.video_socket.recv()
            frame = cv2.imdecode(frame, cv2.IMREAD_COLOR)
            frame = cv2.resize(frame, (self.video_width, self.video_height))

            # Add the frame to the queue for processing in the main thread
            if frame is not None:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frame = ImageTk.PhotoImage(Image.fromarray(frame))
                self.update_video(frame)


    def update_gui(self):
        pass


        
def get_control_data():
    pygame.event.pump()
    sensor1 = round(random.uniform(20, 30), 1)
    x, y = (
        round(joystick.get_axis(0), 2) * 100,
        round(joystick.get_axis(1) * -1, 2) * 100,
    )
    

# Data Update Function
def update_data():
    pygame.event.pump()
    sensor1 = round(random.uniform(20, 30), 1)
    # print(joystick.get_axis(3))


    control_socket.send_json(joystick_data)

    temp_data[0].append(sensor1)
    update_graph()
    update_joystick_graph(x, y)
    # update_thruster(thruster_power)
    # update_battery(battery_level)
    update_gripper(gripper_status)
    update_tilt(tilt_angle)
    update_float(thruster_power)

    root.after(50, update_data)


if __name__ == "__main__":
    app = GUI()
    threading.Thread(target=update_data)
    app.root.mainloop()
    app.root.destroy()

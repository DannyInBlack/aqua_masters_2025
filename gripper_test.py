import time
import serial

class Gripper:
    def __init__(self, serial_port, gripper_state = "closed"):
        self.gripper_state = gripper_state
        self.failed = False
        self.serial_port = serial_port

        self.set_gripper_state(gripper_state)

        for trial in range(0, 3):
            try:
                self.arduino = serial.Serial(self.serial_port, 9600)
                print("Arduino connected")
                break
            except serial.SerialException as e:
                print(e)
                if trial < 2:
                    time.sleep(3)
                else:
                    self.failed = True
                    print("Failed to connect to gripper, proceeding...")

    def set_gripper_state(self, gripper_state):
        if self.failed:
            return
        while True:
            if self.gripper_state != gripper_state:
                if self.send_to_arduino(gripper_state):
                    print("Gripper state changed to " + gripper_state)
                    self.gripper_state = gripper_state
                    break
                else:
                    print("Couldn't change gripper state to " + gripper_state)
                    time.sleep(1)
            else:
                break

    def send_to_arduino(self, data):
        if self.failed:
            return
        if data == "closed" or data == "opened":
            try:
                self.arduino.write(data[0].encode())
                return True
            except Exception as e:
                print(e)
                return False
        else:
            print("Invalid input")
            return False

# Initialize the gripper with the port connected to arduino,
# and optionally, the starting gripper state
# gripper = Gripper("COM6")
# gripper.set_gripper_state("opened")

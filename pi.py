import zmq
import json
import time
import serial
import threading

# === ZeroMQ Setup ===
context = zmq.Context()

PC_IP = "192.168.178.250"

# CONTROL DATA: SUB socket to receive control inputs
control_socket = context.socket(zmq.SUB)
control_socket.connect(f'tcp://{PC_IP}:5556')  # Replace <PC_IP> with the client machine IP
control_socket.setsockopt(zmq.SUBSCRIBE, b"")

# === Serial Communication Setup ===
# Replace '/dev/ttyUSB0' with the device name for your ESP32 serial interface
serial_port = '/dev/ttyUSB0'
serial_baudrate = 115200

esp32_serial = serial.Serial(serial_port, serial_baudrate, timeout=1)


# === Functions ===
def send_commands_to_esp32():
    """Read control data and send it to the ESP32."""
    while True:
        try:
            # Receive control data from ZeroMQ
            message = control_socket.recv_json()
            print(f"Received control data: {message}")

            # Convert control data to JSON string
            control_data = json.dumps(message)

            # Send JSON data over serial to ESP32
            esp32_serial.write((control_data + "\n").encode('utf-8'))  # "\n" marks the end of the command
            time.sleep(0.05)  # Avoid flooding the serial connection
        except Exception as e:
            print(f"Error while sending commands: {e}")


# === Entry Point ===
if __name__ == "__main__":
    try:
        print("Raspberry Pi: Starting communication with ESP32...")
        time.sleep(2)  # Wait for the serial connection to stabilize
        threading.Thread(target=send_commands_to_esp32, daemon=True).start()

        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        if esp32_serial.is_open:
            esp32_serial.close()

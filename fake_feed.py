import random
import numpy as np
import cv2
from PIL import Image
video_filename = "fake_feed_output.avi"
fourcc = cv2.VideoWriter_fourcc(*"XVID")  # Codec
video_writer = cv2.VideoWriter(video_filename, fourcc, FPS, (VIDEO_WIDTH, VIDEO_HEIGHT))
frame_count = 0
TOTAL_FRAMES = 150
if frame_count >= TOTAL_FRAMES:
    # Stop video saving after generating enough frames
    video_writer.release()
    print(f"Video saved as {video_filename}")

fake_frame = np.random.randint(0, 256, (300, 400, 3), dtype="uint8")
video_writer.write(fake_frame)


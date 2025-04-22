# Used to scan for connected cameras - kept for reference

import cv2

def list_windows_cameras(max_index=5):
    print("Scanning for available cameras...")
    for i in range(max_index):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"✅ Camera available at index {i}")
            cap.release()
        else:
            print(f"❌ No camera found at index {i}")

list_windows_cameras()
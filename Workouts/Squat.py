import math
import os
import time
import cv2
import mediapipe as mp

# variables
squat_count = 0

knee_angle_threshold = 90  # degrees
knee_y = 0
shoulder_y = 0

def angle(a, b, c):
    """Angle at b (degrees) from three (x, y) points."""
    ba = (a[0] - b[0], a[1] - b[1])
    bc = (c[0] - b[0], c[1] - b[1])
    mag = math.hypot(*ba) * math.hypot(*bc)
    if mag == 0:
        return 0.0
    dot = ba[0] * bc[0] + ba[1] * bc[1]
    return math.degrees(math.acos(max(-1, min(1, dot / mag))))

def squat():
    # Initialize MediaPipe Pose
    pass

if __name__ == "__main__":
    squat()
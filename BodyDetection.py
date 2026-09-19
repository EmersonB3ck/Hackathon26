import os 
import sys
import cv2
import numpy as np
import mediapipe as mp
import matplotlib.pyplot as plt 
import time 
import threading
from flask import Flask, Response

BaseOptions           = mp.tasks.BaseOptions
# HandLandmarker is the main class for hand tracking in mediapipe tasks 
PoseLandmarker        = mp.tasks.vision.PoseLandmarker
# HandLandmarkerOptions is used to specify options for the hand landmarker, such as the model file and running mode.
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
# VisionRunningMode is used to specify the running mode for the hand landmarker, such as video or image mode.
VisionRunningMode     = mp.tasks.vision.RunningMode

POSE_CONNECTIONS = [
    #shoulders
    (11, 12),

    #left arm
    (11, 13), (13, 15),

    #right arm
    (12, 14), (14, 16),

    #torso
    (11, 23), (12 ,24), (23, 24),

    #Left leg
    (23, 25), (25, 27), (27, 29),

    #Right Leg
    (24, 26), (26, 28), (28, 30)
]

JPEG_QUALITY = 70

app = Flask(__name__)

# Shared state: the worker writes the newest JPEG, viewers just read it.
latest_jpeg = None
cond = threading.Condition()

def PosePrint(message ,current_ms, state, interval_ms=1000):
    if message != state["last_message"] or (current_ms - state["last_print_ms"]) > interval_ms:
       print(message)
       state["last_message"] = message
       state["last_print_ms"] = current_ms 

def lighting_Report(frame, landmarks=None):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    lines = [
        f"Brightness: {gray.mean():.0f} (aim ~90-170)",
        f"Contrast: {gray.std():.0f} (aim > 40)",
        f"Crushed: {(gray < 25).mean()*100:.0f}% lown: {(gray > 230).mean()*100:.0f}%",
    ]

    if landmarks:
        xs = [int(l.x * w) for l in landmarks]
        ys = [int(l.y * h) for l in landmarks]
        x0, x1 = max(min(xs), 0), min(max(xs), w)
        y0, y1 = max(min(ys), 0), min(max(ys), h)
        if x1 > x0 and y1 > y0:
            mask = np.zeros_like(gray, dtype=bool)
            mask[y0:y1, x0:x1] = True
            body, bg = gray[mask].mean(), gray[~mask].mean()
            lines.append(f"Body vs BG: {body:.0f} / {bg:.0f}")

    for i, text in enumerate(lines):
        cv2.putText(frame, text, (10, 25 + i * 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 0), 1)

# media pipe landmarks are drawn on the body 
def mp_draw_lm(frame, landmarks):
    """Replaces mp_draw.draw_landmarks()"""
    # Get the height and width of the frame to convert normalized coordinates to pixel coordinates
    h, w = frame.shape[:2]
    for start, end in POSE_CONNECTIONS:
        # Convert normalized coordinates to pixel coordinates
        x0, y0 = int(landmarks[start].x * w), int(landmarks[start].y * h)
        x1, y1 = int(landmarks[end].x * w),   int(landmarks[end].y * h)
        # Draw the connection line
        cv2.line(frame, (x0, y0), (x1, y1), (0, 200, 0), 2)
        # for lm in [landmarks[start], landmarks[end]]:
    for lm in landmarks:
        # Draw the landmark point
        cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 5, (0, 0, 255), -1)

def confidence_check(landmarks, threshold=0.6):
    return landmarks.visibility > threshold and landmarks.presence > threshold 


def angle_Calculator(lm1, lmV, lm2):
    lm1 = np.array([lm1.x, lm1.y])
    lmV = np.array([lmV.x, lmV.y])
    lm2 = np.array([lm2.x, lm2.y])

    radians = np.arctan2(lm2[1] - lmV[1], lm2[0] - lmV[0]) - np.arctan2(lm1[1] - lmV[1], lm1[0]-lmV[0]) 
    angle = np.abs(radians*180.0/np.pi)

    if angle > 180.0:
        angle = 360 - angle
    return angle

def find_body(exercise_tracker):
    global latest_jpeg
    #Set the settings of mediapipe
    options = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'),
    running_mode=VisionRunningMode.VIDEO)
    #open a videoStream
    stream = cv2.VideoCapture(0)
    windowName = "Workout Tracker"
    #name the window 
    cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
    #Track the start of the wrokout 
    start_time = time.time()
    # gesture state is for help printing
    gesture_state = {"last_message": None, "last_print_ms": 0}

    #create the detection instance 
    with PoseLandmarker.create_from_options(options) as landmarker:

        #while user hasnt clickes "esc" keep tracking 
        while cv2.waitKey(1) != 27:
            has_frame, frame = stream.read()

            if not has_frame:
                print("Unable to capture video")
                break
            #change from BGR to RGB
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            # THe time that has lapsed since the start
            timeStamp_ms = int((time.time() - start_time) * 1000)
            # Runs the pose detection 
            result = landmarker.detect_for_video(mp_image, timeStamp_ms)

            if result.pose_landmarks:
                for bodylms in result.pose_landmarks:
                    mp_draw_lm(frame, bodylms)
                    message = exercise_tracker.process(bodylms, timeStamp_ms)
                    PosePrint(message, timeStamp_ms, gesture_state)
            # get lighting level
            lighting_Report(frame)
            # display window
            cv2.imshow(windowName, frame)

            ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
            if not ok:
                continue
            with cond:
                latest_jpeg = buf.tobytes()
                cond.notify_all()
    # release the stream
    stream.release()
    # destroy all windows created
    cv2.destroyAllWindows()

def stream():
    """One of these runs per viewer; it only forwards the newest frame."""
    last = None
    while True:
        with cond:
            cond.wait_for(lambda: latest_jpeg is not last, timeout=5)
            jpeg = latest_jpeg
        if jpeg is None or jpeg is last:
            continue
        last = jpeg
        yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpeg + b"\r\n"

@app.route("/")
def index():
    return '<img src="/video" style="width:100%">'

@app.route("/video")
def video():
    return Response(stream(), mimetype="multipart/x-mixed-replace; boundary=frame")
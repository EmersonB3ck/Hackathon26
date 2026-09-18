import os 
import sys
import cv2
import mediapipe as mp
import time 

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
    (23, 25), (25, 27),

    #Right Leg
    (24, 26), (26, 28),
]





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


def find_body():
    options = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'),
    running_mode=VisionRunningMode.VIDEO)

    stream = cv2.VideoCapture(0)
    #Track the start of the wrokout 
    start_time = time.time();

    with PoseLandmarker.create_from_options(options) as landmarker:

        #while user hasnt clickes "esc" keep tracking 
        while cv2.waitKey(1) != 27:
            has_frame, frame = stream.read()

            if not has_frame:
                print("Unable to capture video")
                break

            rgb = cv2.cvtColor(frame, cv2.color_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timeStamp_ms = int(time.time() - start_time) * 100

            result = landmarker.detect_for_video(mp.image, timeStamp_ms)

            cv2.imshow("Body Tracker", frame)


    stream.release()
    cv2.destroyAllWindows

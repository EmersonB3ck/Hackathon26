import os 
import sys
import cv2
import mediapipe as mp
import matplotlib.pyplot as plt 
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
    (23, 25), (25, 27), (27, 29),

    #Right Leg
    (24, 26), (26, 28), (28, 30)
]

def PosePrint(message ,current_ms, state, interval_ms=1000):
    if message != state["last_messgae"] or (current_ms - state["last_print_ms"]) > interval_ms:
       print(message)
       state["last_message"] = message
       state["last_print_ms"] = current_ms 



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
    windowName = "Workout Tracker"
    cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)
    #Track the start of the wrokout 
    start_time = time.time()
    gesture_state = {"last_message": None, "last_print_ms": 0}

    with PoseLandmarker.create_from_options(options) as landmarker:

        #while user hasnt clickes "esc" keep tracking 
        while cv2.waitKey(1) != 27:
            has_frame, frame = stream.read()

            if not has_frame:
                print("Unable to capture video")
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            timeStamp_ms = int((time.time() - start_time) * 1000)

            result = landmarker.detect_for_video(mp_image, timeStamp_ms)

            if result.pose_landmarks:
                for bodylms in result.pose_landmarks:
                    mp_draw_lm(frame, bodylms)

                    Left_Shoulder = bodylms[11]
                    Left_Elbow = bodylms[13]
                    Left_Wrist = bodylms[15]
                    Left_Hip = bodylms[23]
                    Left_Knee = bodylms[25]
                    Left_Ankle = bodylms[27]
                    Left_Heel = bodylms[29]
                    Right_Shoulder = bodylms[12]
                    Right_Elbow = bodylms[14]
                    Right_Wrist = bodylms[16]
                    Right_Hip = bodylms[24]
                    Right_Knee = bodylms[26]
                    Right_Ankle = bodylms[28]
                    Right_Heel = bodylms[30]

                    if (Left_Shoulder.y > Left_Knee.y):
                        PosePrint("Good Start", timeStamp_ms, gesture_state)
            cv2.imshow(windowName, frame)
    stream.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    find_body()

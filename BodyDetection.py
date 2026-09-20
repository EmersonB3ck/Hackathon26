import cv2
import numpy as np
import mediapipe as mp
import time 

# --MediaPipe Task API shortcuts--
BaseOptions           = mp.tasks.BaseOptions
# HandLandmarker is the main class for hand tracking in mediapipe tasks 
PoseLandmarker        = mp.tasks.vision.PoseLandmarker
# HandLandmarkerOptions is used to specify options for the hand landmarker, such as the model file and running mode.
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
# VisionRunningMode is used to specify the running mode for the hand landmarker, such as video or image mode.
VisionRunningMode     = mp.tasks.vision.RunningMode

# landmark connections to make the skeleton overlay
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

#Useful development helper that determines if lighting will cuase problems with tracking 
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


# Draws the pose skeleton on the frame using the earlier identified connections
# each red dot is a land mark and the green lines are their connections 
def mp_draw_lm(frame, landmarks):
    """Replaces mp_draw.draw_landmarks()"""
    # Get the height and width of the frame to convert normalized coordinates to pixel coordinates
    h, w = frame.shape[:2]

    for start, end in POSE_CONNECTIONS:
        # Convert mediapipe's normalized (0-1) coordinates to pixel positions
        x0, y0 = int(landmarks[start].x * w), int(landmarks[start].y * h)
        x1, y1 = int(landmarks[end].x * w),   int(landmarks[end].y * h)
        # Draw the connection line
        cv2.line(frame, (x0, y0), (x1, y1), (0, 200, 0), 2)

    for lm in landmarks:
        # Draw the landmark point
        cv2.circle(frame, (int(lm.x * w), int(lm.y * h)), 5, (0, 0, 255), -1)


# Returns if a landmark is unblocked and present in the frame 
# Use this to get rid of fuzzy frames or when mediaPipe tries to predict landmarks and fails wildly
def confidence_check(landmarks, threshold=0.8):
    return landmarks.visibility > threshold and landmarks.presence > threshold 


# Calculates the angle at the vertex lmV(landmark vertex) which is 
# the three landmarks which is used for each workout 
def angle_Calculator(lm1, lmV, lm2):
    lm1 = np.array([lm1.x, lm1.y])
    lmV = np.array([lmV.x, lmV.y])
    lm2 = np.array([lm2.x, lm2.y])

    # angle between 2 vectors 
    radians = np.arctan2(lm2[1] - lmV[1], lm2[0] - lmV[0]) - np.arctan2(lm1[1] - lmV[1], lm1[0]-lmV[0]) 
    angle = np.abs(radians*180.0/np.pi)

    if angle > 180.0:
        # normalize the angle 
        angle = 360 - angle
    return angle


# This is the main camera and pose detection loop
def find_body(exercise_tracker):
    #Set the settings of mediapipe - set to video for a constant stream which has time stamps
    options = PoseLandmarkerOptions(base_options=BaseOptions(model_asset_path='pose_landmarker_lite.task'),
    running_mode=VisionRunningMode.VIDEO)

    #open a videoStream
    stream = cv2.VideoCapture(0)
    windowName = "Workout Tracker"
    #name the window 
    cv2.namedWindow(windowName, cv2.WINDOW_NORMAL)

    #Used for tracking frames time stamp
    start_time = time.time()

    #create the detection instance 
    with PoseLandmarker.create_from_options(options) as landmarker:
        # while the exercise is not complete
        while not exercise_tracker.complete:
            # store the key being pressed
            key = cv2.waitKey(1) & 0xFF

             #if user clickes "esc" break 
            if key == 27:
               break

            #if no frames are available unable send error and break stream
            has_frame, frame = stream.read()
            if not has_frame:
                print("Unable to capture video")
                break

            # MediaPipe uses RGB coloring but OpenCV captures in BGR so change the frame color format
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

            # The time that has lapsed since the start
            timeStamp_ms = int((time.time() - start_time) * 1000) 
            result = landmarker.detect_for_video(mp_image, timeStamp_ms)

            if result.pose_landmarks:
                for bodylms in result.pose_landmarks:
                    #draw skeleton overlay
                    mp_draw_lm(frame, bodylms)
                    #pass the frames landmarks and the current key to the exercise_tracker
                    # returns a status message when a value changes
                    message = exercise_tracker.process(bodylms, timeStamp_ms, key)
                    if message:
                        print(message, flush=True)

                    # adds the current vertex landmark's angle to the frame 
                    angle_info = exercise_tracker.get_angle(bodylms, frame.shape[1], frame.shape[0])
                    if angle_info:
                        text, x, y = angle_info
                        cv2.putText(frame, text, (x + 15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

            # this is for the text block at the top left of the frame which tracks
            # reps, sets, angle, and rest when rest state is active 
            for i, line in enumerate(exercise_tracker.get_WorkoutInfo(timeStamp_ms)):
                cv2.putText(frame, line, (10, 25 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # get lighting level
            #lighting_Report(frame)

            # display window
            cv2.imshow(windowName, frame)

           
    # release the stream
    stream.release()
    # destroy all windows created
    cv2.destroyAllWindows()
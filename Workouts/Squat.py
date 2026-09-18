import time
import cv2
import mediapipe as mp

BaseOptions = mp.tasks.BaseOptions
PoseLandmarker = mp.tasks.vision.PoseLandmarker
PoseLandmarkerOptions = mp.tasks.vision.PoseLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

model_path = 'Hackathon26/Workouts/pose_landmarker_lite.task'

shoulder_y = 0
knee_y = 0

# Runs on MediaPipe's own thread each time a frame finishes processing
def on_result(result, output_image, timestamp_ms):
    global shoulder_y, knee_y
    if not result.pose_landmarks:
        return
    lms = result.pose_landmarks[0]          # first person detected
    shoulder_y = (lms[11].y + lms[12].y) / 2   # avg of left/right shoulder
    knee_y = (lms[25].y + lms[26].y) / 2       # avg of left/right knee

def squat():
    options = PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.LIVE_STREAM,
        result_callback=on_result)

    cap = cv2.VideoCapture(0)
    start = time.time()

    with PoseLandmarker.create_from_options(options) as landmarker:
        while cv2.waitKey(1) != 27:  # Esc to quit
            ok, frame = cap.read()
            if not ok:
                break

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            landmarker.detect_async(mp_image, int((time.time() - start) * 1000))

            # Draw the values on the video frame
            cv2.putText(frame, f"Shoulder Y: {shoulder_y:.3f}", (10, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(frame, f"Knee Y: {knee_y:.3f}", (10, 65),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.imshow("Squat", frame)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    squat()
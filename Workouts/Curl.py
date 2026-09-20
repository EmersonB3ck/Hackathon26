import time
import cv2
import mediapipe as mp
from BodyDetection import angle_Calculator, confidence_check
from RestTimer import RestTimer

class Curl:
    def __init__(self, reps, sets, rest_seconds=120):
        self.reps = reps
        self.sets = sets
        self.rep_count = 0
        self.set_count = 0

        self.stage = "Extended"

        self.resting = False
        self.Rtimer = RestTimer(rest_seconds)

        self.complete = False
        self.current_angle = None
        self.low_confidence = 0
        # last warning given to user
        self.last_warning = 0

    # returns the angle_text, pixel.x, pixel.y so BodyDetection can draw it on the frame
    def get_angle(self, landmarks, w , h):
        if self.current_angle is None:
            return None
        #Elbow landmark 
        ELm = landmarks[13]
        return(f"{self.current_angle:.0f}", int(ELm.x * w), int(ELm.y * h))

    # The text to be displayed on the frame
    # if resting then writes rest time and way to skip 
    # if not then shows reps, sets, and current angle 
    def get_WorkoutInfo(self, timestamp_ms):
        if self.resting:
            secs = self.Rtimer.remaining_seconds(timestamp_ms)
            mins, s = divmod(secs, 60)
            return [f"BREAK: {mins}:{s:02d}", "Press 'b' to skip water break"]
        angle_text = f"Angle: {self.current_angle:.0f}" if self.current_angle is not None else "Angle: --"
        return [f"Curls: {self.rep_count}/{self.reps}", f"Sets: {self.set_count}/{self.sets}", angle_text]


    # called once per frame for find_body to deal with all the curl logic 
    def process(self, landmarks, timestamp_ms, key=None):
        if self.complete:
            return None

        # if in resting mode
        if self.resting:
        # if user clicks b then skips current break
            skip = key == ord('b')
            if self.Rtimer.check(timestamp_ms, skip):
                self.resting = False
                return "Break over, get ready!"
            return None # continue to rest

        # get needed landmarks 
        Left_Shoulder = landmarks[11]
        Right_Shoulder = landmarks[12]
        Left_Elbow = landmarks[13]
        Right_Elbow = landmarks[14]
        Left_Wrist = landmarks[15]
        Right_Wrists = landmarks[16]

        if not all(confidence_check(l, threshold=0.8) for l in (Left_Shoulder, Left_Elbow, Left_Wrist)):
            self.low_confidence += 1

            if self.low_confidence >= 5 and (timestamp_ms - self.last_warning) > 2000:
                self.last_warning = timestamp_ms
                return "move your whole bdy into frame"
            return None
        self.low_confidence = 0

        angle = angle_Calculator(Left_Shoulder, Left_Elbow, Left_Wrist)
        self.current_angle = angle

        message = None
        # if the arm is marked as curled and the angle grows greater than 160 degrees
        # the user is starting to extend their arms
        if angle > 160 and self.stage == "Extended":
            self.stage = "Curled"

        # if the arm is marked as extended and the angle decreases to below 50 degrees
        # the user is starting to curl
        elif angle < 40 and self.stage == "Curled":
            self.stage = "Extended"
            self.rep_count += 1
            message = f" Rep: {self.rep_count}/{self.reps}"
            # once completing all reps then reset rep counter and increase set counter
            if self.rep_count >= self.reps:
                self.rep_count = 0
                self.set_count += 1
            
                # When user completes all sets print a success statement
                if self.set_count >= self.sets:
                    self.complete = True
                    message = "Curls Complete! Great Job!"

                else:
                    self.resting = True
                    self.Rtimer.start(timestamp_ms)
                    message = f" Sets: {self.set_count}/{self.sets} complete - resting"
        return message
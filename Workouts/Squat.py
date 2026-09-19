import time
import cv2
import mediapipe as mp
from BodyDetection import angle_Calculator
from RestTimer import RestTimer
class Squat:
    def __init__(self, reps, sets, rest_seconds=120):
        # initialize a squat 
        self.reps = reps
        self.sets = sets
        self.rest_seconds = rest_seconds * 1000
        self.rep_count = 0
        self.set_count = 0
        self.stage = "Upright"
        self.resting = False
        self.Rtimer = RestTimer(rest_seconds)
        self.complete = False

    def process(self, landmarks, timestamp_ms, key=None):
        if self.complete:
            return None

        if self.resting:
            skip = key == ord('b')
            if self.Rtimer.check(timestamp_ms, skip):
                self.resting = False
                return "Break over, get ready!"
            return None

        # get all the landmarks needed for a squat 
        Left_Shoulder = landmarks[11]
        Right_Shoulder = landmarks[12]
        Left_Hip = landmarks[23]
        Right_Hip = landmarks[24]
        Left_Knee = landmarks[25]
        Right_Knee = landmarks[26]
        Left_Ankle = landmarks[27]
        Right_Ankle = landmarks[28]

        # calculate the angle between 3 landmarks
        # The knee is the vertex between the Hip and the Ankle 
        angle = angle_Calculator(Left_Hip, Left_Knee, Left_Ankle)

        message = None

        # if the angle of your hips and ankles are less than 100 
        # set the state to be down
        if angle < 100 and self.stage == "Upright":
            self.stage = "Down"

        # if your marked as being down and your angle is greater than 160(standing up)
        elif angle > 160 and self.stage == "Down":
            self.stage = "Upright"
            self.rep_count += 1
            message = f" Rep: {self.rep_count}/{self.reps}"

            if self.rep_count >= self.reps:
                self.rep_count = 0
                self.set_count += 1

                if self.set_count >= self.sets:
                    self.complete = True
                    message = "Squats Complete! Great Job!"

                else:
                    self.resting = True
                    self.Rtimer.start(timestamp_ms)
                message = f" Sets: {self.set_count}/{self.sets} complete - resting"
        return message
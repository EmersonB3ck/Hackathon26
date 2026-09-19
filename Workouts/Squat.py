import time
import cv2
import mediapipe as mp
from BodyDetection import angle_Calculator
class Squat:
    def __init__(self, reps, sets):
        # initialize a squat 
        self.reps = reps
        self.sets = sets
        self.rep_count = 0
        self.set_count = 0
        self.stage = "Upright"

    def process(self, landmarks, timestamp_ms):
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

        # if the angle of your hips and ankles are less than 100 
        # set the state to be down
        if angle < 100 and self.stage == "Upright":
            self.stage = "Down"
        # if your marked as being down and your angle is greater than 160(standing up)
        elif angle > 160 and self.stage == "Down":
            self.stage = "Upright"
            self.rep_count += 1
            if self.rep_count >= self.reps:
                self.rep_count = 0
                self.set_count += 1
        return f"Squats: Rep: {self.rep_count}/{self.reps} | Set: {self.set_count}/{self.sets}"

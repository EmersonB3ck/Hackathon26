import time
import cv2
import mediapipe as mp
from BodyDetection import angle_Calculator, confidence_check
from RestTimer import RestTimer

class PushUp:
    def __init__(self, reps, sets, rest_seconds=120):
        # initialize a push-up
        self.reps = reps
        self.sets = sets
        self.rep_count = 0
        self.set_count = 0

        #what stage of the push-up you are at
        self.stage = "Upright"
        # flag for resting 

        self.resting = False
        # rest timer
        self.Rtimer = RestTimer(rest_seconds)
        
        # flag for if the workout is completed
        self.complete = False
        # current angle wanting to calculate
        self.current_angle = None
        # mediapipe confidence of a single frame 
        self.low_confidence = 0
        # last warning given to user
        self.last_warning = 0

    # returns the angle_text, pixel.x, pixel.y so BodyDetection can draw it on the frame
    def get_angle(self, landmarks, w , h):
        if self.current_angle is None:
            return None
        #elbow landmark 
        KLm = landmarks[13]
        return(f"{self.current_angle:.0f}", int(KLm.x * w), int(KLm.y * h))

    # The text to be displayed on the frame
    # if resting then writes rest time and way to skip 
    # if not then shows reps, sets, and current angle 
    def get_WorkoutInfo(self, timestamp_ms):
        if self.resting:
            secs = self.Rtimer.remaining_seconds(timestamp_ms)
            mins, s = divmod(secs, 60)
            return [f"BREAK: {mins}:{s:02d}", "Press 'b' to skip water break"]
        angle_text = f"Angle: {self.current_angle:.0f}" if self.current_angle is not None else "Angle: --"
        return [f"PushUp: {self.rep_count}/{self.reps}", f"Sets: {self.set_count}/{self.sets}", angle_text ]

    # this is called once a frame (by find_body()) and hold sthe main logic for a squat
    # Returns a string that is shows notable achievements like completing a rep, set, whole workout, or entering break 
    def process(self, landmarks, timestamp_ms, key=None):
        # if exercise is complete then break 
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

        # get all the landmarks needed for a squat 
        right_shoulder = landmarks[12]
        right_elbow = landmarks[14]
        right_wrist = landmarks[16]
        left_shoulder = landmarks[11]
        left_elbow = landmarks[13]
        left_wrist = landmarks[15]

        # confidence check on frames
        # if 5 or more frames have low confidence then provides a warning so the user can step back into frame 
        # allowing mediapipe to reset
        if not all(confidence_check(l, threshold=0.8) for l in (left_shoulder, left_elbow, left_wrist)):
            # if bad frame then awdd to low confidence count
            self.low_confidence += 1
            # once 5 or more bad frames in a row comes in and the last warning was more than 2s ago
            #return the message
            if self.low_confidence >= 5 and (timestamp_ms - self.last_warning) > 2000:
                self.last_warning = timestamp_ms
                return "move your whole body into frame"
            return None
        self.low_confidence = 0

        # calculate the angle between 3 landmarks
        # The knee is the vertex between the Hip and the Ankle 
        # way we count reps
        angle = angle_Calculator(left_shoulder, left_elbow, left_wrist)
        # store the angle to be placed on the frame 
        self.current_angle = angle

        message = None

        # while the user is planking and the angle drops below 100 degrees 
        # the user has started descending for the push-up so state is Down 
        if angle < 100 and self.stage == "Upright":
            self.stage = "Down"

        # if user is marked as down and the angle becoes greater than 90 degrees 
        # then the user is marked as standing upright completing one rep
        elif angle > 155 and self.stage == "Down":
            self.stage = "Upright"
            self.rep_count += 1
            message = f" Rep: {self.rep_count}/{self.reps}"
            # once completing all reps then reset rep counter and increase set counter
            if self.rep_count >= self.reps:
                self.rep_count = 0
                self.set_count += 1

                # When user completes all sets print a success statement
                if self.set_count >= self.sets:
                    self.complete = True
                    message = "PushUp Complete! Great Job!"

                #otherwise they are resting between sets
                else:
                    self.resting = True
                    self.Rtimer.start(timestamp_ms)
                    message = f" Sets: {self.set_count}/{self.sets} complete - resting"
        return message
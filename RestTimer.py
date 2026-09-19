import time

class RestTimer:
    def __init__(self, rest_seconds):
        # initialize a squat 
        self.rest_ms = rest_seconds * 1000
        self.start_ms = None

    def start(self, timestamp_ms):
        self.start_ms = timestamp_ms

    def remaining_seconds(self, timestamp_ms):
        elapse = timestamp_ms - self.start_ms
        remaining_time = max(0, self.rest_ms - elapse)
        return remaining_time // 1000

    def check(self, timestamp_ms, skip=False):
        elapse = timestamp_ms - self.start_ms
        remaining_time = max(0, self.rest_ms - elapse)
        if skip or remaining_time <= 0:
            self.start_ms = None
            return True
        return False
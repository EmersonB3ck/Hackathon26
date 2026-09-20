from colorama import init, Style 
from BodyDetection import find_body
from Workouts.Squat import Squat
from Workouts.Curl import Curl
from Workouts.Bench import Bench
from Workouts.PushUp import PushUp
from voice import generate_audio, speak
init()
# all exercises we have 
EXERCISES = { "squat" : Squat, "bench" : Bench, "pushup" : PushUp, "curl" : Curl}

def workout_session():
    while True:
    # ask the user 
        #speak("Pick a workout from the list: " + ", ".join(EXERCISES.keys()))
        print("\033[1mPick a workout from the list:\033[0m", ", ".join(EXERCISES.keys()))
        #speak("Which exercise?: ")
        chosen = input("Which exercise?: ").strip().lower()

        while chosen not in EXERCISES:
            chosen = input(f"'{chosen}' is not on the wrokout list. Please select a new workout").strip().lower()

        #speak("Number of reps per set?: ")
        reps = int(input("# of reps per set: "))
        #speak("Number of sets?: ")
        sets = int(input("Number of sets: "))
        #speak("How many seconds of rest between sets (120s = 2mins)?: ")
        rest_time = input("How many seconds of rest between sets (120s = 2mins)?: ").strip()
        rest = int(rest_time) if rest_time else 120
        tracker = EXERCISES[chosen](reps, sets, rest)
        find_body(tracker)

        #speak("Pick another workout? (y/n): ")
        again = input("Pick another workout? (y/n): ").strip().lower()
        if again != "y":
            #speak("Great Workout ")
            print("Great Workout ")
            break

if __name__ == "__main__":
    workout_session()
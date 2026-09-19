from colorama import init, Style 
from BodyDetection import find_body
from Workouts.Squat import Squat
init()
# all exercises we have 
EXERCISES = { "squat" : Squat}

def workout_session():
    while True:
    # ask the user 
        print("\033[1mPick a workout from the list:\033[0m", ",".join(EXERCISES.keys()))
        chosen = input("Which exercise?: ").strip().lower()
    
        while chosen not in EXERCISES:
            chosen = input(f"'{chosen}' is not on the wrokout list. Please select a new workout").strip().lower()
    
        reps = int(input("# of reps per set: "))
        sets = int(input("Number of sets: "))
        rest_time = input("How many seconds of rest between sets (120s = 2mins)?: ").strip()
        rest = int(rest_time) if rest_time else 120
        tracker = EXERCISES[chosen](reps, sets, rest)
        find_body(tracker)

        again = input("Pick another workout? (y/n): ").strip().lower()
        if again != "y":
            print("Great Workout ")
            break

if __name__ == "__main__":
    workout_session()
import threading
from dotenv import load_dotenv
import os
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play

load_dotenv(override=True)
key = os.getenv("ELEVEN_API_KEY")
# print("Key loaded:", key is not None, "| length:", len(key) if key else 0)

client = ElevenLabs(api_key=os.getenv("ELEVEN_API_KEY"))

speak_lock = threading.Lock()

def generate_audio(text: str):
    with speak_lock:
        audio = client.text_to_speech.convert(
            text=text,
            voice_id="nPczCjzI2devNBz1zQrb",
            model_id="eleven_flash_v2_5",
            output_format="mp3_44100_128",
        )
        play(audio)

def speak(text: str):
    threading.Thread(target=generate_audio, args=(text,), daemon=True).start()

if __name__ == "__main__":
    text = "That was not a full squat, you nonchalant fool. You need to go lower, and I mean all the way down. Feel the burn in your quads and glutes, and remember, form is everything. Now, let's see you do it right this time!"
    generate_audio(text)
import os
import random
import time
import logging
import subprocess
import base64
import io

import pyaudio
import speech_recognition as sr
from pydub import AudioSegment
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .zshrc
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Retrieve API keys
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')

# Initialize clients
groq_client = Groq(api_key=GROQ_API_KEY)
elevenlabs_client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Speech recognizer setup
recognizer = sr.Recognizer()

# Constants
WAKE_WORD = "alice"
VOICE_ID = "cgSgspJ2msm6clMCkdW9"
MODEL = "llama3-70b-8192"
style = 0.1
stab = 0.3
sim = 0.2

# Assistant's initial context
initial_context = [{
    "role": "system",
    "content": f"You are a voice assistant named {WAKE_WORD}. Your responses should be short and suitable for speech, using conversational phrases. Avoid text-only tokens."
}]
context = initial_context.copy()

def stream_audio(audio_chunks):
    """Play audio stream."""
    p = pyaudio.PyAudio()
    audio_data = b''.join(chunk for chunk in audio_chunks)
    audio = AudioSegment.from_mp3(io.BytesIO(audio_data))
    
    stream = p.open(format=p.get_format_from_width(audio.sample_width),
                    channels=audio.channels,
                    rate=audio.frame_rate,
                    output=True)
    
    for offset in range(0, len(audio.raw_data), 1024):
        chunk = audio.raw_data[offset:offset + 1024]
        stream.write(chunk)

    stream.stop_stream()
    stream.close()
    p.terminate()

def listen_for_input(wait_for_wake_word=True):
    """Listen for audio input and process it."""
    mode_message = f"Listening for wake word '{WAKE_WORD}'..." if wait_for_wake_word else "Listening for user input..."
    logging.info(mode_message)

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=1)
        try:
            audio = recognizer.listen(source, timeout=10, phrase_time_limit=10)
            text = recognizer.recognize_google(audio).lower()
            if wait_for_wake_word:
                if WAKE_WORD in text:
                    logging.info("Wake word detected.")
                    speak("How you doing?")
                    return listen_for_input(wait_for_wake_word=False)
                elif "restart" in text:
                    return "restart"
            else:
                return process_user_command(text)
        except (sr.WaitTimeoutError, sr.UnknownValueError):
            logging.warning("Could not understand audio. Trying again.")
            return listen_for_input(wait_for_wake_word)
        except sr.RequestError as e:
            logging.error(f"Speech recognition service error: {e}")
            return None

def process_user_command(text):
    """Process user commands."""
    logging.info(f"User said: {text}")
    if "look at" in text or "what do you see" in text:
        return "vision_request" + text
    return text


def speak(text):
    """Convert text to speech and play it."""
    audio_stream = elevenlabs_client.text_to_speech.convert_as_stream(
        voice_id=VOICE_ID,
        optimize_streaming_latency="2",
        output_format="mp3_22050_32",
        text=text,
        model_id="eleven_turbo_v2_5",
        voice_settings=VoiceSettings(
            stability=stab,
            similarity_boost=sim,
            style=style,
        ),
    )
    stream_audio(audio_stream)

# Main interaction loop
try:
    waiting_for_wake = True
    while True:
        user_input = listen_for_input(waiting_for_wake)
        if user_input:
            if user_input.lower() == "restart":
                logging.info("Restarting conversation...")
                context.clear()
                context.append(initial_context[0])
                speak("I just cleared the context window")
                waiting_for_wake = True
            else:
                context.append({"role": "user", "content": user_input})
                chat_completion = groq_client.chat.completions.create(
                    messages=context,
                    model=MODEL,
                    temperature=0.6,
                    max_tokens=1024,
                )
                response = chat_completion.choices[0].message.content
                context.append({"role": "assistant", "content": response})
                logging.info(f"Assistant responded: {response}")

            speak(response)
            waiting_for_wake = False
        else:
            waiting_for_wake = True

except KeyboardInterrupt:
    logging.info("Exiting the conversation.")

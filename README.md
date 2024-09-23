# Robs Voice Assistant

This is a custom voice assistant project i'm running locally on a mac using two API's. Groq's LLaMA 3.1 (70B) model & the ElevenLabs API for smooth text-to-speech (TTS) output. For STT I’m using Google's Speech Recognition, audio output is handled with PyAudio.

## Features

- **Lightning-Fast Responses**: Groq's LLaMA model
- **Natural-Sounding Voices**: TTS from ElevenLabs
- **Accurate Voice Recognition**: Google’s STT.
- **Smooth Audio Playback**: PyAudio handles the audio output

## Installation

For running this on Mac:

1. **Update your system**:
   ```bash
   brew update && brew upgrade
   - brew install portaudio ffmpeg flac libjpeg
   - pip install -r requirements.txt
   ```

## Extra steps may that may be needed:

- export GROQ_API_KEY={KEY}
- export ELEVENLABS_API_KEY={KEY}
- Create a virtual env using: `python3 -m venv venv`
- run: `pip install -r requirements.txt` after virtual env is set up.

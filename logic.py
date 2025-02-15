import os
import json
from datetime import datetime
from threading import Event, Thread
from collections import deque
import numpy as np
import pyaudio
import soundcard as sc
import soundfile as sf
from playsound import playsound

# Constants
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BUFFER_SECONDS = 60  # 4 minutes
MAX_FRAMES = BUFFER_SECONDS * RATE // CHUNK
SAMPLE_RATE = 44100  # For system audio
CONFIG_FILE = "config.json"

# Circular buffers
audio_buffer = deque(maxlen=MAX_FRAMES)
system_audio_buffer = deque(maxlen=MAX_FRAMES)

# Control flags
listening = Event()
recording = Event()

# Audio setup
p = pyaudio.PyAudio()

# Config management
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {"record_binding": ""}

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

config = load_config()
record_binding = config.get("record_binding", "")

# Audio logic
def listen_to_microphone():
    stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    try:
        while listening.is_set():
            data = stream.read(CHUNK)
            stereo_data = convert_mono_to_stereo(data)
            audio_buffer.append(stereo_data)
    finally:
        stream.stop_stream()
        stream.close()

def convert_mono_to_stereo(mono_data):
    stereo_data = bytearray()
    for i in range(0, len(mono_data), 2):
        sample = mono_data[i:i+2]
        stereo_data.extend(sample)
        stereo_data.extend(sample)
    return bytes(stereo_data)

def listen_to_system_audio():
    with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
        while listening.is_set():
            data = mic.record(numframes=CHUNK)
            system_audio_buffer.append(data)

def save_combined_recording(update_status):
    if not audio_buffer and not system_audio_buffer:
        update_status("Buffers are empty. Nothing to save.")
        return

    recordings_dir = "recordings"
    os.makedirs(recordings_dir, exist_ok=True)
    today_date = datetime.now().strftime("%Y-%m-%d")

    existing_files = [
        f for f in os.listdir(recordings_dir)
        if f.startswith(f"recording-{today_date}-") and f.endswith(".wav")
    ]
    numbers = [
        int(f.split(f"recording-{today_date}-")[1].split(".wav")[0])
        for f in existing_files if f.split(f"recording-{today_date}-")[1].split(".wav")[0].isdigit()
    ]
    next_number = max(numbers, default=0) + 1
    filename = os.path.join(recordings_dir, f"recording-{today_date}-{next_number}.wav")

    mic_data = b''.join(audio_buffer)
    system_data = np.concatenate(system_audio_buffer)

    mic_array = np.frombuffer(mic_data, dtype=np.int16).reshape(-1, CHANNELS)
    system_array = np.int16(system_data * 32767)
    combined_array = np.hstack((mic_array[:len(system_array)], system_array[:len(mic_array)]))

    sf.write(filename, combined_array, RATE)
    update_status(f"Recording saved as {filename}")

    audio_buffer.clear()
    system_audio_buffer.clear()
    update_status("Buffers cleared for the next recording.")

    playsound('sfx/recordingsfx.wav')

def toggle_listening(toggle_button, update_status):
    if not listening.is_set():
        listening.set()
        Thread(target=listen_to_microphone, daemon=True).start()
        Thread(target=listen_to_system_audio, daemon=True).start()
        toggle_button.config(text="Stop Listening", bg="#CCC5B9")
        update_status("Listening started.")
    else:
        listening.clear()
        audio_buffer.clear()
        system_audio_buffer.clear()
        toggle_button.config(text="Start Listening", bg="#EB5E28")
        update_status("Listening stopped. Buffers cleared.")

def cleanup():
    listening.clear()
    p.terminate()
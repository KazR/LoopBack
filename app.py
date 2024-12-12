import tkinter as tk
from tkinter import ttk
from threading import Thread, Event
from collections import deque
import pyaudio
import os
from datetime import datetime
import soundcard as sc
import soundfile as sf
import numpy as np
import pyglet

pyglet.font.add_file('Fonts/Altone-Regular.ttf')
title_font = ("Altone Trial", 24)
text_font = ("Altone Trial", 12)

# Constants
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BUFFER_SECONDS = 240  # 4 minutes
MAX_FRAMES = BUFFER_SECONDS * RATE // CHUNK
SAMPLE_RATE = 44100  # For system audio

# Circular buffer
audio_buffer = deque(maxlen=MAX_FRAMES)
system_audio_buffer = deque(maxlen=MAX_FRAMES)

# Control flags
listening = Event()
recording = Event()

# Audio setup
p = pyaudio.PyAudio()

def listen_to_microphone():
    """Continuously listen to the microphone and store data in the buffer."""
    stream = p.open(format=FORMAT, channels=1, rate=RATE, input=True, frames_per_buffer=CHUNK)
    try:
        while listening.is_set():
            data = stream.read(CHUNK)
            # Convert mono data to stereo
            stereo_data = convert_mono_to_stereo(data)
            audio_buffer.append(stereo_data)
    finally:
        stream.stop_stream()
        stream.close()

def convert_mono_to_stereo(mono_data):
    """Convert mono audio data to stereo by duplicating each sample."""
    stereo_data = bytearray()
    for i in range(0, len(mono_data), 2):  # Process 2 bytes (1 sample) at a time
        sample = mono_data[i:i+2]  # Extract one sample (2 bytes)
        stereo_data.extend(sample)  # Write to left channel
        stereo_data.extend(sample)  # Write to right channel
    return bytes(stereo_data)

def listen_to_system_audio():
    """Continuously listen to system audio and store data in the buffer."""
    with sc.get_microphone(id=str(sc.default_speaker().name), include_loopback=True).recorder(samplerate=SAMPLE_RATE) as mic:
        while listening.is_set():
            data = mic.record(numframes=CHUNK)
            system_audio_buffer.append(data)

def save_combined_recording():
    """Combine and save the microphone and system audio buffers to a .wav file."""
    if not audio_buffer and not system_audio_buffer:
        update_status("Buffers are empty. Nothing to save.")
        return

    # Ensure the 'recordings' directory exists
    recordings_dir = "recordings"
    os.makedirs(recordings_dir, exist_ok=True)

    # Get today's date in YYYY-MM-DD format
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Find the next sequential number for today's date
    existing_files = [
        f for f in os.listdir(recordings_dir)
        if f.startswith(f"recording-{today_date}-") and f.endswith(".wav")
    ]
    numbers = [
        int(f.split(f"recording-{today_date}-")[1].split(".wav")[0])
        for f in existing_files if f.split(f"recording-{today_date}-")[1].split(".wav")[0].isdigit()
    ]
    next_number = max(numbers, default=0) + 1

    # Generate the filename
    filename = os.path.join(recordings_dir, f"recording-{today_date}-{next_number}.wav")

    # Combine audio data
    mic_data = b''.join(audio_buffer)
    system_data = np.concatenate(system_audio_buffer)

    # Match sample rates
    mic_array = np.frombuffer(mic_data, dtype=np.int16).reshape(-1, CHANNELS)
    system_array = np.int16(system_data * 32767)  # Convert float to int16

    combined_array = np.hstack((mic_array[:len(system_array)], system_array[:len(mic_array)]))

    # Save the combined audio
    sf.write(filename, combined_array, RATE)
    update_status(f"Recording saved as {filename}")

    # Clear buffers
    audio_buffer.clear()
    system_audio_buffer.clear()
    update_status("Buffers cleared for the next recording.")

def toggle_listening():
    """Start or stop the listening threads."""
    if not listening.is_set():
        listening.set()
        Thread(target=listen_to_microphone, daemon=True).start()
        Thread(target=listen_to_system_audio, daemon=True).start()
        toggle_button.config(text="Stop Listening", bg="#CCC5B9")  
        update_status("Listening started.")
    else:
        listening.clear()
        toggle_button.config(text="Start Listening", bg="#EB5E28") 
        update_status("Listening stopped.")

def record_audio():
    """Record the current buffer to a file."""
    if listening.is_set():
        save_combined_recording()
    else:
        update_status("Please start listening before recording.")

def update_status(message):
    """Update the status box with a new message."""
    status_box.config(state="normal")
    status_box.insert(tk.END, f"{message}\n")
    status_box.config(state="disabled")
    status_box.see(tk.END)

# Create main window
app = tk.Tk()
app.title("LoopBack")
app.geometry("380x325")
app.resizable(False, False)
app.configure(bg="#252422")

MyLabel = tk.Label(app,text="loopback",font=title_font, bg="#252422", fg="#FFFCF2")
MyLabel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Add Toggle Button for Listening
toggle_button = tk.Button(
    app,
    text="Start Listening",
    font=text_font,
    bg="#EB5E28",
    fg="#FFFCF2",
    width=35,
    command=toggle_listening
)
toggle_button.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

# Record button
record_button = tk.Button(
    app,
    text="Record",
    font=text_font,
    bg="#EB5E28",
    fg="#FFFCF2",
    width=35,
    command=record_audio
)
record_button.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

# Status
status_box = tk.Text(
    app,
    height=8,
    width=45,
    bg="#252422",
    fg="#FFFCF2",
    font=("Inter", 10),
    wrap="word",
    state="disabled",
)
status_box.grid(row=5, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

def on_closing():
    """Handle the application closing event."""
    listening.clear()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

# Run the application
app.mainloop()

# Cleanup
p.terminate()

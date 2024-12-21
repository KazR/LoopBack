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
import json

# Fonts
title_font = ("Corbel", 24)
text_font = ("Corbel", 12)

# Constants
CHUNK = 512
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BUFFER_SECONDS = 240  # 4 minutes
MAX_FRAMES = BUFFER_SECONDS * RATE // CHUNK
SAMPLE_RATE = 44100  # For system audio
CONFIG_FILE = "config.json"

# Circular buffer
audio_buffer = deque(maxlen=MAX_FRAMES)
system_audio_buffer = deque(maxlen=MAX_FRAMES)

# Control flags
listening = Event()
recording = Event()

# Audio setup
p = pyaudio.PyAudio()

# Load or initialize config
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

# Functions
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

def save_combined_recording():
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

def toggle_listening():
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

def record_audio():
    if listening.is_set():
        save_combined_recording()
    else:
        update_status("Please start listening before recording.")

def update_status(message):
    status_box.config(state="normal")
    status_box.insert(tk.END, f"{message}\n")
    status_box.config(state="disabled")
    status_box.see(tk.END)

def set_record_binding():
    update_status("Press a key combination to set as the record binding.")
    app.bind("<KeyPress>", capture_binding)

def capture_binding(event):
    global record_binding
    record_binding = f"<{event.keysym}>"
    config["record_binding"] = record_binding
    save_config(config)
    update_binding_button()
    update_status(f"Record binding set to: {record_binding}")
    app.unbind("<KeyPress>")

def update_binding_button():
    binding_button.config(text=f"Binding: {record_binding or 'None'}")

def on_key_press(event):
    if f"<{event.keysym}>" == record_binding:
        record_audio()

# Create main window
app = tk.Tk()
app.title("loopBack")
app.geometry("345x350")
app.resizable(False, False)
app.configure(bg="#252422")
app.bind("<KeyPress>", on_key_press)

MyLabel = tk.Label(app, text="loopBack", font=title_font, bg="#252422", fg="#FFFCF2")
MyLabel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

# Set Binding button
binding_button = tk.Button(
    app,
    text=f"Binding: {record_binding or 'None'}",
    font=text_font,
    bg="#6A4C93",
    fg="#FFFCF2",
    width=35,
    command=set_record_binding
)
binding_button.grid(row=2, column=1, padx=10, pady=10, sticky="nsew")

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
    font=("Lucida Console", 8),
    wrap="word",
    state="disabled"
)
status_box.grid(row=6, column=1, columnspan=3, padx=10, pady=10, sticky="nsew")

def on_closing():
    listening.clear()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

# Run the application
app.mainloop()

# Cleanup
p.terminate()

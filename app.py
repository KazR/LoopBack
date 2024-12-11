import tkinter as tk
import numpy as np
from tkinter import ttk
import sounddevice as sd
from threading import Thread
from recorder import recorder


listening = False

def toggle_listening():
    """Toggle the listening state."""
    global listening
    if listening:
        recorder.stop_recording()  # Stop capturing audio
        toggle_button.config(text="Start Listening", bg="#4CAF50")
        listening = False
    else:
        recorder.start_recording()  # Start capturing audio
        toggle_button.config(text="Stop Listening", bg="#F44336")
        listening = True

def save_audio():
    """Save the current buffer to a file."""
    if listening:
        recorder.save_last_buffer()
        record_button.config(text="Saved!", bg="#FFC107")
        app.after(2000, lambda: record_button.config(text="Record", bg="#EB5E28"))
    else:
        print("Not listening. Cannot save audio.")

def on_record_button_click():
    record_button.config(text="Saving audio...", bg="#FFC107")
    recorder.save_last_buffer()  # Save the last 4 minutes of audio
    record_button.config(text="Record", bg="#EB5E28")

# Function to get available microphones
def get_microphone_list():
    """Get the list of input-capable devices."""
    input_devices = sd.query_devices()
    devices = [device['name'] for device in input_devices if device['max_input_channels'] > 0]
    return devices

# Function to display selected microphone
def select_microphone(event):
    selected_microphone = mic_dropdown.get()
    device_list = sd.query_devices()
    for index, device in enumerate(device_list):
        if device['name'] == selected_microphone:
            recorder.set_microphone(index)
            break
    print(f"Selected Microphone: {selected_microphone}")

# Function to get loopback devices
def get_wasapi_devices():
    """Get the list of WASAPI devices for system audio (loopback)."""
    devices = sd.query_devices()
    wasapi_devices = [device['name'] for device in devices if device['hostapi'] == 1 and device['max_input_channels'] > 0]
    return wasapi_devices

# Function to display selected loopback device
def select_device(event):
    selected_device = wasapi_dropdown.get()
    device_list = sd.query_devices()
    for index, device in enumerate(device_list):
        if device['name'] == selected_device:
            recorder.set_system_audio(index)
            break
    print(f"Selected Audio Device: {selected_device}")

# Function to monitor audio levels
def update_level_meter(indata, frames, time, status):
    """Update the decibel meter based on real-time audio levels."""
    meter_value = np.linalg.norm(indata)  # Root mean square value
    meter.set(meter_value / 32768)  # Normalize to a range of 0.0 to 1.0


# Binding logic
def record_binding(event=None):
    global recording
    if recording:
        binding_button.config(text=f"Recorded: {event.keysym or event.type}")
        recording = False
    else:
        binding_button.config(text="Press any key or click to bind!")
        recording = True

def binding_event(event):
    if recording:
        binding_button.config(text=f"Bound to: {event.keysym if hasattr(event, 'keysym') else event.type}")

# Create main window
app = tk.Tk()
app.title("LoopBack")
app.geometry("800x300")  # Adjusted size for additional elements
app.resizable(False, False)  # Disable resizing
app.configure(bg="#252422")

# Initial state
recording = False

# Get devices
microphone_list = get_microphone_list()
wasapi_devices = get_wasapi_devices()

# MICROPHONE SELECTION
mic_label = tk.Label(app, text="Select Microphone:", bg="#252422", fg="#CCC5B9", anchor="w", font=("Inter", 12))
mic_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")

mic_dropdown = ttk.Combobox(app, values=microphone_list, state="readonly", width=50)
mic_dropdown.grid(row=0, column=1, padx=10, pady=10)
mic_dropdown.bind("<<ComboboxSelected>>", select_microphone)

# Decibel Meter for Microphone
meter = ttk.Progressbar(app, orient="horizontal", length=200, mode="determinate", maximum=1.0)
meter.grid(row=0, column=2, padx=10, pady=10)

# AUDIO DEVICE SELECTION
audio_device_label = tk.Label(app, text="Select Audio Device:", bg="#252422", fg="#CCC5B9", anchor="w", font=("Inter", 12))
audio_device_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

wasapi_dropdown = ttk.Combobox(app, values=wasapi_devices, state="readonly", width=50)
wasapi_dropdown.grid(row=1, column=1, padx=10, pady=10)
wasapi_dropdown.bind("<<ComboboxSelected>>", select_device)

# Decibel Meter for Audio Device
meter_audio = ttk.Progressbar(app, orient="horizontal", length=200, mode="determinate", maximum=1.0)
meter_audio.grid(row=1, column=2, padx=10, pady=10)

# RECORD BINDING
record_binding_label = tk.Label(app, text="Record Binding:", bg="#252422", fg="#CCC5B9", anchor="w", font=("Inter", 12))
record_binding_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

# Binding button
binding_button = tk.Button(app, text="Click to create binding", bg="#FFFCF2", anchor="w", font=("Arial", 8), command=record_binding, width=52, height=1)
binding_button.grid(row=2, column=1, padx=10, pady=10, sticky="w")

# Bind events
app.bind("<Key>", binding_event)

# Add Toggle Button for Listening
toggle_button = tk.Button(
    app,
    text="Start Listening",
    font=("Inter", 12),
    command=toggle_listening,
    bg="#4CAF50",
    fg="#FFFCF2",
    width=35,
)
toggle_button.grid(row=3, column=1, padx=10, pady=10, sticky="w")

# Record button
record_button = tk.Button(
    app,
    text="Record",
    font=("Inter", 12),
    command=save_audio,
    bg="#EB5E28",
    fg="#FFFCF2",
    width=35,
)
record_button.grid(row=4, column=1, padx=10, pady=10, sticky="w")

def on_closing():
    recorder.stop_recording()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

# Run the application
app.mainloop()

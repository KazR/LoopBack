import tkinter as tk
from tkinter import ttk
import sounddevice as sd

# Function to get available microphones
def get_microphone_list():
    input_devices = sd.query_devices()
    devices = [device['name'] for device in input_devices if device['max_input_channels'] > 0]
    return devices

# Function to display selected microphone
def select_microphone(event):
    selected_microphone = mic_dropdown.get()
    print(f"Selected Microphone: {selected_microphone}")

# Function to get loopback devices
def get_wasapi_devices():
    devices = sd.query_devices()
    # Filter to show only WASAPI devices (hostapi == 1 for WASAPI)
    wasapi_devices = [device['name'] for device in devices if device['hostapi'] == 1]
    return wasapi_devices

# Function to record audio
def on_record_button_click():
    selected_mic = mic_dropdown.get()
    selected_wasapi = wasapi_dropdown.get()

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
app.geometry("600x300")  # Adjusted size for additional elements
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

# AUDIO DEVICE SELECTION
audio_device_label = tk.Label(app, text="Select Audio Device:", bg="#252422", fg="#CCC5B9", anchor="w", font=("Inter", 12))
audio_device_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")

wasapi_dropdown = ttk.Combobox(app, values=wasapi_devices, state="readonly", width=50)
wasapi_dropdown.grid(row=1, column=1, padx=10, pady=10)
wasapi_dropdown.bind("<<ComboboxSelected>>", select_microphone)

# RECORD BINDING
record_binding_label = tk.Label(app, text="Record Binding:", bg="#252422", fg="#CCC5B9", anchor="w", font=("Inter", 12))
record_binding_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")

# Binding button
binding_button = tk.Button(app, text="Click to create binding", bg="#FFFCF2", anchor="w", font=("Arial", 8), command=record_binding, width=52, height=1)
binding_button.grid(row=2, column=1, padx=10, pady=10, sticky="w")

# Bind events
app.bind("<Key>", binding_event)

# RECORD BUTTON
record_button = tk.Button(app, text="Record", font=("Inter", 12), command=on_record_button_click, bg="#EB5E28", fg="#FFFCF2", width=35)
record_button.grid(row=3, column=1, padx=10, pady=10,sticky="w")

# Run the application
app.mainloop()

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

# Create main window
app = tk.Tk()
app.title("LoopBack")
app.geometry("600x200")  # Set size to 600x200 pixels
app.resizable(False, False)  # Disable resizing
app.configure(bg="#252422")

# Get devices
microphone_list = get_microphone_list()
wasapi_devices = get_wasapi_devices()

#MICROPHONE SELECTION
mic_label = tk.Label(app, text="Select Microphone:", bg="#252422", fg="#CCC5B9", anchor="w", font=("Inter", 12),)
mic_label.grid(row=0, column=0, padx=10, pady=10)

mic_dropdown = ttk.Combobox(app, values=microphone_list, state="readonly", width=50)
mic_dropdown.grid(row=0, column=1, padx=10, pady=10)
mic_dropdown.bind("<<ComboboxSelected>>", select_microphone)

#AUDIO DEVICE SELECTION
mic_label = tk.Label(app, text="Select Audio Device:", bg="#252422", fg="#CCC5B9", anchor="w", font=("Inter", 12))
mic_label.grid(row=1, column=0, padx=10, pady=10)

mic_dropdown = ttk.Combobox(app, values=microphone_list, state="readonly", width=50)
mic_dropdown.grid(row=1, column=1, padx=10, pady=10)
mic_dropdown.bind("<<ComboboxSelected>>", select_microphone)

#BINDING SELECTION
mic_label = tk.Label(app, text="Select Audio Device:", bg="#252422", fg="#CCC5B9", anchor="w", font=("Inter", 12))
mic_label.grid(row=1, column=0, padx=10, pady=10)

mic_dropdown = ttk.Combobox(app, values=wasapi_devices, state="readonly", width=50)
mic_dropdown.grid(row=1, column=1, padx=10, pady=10)
mic_dropdown.bind("<<ComboboxSelected>>", select_microphone)

# Run the application
app.mainloop()

import tkinter as tk
from tkinter import ttk
from logic import (
    toggle_listening,
    save_combined_recording,
    load_config,
    save_config,
    cleanup
)
from pynput import keyboard
import threading

# Fonts
title_font = ("Corbel", 24)
text_font = ("Corbel", 12)

# Load configuration
config = load_config()
record_binding = config.get("record_binding", "")

# Create main window
app = tk.Tk()
app.title("loopBack")
app.geometry("345x350")
app.resizable(False, False)
app.configure(bg="#252422")

# Global variables
current_keys = set()
listener = None

def update_status(message):
    # Need to use after() to update GUI from different thread
    app.after(0, lambda: _update_status_internal(message))

def _update_status_internal(message):
    status_box.config(state="normal")
    status_box.insert(tk.END, f"{message}\n")
    status_box.config(state="disabled")
    status_box.see(tk.END)

def on_press(key):
    try:
        # Convert key to string representation
        key_str = key.char if hasattr(key, 'char') else str(key)
        current_keys.add(key_str)
        
        # Check if the current combination matches the binding
        if record_binding and set(record_binding.strip('<>').split('+')) == current_keys:
            # Run the recording function in the main thread
            app.after(0, lambda: save_combined_recording(update_status))
    except AttributeError:
        pass

def on_release(key):
    try:
        key_str = key.char if hasattr(key, 'char') else str(key)
        current_keys.discard(key_str)
    except AttributeError:
        pass

def start_keyboard_listener():
    global listener
    listener = keyboard.Listener(on_press=on_press, on_release=on_release)
    listener.start()

def set_record_binding():
    update_status("Press a key combination to set as the record binding.")
    app.bind("<KeyPress>", capture_binding)

def capture_binding(event):
    global record_binding
    # Convert the key combination to a format that pynput can use
    record_binding = f"<{event.keysym}>"
    config["record_binding"] = record_binding
    save_config(config)
    update_binding_button()
    update_status(f"Record binding set to: {record_binding}")
    app.unbind("<KeyPress>")

def update_binding_button():
    binding_button.config(text=f"Binding: {record_binding or 'None'}")

# GUI Elements
MyLabel = tk.Label(app, text="loopBack", font=title_font, bg="#252422", fg="#FFFCF2")
MyLabel.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

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

toggle_button = tk.Button(
    app,
    text="Start Listening",
    font=text_font,
    bg="#EB5E28",
    fg="#FFFCF2",
    width=35,
    command=lambda: toggle_listening(toggle_button, update_status)
)
toggle_button.grid(row=3, column=1, padx=10, pady=10, sticky="nsew")

record_button = tk.Button(
    app,
    text="Record",
    font=text_font,
    bg="#EB5E28",
    fg="#FFFCF2",
    width=35,
    command=lambda: save_combined_recording(update_status)
)
record_button.grid(row=4, column=1, padx=10, pady=10, sticky="nsew")

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
    global listener
    if listener:
        listener.stop()
    cleanup()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

# Start the keyboard listener
start_keyboard_listener()

# Run the application
app.mainloop()
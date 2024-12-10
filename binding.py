# State for recording
recording = False
current_keys = set()

def start_recording():
    """Start recording key bindings."""
    global recording, current_keys
    recording = True
    current_keys.clear()

def stop_recording():
    """Stop recording and return the captured key combination."""
    global recording
    recording = False
    return " + ".join(sorted(current_keys)) if current_keys else None

def handle_key_press(event):
    """Handle a key press during recording."""
    global current_keys
    if recording:
        if event.keysym in ["Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R"]:
            # Normalize modifier keys
            current_keys.add(event.keysym.replace("_L", "").replace("_R", ""))
        else:
            current_keys.add(event.keysym)

def handle_key_release(event):
    """Handle a key release during recording."""
    global current_keys
    if recording and event.keysym in current_keys:
        current_keys.remove(event.keysym)

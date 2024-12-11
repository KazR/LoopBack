import pyaudio
import wave
import threading
from collections import deque
import time
import os
from datetime import datetime
import numpy as np

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BUFFER_SECONDS = 240  # 4 minutes
OUTPUT_DIR = "recordings"

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.mic_stream = None
        self.system_stream = None
        self.buffer = deque(maxlen=int(RATE / CHUNK * BUFFER_SECONDS))  # Circular buffer
        self.recording = False
        self.lock = threading.Lock()
        self.mic_device_index = None  # Selected microphone
        self.system_device_index = None  # System sound (loopback) device

        # Ensure the recordings directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def set_microphone(self, device_index):
        """Set the microphone input device index."""
        self.mic_device_index = device_index
        print(f"Microphone device set to index: {device_index}")

    def set_system_audio(self, device_index):
        """Set the system audio (loopback) device index."""
        self.system_device_index = device_index
        print(f"System audio device set to index: {device_index}")

    def start_recording(self):
        """Start recording from microphone and system audio."""
        self.mic_stream = self.audio.open(format=FORMAT,
                                          channels=CHANNELS,
                                          rate=RATE,
                                          input=True,
                                          input_device_index=self.mic_device_index,
                                          frames_per_buffer=CHUNK)
        
        self.system_stream = self.audio.open(format=FORMAT,
                                             channels=CHANNELS,
                                             rate=RATE,
                                             input=True,
                                             input_device_index=self.system_device_index,
                                             frames_per_buffer=CHUNK)
        
        self.recording = True
        threading.Thread(target=self._record_loop, daemon=True).start()

    def stop_recording(self):
        """Stop recording and close streams."""
        self.recording = False
        if self.mic_stream:
            self.mic_stream.stop_stream()
            self.mic_stream.close()
        if self.system_stream:
            self.system_stream.stop_stream()
            self.system_stream.close()
        self.audio.terminate()

    def _record_loop(self):
        """Record audio from both microphone and system audio."""
        while self.recording:
            mic_data = self.mic_stream.read(CHUNK, exception_on_overflow=False)
            system_data = self.system_stream.read(CHUNK, exception_on_overflow=False)

            # Mix the two audio streams
            mic_array = np.frombuffer(mic_data, dtype=np.int16)
            system_array = np.frombuffer(system_data, dtype=np.int16)
            mixed_array = mic_array + system_array  # Simple mixing
            mixed_data = mixed_array.astype(np.int16).tobytes()

            with self.lock:
                self.buffer.append(mixed_data)

    def _generate_filename(self):
        """Generate a unique filename for the recording."""
        date_str = datetime.now().strftime("%d%m%y")  # Format: DDMMYY
        existing_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(f"recording{date_str}")]
        number = len(existing_files) + 1
        return os.path.join(OUTPUT_DIR, f"recording{date_str}{number:02}.wav")

    def save_last_buffer(self):
        """Save the current buffer to a file and clear it afterward."""
        if not self.buffer:
            print("No audio data to save.")
            return

        filename = self._generate_filename()
        with self.lock:
            frames = list(self.buffer)
            self.buffer.clear()  # Clear the buffer after saving
        
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"Audio saved to {filename}")


recorder = AudioRecorder()

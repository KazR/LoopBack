import pyaudio
import wave
import threading
from collections import deque
import time
import os
from datetime import datetime

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
BUFFER_SECONDS = 240  # 4 minutes
OUTPUT_DIR = "recordings"

class AudioRecorder:
    def __init__(self):
        self.audio = pyaudio.PyAudio()
        self.stream = None
        self.buffer = deque(maxlen=int(RATE / CHUNK * BUFFER_SECONDS))  # Circular buffer
        self.recording = False
        self.lock = threading.Lock()

        # Ensure the recordings directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

    def start_recording(self):
        self.stream = self.audio.open(format=FORMAT,
                                      channels=CHANNELS,
                                      rate=RATE,
                                      input=True,
                                      frames_per_buffer=CHUNK)
        self.recording = True
        threading.Thread(target=self._record_loop, daemon=True).start()

    def stop_recording(self):
        self.recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        self.audio.terminate()

    def _record_loop(self):
        while self.recording:
            data = self.stream.read(CHUNK, exception_on_overflow=False)
            with self.lock:
                self.buffer.append(data)

    def _generate_filename(self):
        date_str = datetime.now().strftime("%d%m%y")  # Format: DDMMYY
        existing_files = [f for f in os.listdir(OUTPUT_DIR) if f.startswith(f"recording{date_str}")]
        number = len(existing_files) + 1
        return os.path.join(OUTPUT_DIR, f"recording{date_str}{number:02}.wav")

    def save_last_buffer(self):
        filename = self._generate_filename()
        with self.lock:
            frames = list(self.buffer)
        wf = wave.open(filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        print(f"Audio saved to {filename}")

recorder = AudioRecorder()

import pyaudio
import wave
import os
from datetime import datetime
from collections import deque

CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
RECORD_SECONDS = 5
BUFFER_SECONDS = 240  # 4 minutes
MAX_FRAMES = BUFFER_SECONDS * RATE // CHUNK

# Circular buffer to hold the last 4 minutes of audio
audio_buffer = deque(maxlen=MAX_FRAMES)

p = pyaudio.PyAudio()

# Start the audio stream
stream = p.open(format=FORMAT,
                channels=CHANNELS,
                rate=RATE,
                input=True,
                frames_per_buffer=CHUNK)

print("* recording")
try:
    for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        audio_buffer.append(data)

    print("* done recording")

    # Ensure the 'recordings' directory exists
    recordings_dir = "recordings"
    os.makedirs(recordings_dir, exist_ok=True)

    # Generate the filename dynamically
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

    # Save to the generated filename
    with wave.open(filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(audio_buffer))

    print(f"Recording saved as {filename}")

finally:
    stream.stop_stream()
    stream.close()
    p.terminate()

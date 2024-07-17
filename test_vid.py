import threading
import subprocess
from PIL import ImageGrab
import numpy as np
import cv2
import pyautogui
import sounddevice as sd
import soundfile as sf
import time
from pynput import keyboard, mouse
import queue
import os

# Parameters for audio recording
samplerate = 44100  # Hertz
channels = 2  # Typically, system audio will have 2 channels (stereo)
device_index = None  # We'll determine this dynamically

stop_event = threading.Event()

# Duration for each segment in seconds
segment_duration = 5

# Output filenames
output_audio_file = 'output_audio.wav'
output_video_file = 'output_video.mp4'
output_events_file = 'output_events.txt'

# Buffers for audio, video, and events
audio_buffer = queue.Queue()
video_buffer = queue.Queue()
event_buffer = queue.Queue()

# Function to find the virtual audio device index
def find_device_index(device_name):
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device_name in device['name']:
            return i
    return None

# Function to record audio
def record_audio():
    try:
        with sd.InputStream(samplerate=samplerate, channels=channels, device=device_index) as stream:
            while not stop_event.is_set():
                start_time = time.time()
                audio_data = []
                while time.time() - start_time < segment_duration and not stop_event.is_set():
                    data, overflowed = stream.read(1024)
                    audio_data.append(data)
                if audio_data:
                    audio_buffer.put(audio_data)
    except Exception as e:
        print(f"Error recording audio: {e}")

def write_audio():
    with sf.SoundFile(output_audio_file, mode='w', samplerate=samplerate, channels=channels) as file:
        while not stop_event.is_set() or not audio_buffer.empty():
            if not audio_buffer.empty():
                audio_data = audio_buffer.get()
                for data in audio_data:
                    file.write(data)
                print('Written audio segment')
            time.sleep(1)

# Function to record video
def record_video():
    SCREEN_SIZE = pyautogui.size()
    while not stop_event.is_set():
        start_time = time.time()
        video_data = []
        while time.time() - start_time < segment_duration and not stop_event.is_set():
            try:
                img = ImageGrab.grab(bbox=(0, 0, SCREEN_SIZE.width, SCREEN_SIZE.height))
                img_np = np.array(img)
                img_final = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
                video_data.append(img_final)
            except Exception as e:
                print(f"Error capturing screen: {e}")
                break
        if video_data:
            video_buffer.put(video_data)
        print('Captured video segment')

def write_video():
    SCREEN_SIZE = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 3
    captured = cv2.VideoWriter(output_video_file, fourcc, fps, (SCREEN_SIZE.width, SCREEN_SIZE.height))

    while not stop_event.is_set() or not video_buffer.empty():
        if not video_buffer.empty():
            video_data = video_buffer.get()
            for frame in video_data:
                captured.write(frame)
            print('Written video segment')
        time.sleep(1)

    captured.release()
    print("Video recording stopped.")

# Function to log system events
def log_system_events():
    event_list = []

    def on_press(key):
        event_list.append(f'{time.time()} - Key pressed: {key}\n')

    def on_click(x, y, button, pressed):
        event_list.append(f'{time.time()} - Mouse {"pressed" if pressed else "released"} at ({x}, {y}) with {button}\n')

    with keyboard.Listener(on_press=on_press) as k_listener, mouse.Listener(on_click=on_click) as m_listener:
        while not stop_event.is_set():
            start_time = time.time()
            while time.time() - start_time < segment_duration and not stop_event.is_set():
                time.sleep(0.1)  # Sleep to prevent busy-waiting

            if event_list:
                event_buffer.put(event_list)
                event_list = []

def write_events():
    while not stop_event.is_set() or not event_buffer.empty():
        if not event_buffer.empty():
            events = event_buffer.get()
            with open(output_events_file, 'a') as f:
                for event in events:
                    f.write(event)
                print('Written event segment')
        time.sleep(1)

if __name__ == "__main__":
    device_index = find_device_index("BlackHole")  # Change this to the name of your virtual audio device

    if device_index is None:
        print("Virtual audio device not found. Ensure BlackHole or Soundflower is installed and set up correctly.")
    else:
        try:
            # Start recording threads
            video_thread = threading.Thread(target=record_video)
            audio_thread = threading.Thread(target=record_audio)
            events_thread = threading.Thread(target=log_system_events)

            audio_writer_thread = threading.Thread(target=write_audio)
            video_writer_thread = threading.Thread(target=write_video)
            events_writer_thread = threading.Thread(target=write_events)

            video_thread.start()
            audio_thread.start()
            events_thread.start()

            audio_writer_thread.start()
            video_writer_thread.start()
            events_writer_thread.start()

            # Wait for user to stop recording
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("Program interrupted.")
            stop_event.set()

            # Stop threads
            video_thread.join()
            audio_thread.join()
            events_thread.join()

            audio_writer_thread.join()
            video_writer_thread.join()
            events_writer_thread.join()

            print("Recording stopped.")
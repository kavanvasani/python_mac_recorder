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

# Parameters for audio recording
samplerate = 44100  # Hertz
channels = 2  # Typically, system audio will have 2 channels (stereo)
output_audio_file = 'output_audio.wav'
output_video_file = 'output.mp4'
output_combined_file = 'output_combined.mp4'
output_events_file = 'output_events.txt'
device_index = None  # We'll determine this dynamically

stop_event = threading.Event()

# Find the virtual audio device index
def find_device_index(device_name):
    devices = sd.query_devices()
    for i, device in enumerate(devices):
        if device_name in device['name']:
            return i
    return None

# Function to record audio
def record_audio():
    try:
        with sf.SoundFile(output_audio_file, mode='w', samplerate=samplerate, channels=channels) as file:
            print("Recording audio... Press Ctrl+C to stop.")
            with sd.InputStream(samplerate=samplerate, channels=channels, device=device_index) as stream:
                while not stop_event.is_set():
                    data, overflowed = stream.read(1024)
                    file.write(data)
    except Exception as e:
        print(f"Error recording audio: {e}")

# Function to record video
def record_video():
    SCREEN_SIZE = pyautogui.size()
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = 3
    captured = cv2.VideoWriter(output_video_file, fourcc, fps, (SCREEN_SIZE.width, SCREEN_SIZE.height))

    print("Recording video...")
    last_time = time.time()
    while not stop_event.is_set():
        try:
            # Capture the screen
            img = ImageGrab.grab(bbox=(0, 0, SCREEN_SIZE.width, SCREEN_SIZE.height))
            img_np = np.array(img)
            img_final = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            captured.write(img_final)
            
            # # Sleep to maintain the target frame rate
            # elapsed_time = time.time() - last_time
            # time_to_wait = max(0, (1 / fps) - elapsed_time)
            # time.sleep(time_to_wait)
            # last_time = time.time()
        except Exception as e:
            print(f"Error capturing screen: {e}")
            break

    captured.release()
    print("Video recording stopped.")

# Function to log system events
def log_system_events():
    def on_press(key):
        with open(output_events_file, 'a') as f:
            f.write(f'{time.time()} - Key pressed: {key}\n')

    def on_click(x, y, button, pressed):
        with open(output_events_file, 'a') as f:
            f.write(f'{time.time()} - Mouse {"pressed" if pressed else "released"} at ({x}, {y}) with {button}\n')

    with keyboard.Listener(on_press=on_press) as k_listener, mouse.Listener(on_click=on_click) as m_listener:
        k_listener.join()
        m_listener.join()

# Function to merge audio and video
def merge_audio_video():
    try:
        subprocess.call(['ffmpeg', '-i', output_video_file, '-i', output_audio_file, '-c:v', 'copy', '-c:a', 'aac', output_combined_file])
        print("Audio and video merged.")
    except FileNotFoundError:
        print("ffmpeg not found. Please install ffmpeg and ensure it's in the system PATH.")
    except Exception as e:
        print(f"Error merging audio and video: {e}")

if __name__ == "__main__":
    device_index = find_device_index("BlackHole")  # Change this to the name of your virtual audio device

    if device_index is None:
        print("Virtual audio device not found. Ensure BlackHole or Soundflower is installed and set up correctly.")
    else:
        try:
            # Start audio, video, and event recording threads
            video_thread = threading.Thread(target=record_video)
            audio_thread = threading.Thread(target=record_audio)
            events_thread = threading.Thread(target=log_system_events)

            video_thread.start()
            audio_thread.start()
            events_thread.start()

            # Wait for user to stop recording
            while True:
                print('kavan')
                time.sleep(1)
        except KeyboardInterrupt:
            print("Program interrupted.")
            stop_event.set()

            # Stop threads
            video_thread.join()
            audio_thread.join()
            events_thread.join()

            print("Recording stopped. Merging audio and video...")
            merge_audio_video()
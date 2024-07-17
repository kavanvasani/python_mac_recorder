# import threading
# import subprocess
# from PIL import ImageGrab
# import numpy as np
# import cv2
# import pyautogui
# import sounddevice as sd
# import soundfile as sf
# import time
# from datetime import datetime
# import os
# from pynput import keyboard, mouse

# # Parameters for audio recording
# samplerate = 44100  # Hertz
# channels = 2  # Typically, system audio will have 2 channels (stereo)
# output_audio_file_prefix = 'buffer_audio'
# output_video_file_prefix = 'buffer_video'
# output_combined_file_prefix = 'output_combined'
# output_events_file_prefix = 'buffer_events'
# device_index = None  # We'll determine this dynamically

# stop_event = threading.Event()
# buffer_switch_event = threading.Event()
# start_event = threading.Event()
# chunk_duration = 10  # seconds

# # Find the virtual audio device index
# def find_device_index(device_name):
#     devices = sd.query_devices()
#     for i, device in enumerate(devices):
#         if device_name in device['name']:
#             return i
#     return None

# # Function to record audio in chunks with double buffering
# def record_audio():
#     buffer_size = int(samplerate * chunk_duration)
#     buffer1 = np.zeros((buffer_size, channels), dtype='float32')
#     buffer2 = np.zeros((buffer_size, channels), dtype='float32')
#     active_buffer = buffer1
#     buffer_index = 0

#     with sd.InputStream(samplerate=samplerate, channels=channels, device=device_index) as stream:
#         start_event.wait()  # Wait for the signal to start recording
#         while not stop_event.is_set():
#             buffer_switch_event.wait()
#             buffer_switch_event.clear()
#             timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#             for i in range(buffer_size // 1024):
#                 if stop_event.is_set():
#                     break
#                 data, overflowed = stream.read(1024)
#                 active_buffer[buffer_index:buffer_index + len(data)] = data
#                 buffer_index += len(data)

#             # Write the completed buffer to file
#             output_audio_file = f"{output_audio_file_prefix}_{timestamp}.wav"
#             with sf.SoundFile(output_audio_file, mode='w', samplerate=samplerate, channels=channels) as file:
#                 file.write(active_buffer[:buffer_index])

#             active_buffer = buffer1 if active_buffer is buffer2 else buffer2
#             buffer_index = 0

# # Function to record video in chunks with double buffering
# def record_video():
#     SCREEN_SIZE = pyautogui.size()
#     fps = 3
#     frame_count = int(chunk_duration * fps)
#     buffer1 = []
#     buffer2 = []
#     active_buffer = buffer1

#     start_event.wait()  # Wait for the signal to start recording
#     while not stop_event.is_set():
#         buffer_switch_event.wait()
#         buffer_switch_event.clear()
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
#         last_time = time.time()
#         for _ in range(frame_count):
#             if stop_event.is_set():
#                 break
#             img = ImageGrab.grab(bbox=(0, 0, SCREEN_SIZE.width, SCREEN_SIZE.height))
#             img_np = np.array(img)
#             img_final = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
#             active_buffer.append(img_final)

#             elapsed_time = time.time() - last_time
#             time_to_wait = max(0, (1 / fps) - elapsed_time)
#             time.sleep(time_to_wait)
#             last_time = time.time()

#         # Write the completed buffer to file
#         output_video_file = f"{output_video_file_prefix}_{timestamp}.mp4"
#         fourcc = cv2.VideoWriter_fourcc(*'mp4v')
#         video_writer = cv2.VideoWriter(output_video_file, fourcc, fps, (SCREEN_SIZE.width, SCREEN_SIZE.height))
#         for frame in active_buffer:
#             video_writer.write(frame)
#         video_writer.release()

#         active_buffer.clear()
#         active_buffer = buffer1 if active_buffer is buffer2 else buffer2

# # Function to log system events in chunks with double buffering
# def log_system_events():
#     buffer1 = []
#     buffer2 = []
#     active_buffer = buffer1

#     def on_press(key):
#         active_buffer.append(f'{time.time()} - Key pressed: {key}\n')

#     def on_click(x, y, button, pressed):
#         active_buffer.append(f'{time.time()} - Mouse {"pressed" if pressed else "released"} at ({x}, {y}) with {button}\n')

#     k_listener = keyboard.Listener(on_press=on_press)
#     m_listener = mouse.Listener(on_click=on_click)
#     k_listener.start()
#     m_listener.start()

#     start_event.wait()  # Wait for the signal to start recording
#     while not stop_event.is_set():
#         buffer_switch_event.wait()
#         buffer_switch_event.clear()
#         timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

#         # Write the completed buffer to file
#         output_events_file = f"{output_events_file_prefix}_{timestamp}.txt"
#         with open(output_events_file, 'w') as f:
#             f.writelines(active_buffer)

#         active_buffer.clear()
#         active_buffer = buffer1 if active_buffer is buffer2 else buffer2

#     k_listener.stop()
#     m_listener.stop()
#     print("Event logging stopped.")

# # Function to merge audio and video
# def merge_audio_video():
#     try:
#         video_files = sorted([f for f in os.listdir() if f.startswith(output_video_file_prefix)])
#         audio_files = sorted([f for f in os.listdir() if f.startswith(output_audio_file_prefix)])

#         for video_file, audio_file in zip(video_files, audio_files):
#             timestamp = video_file[len(output_video_file_prefix) + 1:-4]
#             output_combined_file = f"{output_combined_file_prefix}_{timestamp}.mp4"
#             subprocess.call(['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', output_combined_file])
#         print("Audio and video merged.")
#     except FileNotFoundError:
#         print("ffmpeg not found. Please install ffmpeg and ensure it's in the system PATH.")
#     except Exception as e:
#         print(f"Error merging audio and video: {e}")

# # Central timer function to synchronize buffer switches
# def central_timer():
#     start_event.set()  # Signal all threads to start recording
#     while not stop_event.is_set():
#         time.sleep(chunk_duration)
#         buffer_switch_event.set()

# if __name__ == "__main__":
#     device_index = find_device_index("BlackHole")  # Change this to the name of your virtual audio device

#     if device_index is None:
#         print("Virtual audio device not found. Ensure BlackHole or Soundflower is installed and set up correctly.")
#     else:
#         try:
#             # Start audio, video, and event recording threads
#             video_thread = threading.Thread(target=record_video)
#             audio_thread = threading.Thread(target=record_audio)
#             events_thread = threading.Thread(target=log_system_events)
#             timer_thread = threading.Thread(target=central_timer)

#             video_thread.start()
#             audio_thread.start()
#             events_thread.start()
#             timer_thread.start()

#             # Wait for user to stop recording
#             while True:
#                 time.sleep(1)
#                 print('kavan')
#         except KeyboardInterrupt:
#             print("Program interrupted.")
#             stop_event.set()

#             # Stop threads
#             video_thread.join()
#             audio_thread.join()
#             events_thread.join()
#             timer_thread.join()

#             print("Recording stopped. Merging audio and video...")
#             merge_audio_video()

import cv2
import pyaudio
import wave
import threading
import time
import subprocess
import os

class VideoRecorder():
    def __init__(self):
        self.open = True
        self.device_index = 0
        self.fps = 6
        self.fourcc = "MJPG"
        self.frameSize = (640,480)
        self.video_filename = "temp_video.avi"
        self.video_cap = cv2.VideoCapture(self.device_index)
        self.video_writer = cv2.VideoWriter_fourcc(*self.fourcc)
        self.video_out = cv2.VideoWriter(self.video_filename, self.video_writer, self.fps, self.frameSize)
        self.frame_counts = 0
        self.start_time = time.time()

    def record(self):
        while self.open:
            ret, video_frame = self.video_cap.read()
            if ret:
                self.video_out.write(video_frame)
                self.frame_counts += 1
                time.sleep(1.0 / self.fps)
            else:
                break

    def stop(self):
        if self.open:
            self.open = False
            self.video_out.release()
            self.video_cap.release()
            cv2.destroyAllWindows()

    def start(self):
        video_thread = threading.Thread(target=self.record)
        video_thread.start()

class AudioRecorder():
    def __init__(self):
        self.open = True
        self.rate = 44100
        self.frames_per_buffer = 1024
        self.channels = 2
        self.format = pyaudio.paInt16
        self.audio_filename = "temp_audio.wav"
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(format=self.format,
                                      channels=self.channels,
                                      rate=self.rate,
                                      input=True,
                                      frames_per_buffer=self.frames_per_buffer)
        self.audio_frames = []

    def record(self):
        self.stream.start_stream()
        while self.open:
            data = self.stream.read(self.frames_per_buffer)
            self.audio_frames.append(data)
            if not self.open:
                break

    def stop(self):
        if self.open:
            self.open = False
            self.stream.stop_stream()
            self.stream.close()
            self.audio.terminate()
            waveFile = wave.open(self.audio_filename, 'wb')
            waveFile.setnchannels(self.channels)
            waveFile.setsampwidth(self.audio.get_sample_size(self.format))
            waveFile.setframerate(self.rate)
            waveFile.writeframes(b''.join(self.audio_frames))
            waveFile.close()

    def start(self):
        audio_thread = threading.Thread(target=self.record)
        audio_thread.start()

def start_AVrecording(filename):
    global video_thread
    global audio_thread

    video_thread = VideoRecorder()
    audio_thread = AudioRecorder()

    audio_thread.start()
    video_thread.start()

    return filename

def stop_AVrecording(filename):
    audio_thread.stop()
    frame_counts = video_thread.frame_counts
    elapsed_time = time.time() - video_thread.start_time
    recorded_fps = frame_counts / elapsed_time

    video_thread.stop()

    while threading.active_count() > 1:
        time.sleep(1)

    if abs(recorded_fps - 6) >= 0.01:
        cmd = f"ffmpeg -r {recorded_fps} -i temp_video.avi -pix_fmt yuv420p -r 6 temp_video2.avi"
        subprocess.call(cmd, shell=True)
        cmd = f"ffmpeg -ac 2 -channel_layout stereo -i temp_audio.wav -i temp_video2.avi -pix_fmt yuv420p {filename}.avi"
        subprocess.call(cmd, shell=True)
    else:
        cmd = f"ffmpeg -ac 2 -channel_layout stereo -i temp_audio.wav -i temp_video.avi -pix_fmt yuv420p {filename}.avi"
        subprocess.call(cmd, shell=True)

def file_manager(filename):
    local_path = os.getcwd()
    for temp_file in ["temp_audio.wav", "temp_video.avi", "temp_video2.avi", f"{filename}.avi"]:
        temp_file_path = os.path.join(local_path, temp_file)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

if __name__ == "__main__":
    filename = "Default_user"
    file_manager(filename)
    start_AVrecording(filename)
    time.sleep(10)
    stop_AVrecording(filename)
    print("Done")
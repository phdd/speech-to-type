import argparse
import numpy as np
import speech_recognition as sr
import whisper
import torch
import notify2
import subprocess

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
import pyperclip

def send_notification(title, message, timeout=5000, action_callback=None, persistent=False):
    notify2.init("Speech To Text")
    n = notify2.Notification(title, message)
    if persistent:
        n.set_timeout(notify2.EXPIRES_NEVER)
    else:
        n.set_timeout(timeout)
    if action_callback:
        n.add_action("stop", "Stop", action_callback)
    n.show()
    return n

def type_text(text):
    subprocess.run(["xdotool", "type", text])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large"], help="Model to use")
    parser.add_argument("--energy_threshold", default=1000, type=int, help="Energy level for mic to detect.")
    parser.add_argument("--phrase_timeout", default=2.0, type=float, help="Timeout to end a phrase.")
    args = parser.parse_args()

    initial_prompt = """
    Beachte bei der Transkription folgende Eigennamen von Orten, Firmen und Personen:

    - ConnCons
    - VIPFluid
    - Cancilico
    """

    data_queue = Queue()
    recorder = sr.Recognizer()
    recorder.energy_threshold = args.energy_threshold
    recorder.dynamic_energy_threshold = False

    source = sr.Microphone(sample_rate=16000)
    
    loading_notification = send_notification("Lade das Modell", "Bitte warten...")
    model = whisper.load_model(args.model)
    loading_notification.close()

    transcription = ""
    stop_recording = False

    def stop_callback(n, action):
        nonlocal stop_recording
        stop_recording = True
        n.close()

    ready_notification = send_notification("Modell geladen", "Sprich!", timeout=0, action_callback=stop_callback, persistent=True)

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData):
        if not stop_recording:
            data_queue.put(audio.get_raw_data())

    recorder.listen_in_background(source, record_callback, phrase_time_limit=None)

    while not stop_recording:
        if not data_queue.empty():
            audio_data = b''.join(data_queue.queue)
            data_queue.queue.clear()

            audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
            result = model.transcribe(audio_np, fp16=torch.cuda.is_available(), initial_prompt=initial_prompt)
            text = result['text'].strip()

            transcription += " " + text
            print(text)
        else:
            sleep(0.5)

    ready_notification.close()

if __name__ == "__main__":
    main()

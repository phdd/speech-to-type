import argparse
import numpy as np
import speech_recognition as sr
import whisper
import torch

from datetime import datetime, timedelta
from queue import Queue
from time import sleep
import pyperclip

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="medium", choices=["tiny", "base", "small", "medium", "large"], help="Model to use")
    parser.add_argument("--energy_threshold", default=1000, type=int, help="Energy level for mic to detect.")
    parser.add_argument("--phrase_timeout", default=2.0, type=float, help="Timeout to end a phrase.")
    args = parser.parse_args()

    phrase_time = None
    data_queue = Queue()
    recorder = sr.Recognizer()

    recorder.energy_threshold = args.energy_threshold
    recorder.dynamic_energy_threshold = False

    source = sr.Microphone(sample_rate=16000)
    model = whisper.load_model(args.model)
    transcription = ""

    with source:
        recorder.adjust_for_ambient_noise(source)

    def record_callback(_, audio: sr.AudioData):
        data_queue.put(audio.get_raw_data())

    recorder.listen_in_background(source, record_callback, phrase_time_limit=None)
    print("Listening...")

    while True:
        try:
            now = datetime.now()
            if not data_queue.empty():
                audio_data = b''.join(data_queue.queue)
                data_queue.queue.clear()

                audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                result = model.transcribe(audio_np, fp16=torch.cuda.is_available())
                text = result['text'].strip()

                if phrase_time and now - phrase_time > timedelta(seconds=args.phrase_timeout):
                    transcription = text
                else:
                    transcription += " " + text

                phrase_time = now
                pyperclip.copy(transcription.strip())
                print(f"{transcription.strip()}")
            else:
                sleep(0.1)
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    main()

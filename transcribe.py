import re
import sys
import gi
from pynput import keyboard

gi.require_version('Notify', '0.7')
gi.require_version('Gtk', '4.0')

from gi.repository import Notify, Gtk, GLib

import numpy as np
import speech_recognition as sr
import whisper
import torch
import subprocess

model_name = "medium"
energy_threshold = 800
initial_prompt = """
Beachte bei der Transkription folgende Eigennamen von Orten, Firmen und Personen:

- ConnCons
- VIPFluid
- Cancilico
- Dima
- Stefan
- Karsten
- Raphael
- sit.institute
- SageDocs
- Fog
- n8n
- Grafana
- Supabase
- Manga-Wiki
- Mautic
- PostHog
- LangGraph
- CrewAI
- RAG
- SaxMS
- Behdark
- arc42
- ChatGPT
- Qonto
- Herr Walther
- SKONTI
- Construct X
- Figma
"""

def type_text(text):
    # Remove control characters and non-spoken symbols
    filtered_text = re.sub(r'[^\w\s.,!?-]', '', text) 
    subprocess.run(["xdotool", "type", filtered_text.strip() + " "])

class SpeechToText(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.github.phdd.SpeechToText")
        self.loop = None  # Main loop reference
        self.recording = False  # State to track if recording is active
        self.listener = None  # Keyboard listener reference

    def stop(self, notification, action, user_data=None):
        print("stop")
        if self.listener:
            self.listener.stop()  # Stop the keyboard listener
        self.loop.quit()

    def start_recording(self):
        if not self.recording:
            self.recording = True
            self.notification.update
            print("Recording started")

    def stop_recording(self):
        if self.recording:
            self.recording = False
            print("Recording stopped")

    def on_press(self, key):
        try:
            if key == keyboard.Key.ctrl:  # Check if the Ctrl key is pressed
                self.start_recording()
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if key == keyboard.Key.ctrl:
                self.stop_recording()
        except AttributeError:
            pass

    def do_activate(self):
        print("do_activate")
        Notify.init('Speech to Text')
        self.loop = GLib.MainLoop() 

        self.notification = Notify.Notification.new("Model laden", "Bitte warte einen Moment")
        self.notification.set_urgency(Notify.Urgency.CRITICAL)
        self.notification.show()

        recorder = sr.Recognizer()
        recorder.energy_threshold = energy_threshold
        recorder.dynamic_energy_threshold = False

        source = sr.Microphone(sample_rate=16000)
        model = whisper.load_model(model_name)
        self.notification.close()

        self.notification = Notify.Notification.new("Modell geladen", "Halte <Strg> gedrückt, um aufzunehmen")
        self.notification.set_urgency(Notify.Urgency.CRITICAL)
        self.notification.set_timeout(Notify.EXPIRES_NEVER)
        self.notification.add_action("stop", "Stop", self.stop)
        self.notification.show()

        with source:
            recorder.adjust_for_ambient_noise(source)

        def record_callback(_, audio: sr.AudioData):
            if not self.recording:
                return

            print("record_callback")
            audio_np = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
            result = model.transcribe(audio_np, fp16=torch.cuda.is_available(), initial_prompt=initial_prompt)
            text = result['text'].strip()

            if len(text) > 10:
                type_text(f"{text} ")

        recorder.listen_in_background(source, record_callback, phrase_time_limit=None)

        # Start the keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

        self.loop.run()

app = SpeechToText()
app.run(sys.argv)
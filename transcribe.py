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
- Ullersdorf
- Löbtau
- Vaadin
"""

def type_text(text):
    # Remove control characters and non-spoken symbols
    filtered_text = re.sub(r'[^\w\s.,!?-]', '', text) 
    result = subprocess.run(
        ["xdotool", "type", "--clearmodifiers", filtered_text.strip() + " "],
        capture_output=True,
        text=True
    )
    print(result.stdout)

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
            self.notification.update("Aufnahme", "gestartet")
            self.notification.show()

    def stop_recording(self):
        if self.recording:
            self.recording = False
            self.notification.update("Aufnahme", "beendet")
            self.notification.show()

    def on_press(self, key):
        try:
            if key == keyboard.Key.f2:  # Check if the F2 key is pressed
                self.start_recording()
        except AttributeError:
            pass

    def on_release(self, key):
        try:
            if key == keyboard.Key.f2:
                self.stop_recording()
        except AttributeError:
            pass

    def do_activate(self):
        print("do_activate")
        Notify.init('Speech to Text')
        self.loop = GLib.MainLoop() 

        self.notification = Notify.Notification.new("Initialisierung", "Bitte warte einen Moment")
        self.notification.set_urgency(Notify.Urgency.CRITICAL)
        self.notification.show()

        recorder = sr.Recognizer()
        recorder.energy_threshold = energy_threshold
        recorder.dynamic_energy_threshold = False

        source = sr.Microphone(sample_rate=16000)
        try:
            model = whisper.load_model(model_name)
        except Exception as e:
            self.notification.update("Fehler", f"Modell konnte nicht geladen werden: {e}")
            self.notification.show()
            print(f"Fehler beim Laden des Modells: {e}")
            sys.exit(1)
        self.notification.close()

        self.notification = Notify.Notification.new("Bereitschaft", "Halte 'F2' gedrückt, dann hör ich zu.")
        self.notification.set_urgency(Notify.Urgency.CRITICAL)
        self.notification.set_timeout(Notify.EXPIRES_NEVER)
        self.notification.add_action("stop", "Beenden", self.stop)
        self.notification.show()

        with source:
            recorder.adjust_for_ambient_noise(source)

        def record_callback(_, audio: sr.AudioData):
            if not self.recording:
                return

            self.notification.update("Aufnahme", "verarbeiten")
            self.notification.show()

            audio_np = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
            result = model.transcribe(audio_np, fp16=torch.cuda.is_available(), initial_prompt=initial_prompt)
            text = result['text'].strip()

            if len(text) > 10:
                type_text(f"{text} ")

            self.notification.update("Bereitschaft", "Halte 'F2' gedrückt, dann hör ich zu.")
            self.notification.show()

        recorder.listen_in_background(source, record_callback, phrase_time_limit=None)

        # Start the keyboard listener
        self.listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        self.listener.start()

        self.loop.run()

app = SpeechToText()
app.run(sys.argv)
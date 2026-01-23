import re
import sys
import gi

gi.require_version('Notify', '0.7')
gi.require_version('Gtk', '4.0')

from gi.repository import Notify, Gtk, GLib

import numpy as np
import speech_recognition as sr
import whisper
import torch
import subprocess

model_name = "medium"
energy_threshold = 200
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
- siti
- SageDocs
- Fog
- n8n
- Grafana
- Supabase
- Manga-Wiki
- Mautic
- PostHog
- LangChain
- LangGraph
- CrewAI
- RAG
- SaxMS
- Behdark
- arc42
- ChatGPT
- Qonto
- Herr Walther
- Heisig
- SKONTI
- Construct X
- Figma
- Ullersdorf
- Löbtau
- Vaadin
- Flowise
- Nuxt
- OpenAPI
- Huey
- FastAPI
- Bearer
- Ullersdorf
- Hoyerswerda
- Highsick
- Langfuse
- Ollama
- Jirka
- Onctopus
- Sybille
"""

def type_text(text):
    # Remove control characters and non-spoken symbols
    filtered_text = re.sub(r'[^\w\s.,!?-]', '', text) 
    filtered_text = filtered_text.replace("Demokraten- ", "")
    subprocess.run(["setxkbmap", "de"])
    subprocess.run(["xdotool", "type", "--clearmodifiers", filtered_text.strip() + " "])

class SpeechToText(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.github.phdd.SpeechToText")
        self.loop = None  # Main loop reference

    def stop(self, notification, action, user_data=None):
        if self.loop:
            self.loop.quit()

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

        self.notification = Notify.Notification.new("Bereitschaft", "Ich höre zu")
        self.notification.add_action("stop", "Beenden", self.stop)
        self.notification.show()

        with source:
            recorder.adjust_for_ambient_noise(source)

        def record_callback(_, audio: sr.AudioData):
            self.notification.update("Aufnahme", "verarbeiten")
            self.notification.show()

            audio_np = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
            result = model.transcribe(audio_np, fp16=torch.cuda.is_available(), initial_prompt=initial_prompt)
            text = result['text']
            if isinstance(text, list):
                text = ' '.join(str(t) for t in text)
            text = str(text).strip()

            if len(text) > 10:
                type_text(f"{text} ")

            self.notification.update("Bereitschaft", "Ich höre zu")
            self.notification.show()

        recorder.listen_in_background(source, record_callback, phrase_time_limit=None)

        self.loop.run()

app = SpeechToText()
app.run(sys.argv)
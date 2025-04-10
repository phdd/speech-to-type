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

    def stop(self, notification, action, user_data=None):
        print("stop")
        self.loop.quit()

    def do_activate(self):
        print("do_activate")
        Notify.init('Speech to Text')
        self.loop = GLib.MainLoop() 

        notification = Notify.Notification.new("Model laden", "Bitte warte einen Moment")
        notification.set_urgency(Notify.Urgency.CRITICAL)
        notification.show()

        recorder = sr.Recognizer()
        recorder.energy_threshold = energy_threshold
        recorder.dynamic_energy_threshold = False

        source = sr.Microphone(sample_rate=16000)
        model = whisper.load_model(model_name)
        notification.close()

        notification = Notify.Notification.new("Modell geladen", "Sprich!")
        notification.set_urgency(Notify.Urgency.CRITICAL)
        notification.set_timeout(Notify.EXPIRES_NEVER)
        notification.add_action("stop", "Stop", self.stop)
        notification.show()

        with source:
            recorder.adjust_for_ambient_noise(source)

        def record_callback(_, audio: sr.AudioData):
            print("record_callback")
            audio_np = np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32) / 32768.0
            result = model.transcribe(audio_np, fp16=torch.cuda.is_available(), initial_prompt=initial_prompt)
            text = result['text'].strip()

            if len(text) > 10:
                type_text(f"{text} ")
            # print(f"Transkription: {text}")

        recorder.listen_in_background(source, record_callback, phrase_time_limit=None)
        self.loop.run()

app = SpeechToText()
app.run(sys.argv)
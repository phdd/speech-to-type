import re
import sys
import gi
import torch
import ctypes
import ctypes.util
import threading

gi.require_version("Notify", "0.7")
gi.require_version("Gtk", "4.0")

from gi.repository import Notify, Gtk, GLib

import numpy as np
import speech_recognition as sr
import whisper
import subprocess

from silero_vad import load_silero_vad, VADIterator

# Konfiguration
model_name = "medium"
DEBUG = False  # Debug-Ausgaben aktivieren/deaktivieren

# VAD-Konfiguration
VAD_THRESHOLD = 0.8  # Sprachwahrscheinlichkeit 0.0-1.0 (höher = strenger)
VAD_MIN_SILENCE_MS = 300  # Mindest-Stille nach Sprache in Millisekunden
VAD_CHUNK_SIZE = 512  # Pflicht für 16kHz (Silero VAD erwartet exakt 512 Samples)

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
- Miro
- Miro-Board (oft als MyRobot verstanden)
"""


def type_text(text, notification=None):
    """
    Tippt Text via wtype ein.
    """
    # Remove control characters and non-spoken symbols
    filtered_text = re.sub(r"[^\w\s.,!?-]", "", text)
    filtered_text = filtered_text.replace("Demokraten- ", "")

    subprocess.run(["wtype", filtered_text.strip() + " "])


class SpeechToText(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.github.phdd.SpeechToText")
        self.loop = None  # Main loop reference

    def stop(self, notification, action, user_data=None):
        if self.loop:
            self.loop.quit()

    def do_activate(self):
        print("do_activate")
        Notify.init("Speech to Text")
        self.loop = GLib.MainLoop()

        self.notification = Notify.Notification.new(
            "Initialisierung", "Bitte warte einen Moment"
        )
        self.notification.set_urgency(Notify.Urgency.CRITICAL)
        self.notification.show()

        recorder = sr.Recognizer()
        recorder.dynamic_energy_threshold = False

        source = sr.Microphone(sample_rate=16000)

        try:
            model = whisper.load_model(model_name)
        except Exception as e:
            self.notification.update(
                "Fehler", f"Modell konnte nicht geladen werden: {e}"
            )
            self.notification.show()
            print(f"Fehler beim Laden des Modells: {e}")
            sys.exit(1)

        try:
            torch.set_num_threads(1)
            vad_model = load_silero_vad()
            vad_iterator = VADIterator(
                vad_model,
                threshold=VAD_THRESHOLD,
                sampling_rate=16000,
                min_silence_duration_ms=VAD_MIN_SILENCE_MS,
            )
        except Exception as e:
            self.notification.update(
                "Fehler", f"VAD-Modell konnte nicht geladen werden: {e}"
            )
            self.notification.show()
            print(f"Fehler beim Laden des VAD-Modells: {e}")
            sys.exit(1)

        self.notification.close()

        self.notification = Notify.Notification.new("Bereitschaft", "Ich höre zu")
        self.notification.add_action("stop", "Beenden", self.stop)
        self.notification.show()

        with source:
            recorder.adjust_for_ambient_noise(source)

        processing = threading.Event()

        def record_callback(_, audio: sr.AudioData):
            if processing.is_set():
                return

            audio_np = (
                np.frombuffer(audio.get_raw_data(), dtype=np.int16).astype(np.float32)
                / 32768.0
            )

            # VAD-Pre-Filter: Audio in 512-Sample-Chunks aufteilen und prüfen
            speech_detected = False
            for i in range(0, len(audio_np) - VAD_CHUNK_SIZE + 1, VAD_CHUNK_SIZE):
                chunk = torch.from_numpy(audio_np[i : i + VAD_CHUNK_SIZE])
                if vad_iterator(chunk, return_seconds=False):
                    speech_detected = True
                    break
            vad_iterator.reset_states()

            if not speech_detected:
                if DEBUG:
                    print("VAD: kein Sprache erkannt, verwerfe Chunk")
                return

            processing.set()
            try:
                self.notification.update("Aufnahme", "verarbeiten")
                self.notification.show()

                result = model.transcribe(
                    audio_np,
                    fp16=torch.cuda.is_available(),
                    initial_prompt=initial_prompt,
                )
                text = result["text"]
                if isinstance(text, list):
                    text = " ".join(str(t) for t in text)
                text = str(text).strip()

                if len(text) > 10:
                    type_text(f"{text} ", notification=self.notification)
            finally:
                processing.clear()
                self.notification.update("Bereitschaft", "Ich höre zu")
                self.notification.show()

        recorder.listen_in_background(source, record_callback, phrase_time_limit=10)

        self.loop.run()


app = SpeechToText()
app.run(sys.argv)

import json
import os
import threading

import sounddevice
import vosk


class MicrophoneError(Exception):
    pass


class Recognizer:
    SAMPLE_RATE = 16000
    BLOCK_SIZE = 8000

    def __init__(self, model_path: str) -> None:
        model_path = os.path.expanduser(model_path)
        if not os.path.isdir(model_path):
            raise FileNotFoundError(f"Vosk model not found at: {model_path}")
        print("Loading vosk model...")
        vosk.SetLogLevel(-1)
        self._model = vosk.Model(model_path)
        print("Vosk model loaded.")
        self._stop_event = threading.Event()

    def capture_and_recognize(self) -> str:
        self._stop_event.clear()
        rec = vosk.KaldiRecognizer(self._model, self.SAMPLE_RATE)
        try:
            with sounddevice.RawInputStream(
                samplerate=self.SAMPLE_RATE,
                blocksize=self.BLOCK_SIZE,
                dtype="int16",
                channels=1,
            ) as stream:
                while not self._stop_event.is_set():
                    data, _ = stream.read(self.BLOCK_SIZE)
                    rec.AcceptWaveform(bytes(data))
        except sounddevice.PortAudioError as e:
            raise MicrophoneError(str(e)) from e

        result = json.loads(rec.FinalResult())
        return result.get("text", "").strip()

    def check_microphone(self) -> bool:
        """Return True if mic is capturing non-silent audio, False if blocked/silent."""
        try:
            with sounddevice.RawInputStream(
                samplerate=self.SAMPLE_RATE,
                blocksize=self.BLOCK_SIZE,
                dtype="int16",
                channels=1,
            ) as stream:
                data, _ = stream.read(self.BLOCK_SIZE)
                return any(b != 0 for b in bytes(data))
        except sounddevice.PortAudioError:
            return False

    def listen_continuous(self, on_result) -> None:
        """Run forever, calling on_result(text) for each recognized phrase."""
        self._stop_event.clear()
        rec = vosk.KaldiRecognizer(self._model, self.SAMPLE_RATE)
        _warned = False
        try:
            with sounddevice.RawInputStream(
                samplerate=self.SAMPLE_RATE,
                blocksize=self.BLOCK_SIZE,
                dtype="int16",
                channels=1,
            ) as stream:
                while not self._stop_event.is_set():
                    data, _ = stream.read(self.BLOCK_SIZE)
                    if rec.AcceptWaveform(bytes(data)):
                        result = json.loads(rec.Result())
                        text = result.get("text", "").strip()
                        if text:
                            _warned = False
                            on_result(text)
                        elif not _warned:
                            _warned = True
                            on_result("")  # empty result — caller can warn
        except sounddevice.PortAudioError as e:
            raise MicrophoneError(str(e)) from e

    def stop(self) -> None:
        self._stop_event.set()

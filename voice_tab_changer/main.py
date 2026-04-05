import difflib
import os
import sys
import threading

# Ensure sibling modules are importable when run directly
sys.path.insert(0, os.path.dirname(__file__))

# PIL.Image.ANTIALIAS was removed in Pillow 10.0 — patch for pystray compatibility
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

import config
import downloader
from listener import HotkeyListener
from recognizer import MicrophoneError, Recognizer
from tray import TrayApp
from window_manager import WindowManager


def main() -> None:
    cfg = config.load_config()

    # Ensure the vosk model is present (downloads if missing)
    downloader.ensure_model(cfg["model_path"])

    # Load vosk model — exit with code 1 on failure
    model_path = os.path.expanduser(cfg["model_path"])
    try:
        recognizer = Recognizer(model_path)
    except Exception as e:
        print(f"ERROR: Failed to load vosk model: {e}", file=sys.stderr)
        sys.exit(1)

    wm = WindowManager()

    # Shared mutable state accessed from multiple threads
    listening = [True]  # use list for mutability in closures
    capture_thread: list[threading.Thread | None] = [None]

    def toggle_listening(enabled: bool) -> None:
        listening[0] = enabled
        if not enabled:
            recognizer.stop()

    tray = TrayApp(cfg, on_toggle=toggle_listening)

    def capture_and_switch() -> None:
        try:
            text = recognizer.capture_and_recognize()
        except MicrophoneError as e:
            print(f"Microphone error: {e}", file=sys.stderr)
            tray.update_status(False)
            listening[0] = False
            return

        if not text:
            return

        # Check aliases first
        alias_target = cfg["aliases"].get(text.lower())
        if alias_target:
            text = alias_target

        # Fuzzy match against visible window titles
        windows = wm.get_windows()
        titles = [w["title"] for w in windows]
        matches = difflib.get_close_matches(
            text, titles, n=1, cutoff=cfg["fuzzy_cutoff"]
        )
        if matches:
            target = next(w for w in windows if w["title"] == matches[0])
            wm.focus_window(target)
        else:
            if cfg.get("error_beep", True):
                print("\a", end="", flush=True)

    def on_hotkey_press() -> None:
        if not listening[0]:
            return
        t = threading.Thread(target=capture_and_switch, daemon=True)
        capture_thread[0] = t
        t.start()

    def on_hotkey_release() -> None:
        recognizer.stop()

    listener = HotkeyListener(cfg, on_hotkey_press, on_hotkey_release)
    listener.start()

    # tray.run() blocks on the main thread until Quit is selected
    tray.run()

    listener.stop()


if __name__ == "__main__":
    main()

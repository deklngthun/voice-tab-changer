import difflib
import os
import sys
import threading
import warnings

# Suppress urllib3 LibreSSL noise (macOS system SSL, not a real issue)
warnings.filterwarnings("ignore", category=Warning, module="urllib3")

# Ensure sibling modules are importable when run directly
sys.path.insert(0, os.path.dirname(__file__))

# PIL.Image.ANTIALIAS was removed in Pillow 10.0 — patch for pystray compatibility
import PIL.Image
if not hasattr(PIL.Image, "ANTIALIAS"):
    PIL.Image.ANTIALIAS = PIL.Image.LANCZOS

def _check_macos_mic_permission() -> bool:
    """Return False if macOS has blocked mic access, True otherwise."""
    if sys.platform != "darwin":
        return True
    try:
        import AVFoundation
        status = AVFoundation.AVCaptureDevice.authorizationStatusForMediaType_(
            AVFoundation.AVMediaTypeAudio
        )
        # 0=undetermined, 1=restricted, 2=denied, 3=authorized
        return status != 2
    except Exception:
        return True  # can't check — let sounddevice try anyway


import config
import downloader
from listener import HotkeyListener
from recognizer import MicrophoneError, Recognizer
from tray import TrayApp
from window_manager import WindowManager


def main() -> None:
    if not _check_macos_mic_permission():
        print(
            "\n[ERROR] Microphone access denied.\n"
            "  Opening System Settings > Privacy & Security > Microphone ...\n",
            file=sys.stderr,
        )
        import subprocess
        subprocess.run([
            "open",
            "x-apple.systempreferences:com.apple.preference.security?Privacy_Microphone"
        ])
        sys.exit(1)

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

    def _warn_if_mic_silent(text: str) -> None:
        if not text and sys.platform == "darwin":
            print(
                "[warn] No speech detected. If you haven't granted Microphone access,\n"
                "  macOS may be showing a permission dialog — check for it and click Allow.\n"
                "  Or open: System Settings > Privacy & Security > Microphone",
                flush=True,
            )

    def process_text(text: str) -> None:
        """Match recognized text against window titles and focus the best match."""
        if not text:
            return
        tray.notify(f'Heard: "{text}"')
        # Check aliases first
        text = cfg["aliases"].get(text.lower(), text)
        # Fuzzy match against visible window titles
        windows = wm.get_windows()
        titles = [w["title"] for w in windows]
        matches = difflib.get_close_matches(
            text, titles, n=1, cutoff=cfg["fuzzy_cutoff"]
        )
        if matches:
            target = next(w for w in windows if w["title"] == matches[0])
            wm.focus_window(target, maximize=cfg.get("maximize_on_switch", True))
        else:
            if cfg.get("error_beep", True):
                print("\a", end="", flush=True)

    def capture_and_switch() -> None:
        try:
            text = recognizer.capture_and_recognize()
        except MicrophoneError as e:
            print(f"Microphone error: {e}", file=sys.stderr)
            tray.update_status(False)
            listening[0] = False
            return
        _warn_if_mic_silent(text)
        process_text(text)

    always_listening = cfg.get("always_listening", False)

    if always_listening:
        def _on_continuous_result(text: str) -> None:
            _warn_if_mic_silent(text)
            process_text(text)

        def _start_continuous() -> None:
            if not listening[0]:
                return
            try:
                recognizer.listen_continuous(_on_continuous_result)
            except MicrophoneError as e:
                print(f"Microphone error: {e}", file=sys.stderr)
                tray.update_status(False)
                listening[0] = False

        def toggle_listening(enabled: bool) -> None:
            listening[0] = enabled
            if not enabled:
                recognizer.stop()
            else:
                threading.Thread(target=_start_continuous, daemon=True).start()

        tray._on_toggle = toggle_listening
        print("Mode: always listening (no hotkey required)")
        threading.Thread(target=_start_continuous, daemon=True).start()
        listener = None
    else:
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
        print(f"Mode: push-to-talk ({cfg['hotkey']})")

        if sys.platform == "darwin":
            print(
                "\n[macOS] If the hotkey does not respond, grant Accessibility permission:\n"
                "  System Settings > Privacy & Security > Accessibility\n"
                "  Add your Terminal app (Terminal.app / iTerm2 / etc.) and restart.\n"
            )

    # tray.run() blocks on the main thread until Quit is selected
    tray.run()

    if listener:
        listener.stop()


if __name__ == "__main__":
    main()

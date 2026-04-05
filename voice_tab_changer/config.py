import json
import os
import subprocess
import sys

CONFIG_DIR = os.path.expanduser("~/.voicetabchanger")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

# When packaged with PyInstaller, the vosk model is bundled inside the binary.
# sys._MEIPASS points to the temp directory where assets are extracted.
def _bundled_model_path() -> str | None:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "models", "vosk-model-small-en-us-0.15")
    return None

DEFAULTS = {
    "hotkey": "ctrl+shift+space",
    "model_path": "~/.voicetabchanger/models/vosk-model-small-en-us-0.15",
    "aliases": {
        "code": "Code",
        "browser": "Google Chrome",
        "music": "Spotify"
    },
    "fuzzy_cutoff": 0.4,
    "error_beep": True,
    "always_listening": False,
    "maximize_on_switch": True
}


def load_config() -> dict:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save_config(DEFAULTS)
        return dict(DEFAULTS)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # Fill in any missing keys from defaults
    for key, val in DEFAULTS.items():
        if key not in cfg:
            cfg[key] = val
    # If running as a frozen bundle, override model_path to the bundled copy
    bundled = _bundled_model_path()
    if bundled:
        cfg["model_path"] = bundled
    return cfg


def save_config(cfg: dict) -> None:
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def open_config_in_editor() -> None:
    if sys.platform == "win32":
        os.startfile(CONFIG_PATH)
    else:
        subprocess.run(["open", CONFIG_PATH])

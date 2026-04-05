import json
import os
import subprocess
import sys

CONFIG_DIR = os.path.expanduser("~/.voicetabchanger")
CONFIG_PATH = os.path.join(CONFIG_DIR, "config.json")

DEFAULTS = {
    "hotkey": "ctrl+shift+space",
    "model_path": "~/.voicetabchanger/models/vosk-model-small-en-us-0.15",
    "aliases": {
        "code": "Visual Studio Code",
        "browser": "Google Chrome",
        "music": "Spotify"
    },
    "fuzzy_cutoff": 0.4,
    "error_beep": True
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

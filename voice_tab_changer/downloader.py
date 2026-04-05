import os
import urllib.request
import zipfile

MODEL_URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"


def _progress_hook(block_num: int, block_size: int, total_size: int) -> None:
    downloaded = block_num * block_size
    if total_size > 0:
        pct = min(100, downloaded * 100 // total_size)
        mb_done = downloaded / (1024 * 1024)
        mb_total = total_size / (1024 * 1024)
        print(f"\r  Downloading... {pct}% ({mb_done:.1f} / {mb_total:.1f} MB)", end="", flush=True)
    else:
        mb_done = downloaded / (1024 * 1024)
        print(f"\r  Downloading... {mb_done:.1f} MB", end="", flush=True)


def ensure_model(model_path: str) -> None:
    model_path = os.path.expanduser(model_path)
    if os.path.isdir(model_path):
        return

    print(f"Vosk model not found at: {model_path}")
    print(f"Downloading model from {MODEL_URL} ...")

    parent_dir = os.path.dirname(model_path)
    os.makedirs(parent_dir, exist_ok=True)

    zip_path = model_path + ".zip"
    try:
        urllib.request.urlretrieve(MODEL_URL, zip_path, reporthook=_progress_hook)
        print()  # newline after progress
        print("Download complete. Extracting...")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(parent_dir)
        print(f"Model extracted to: {model_path}")
    finally:
        if os.path.exists(zip_path):
            os.remove(zip_path)

#!/bin/bash
set -e

MODEL_PATH="$HOME/.voicetabchanger/models/vosk-model-small-en-us-0.15"

if [ ! -d "$MODEL_PATH" ]; then
  echo "Vosk model not found at $MODEL_PATH"
  echo "Run the app once first to auto-download the model, then re-run this script."
  exit 1
fi

pyinstaller \
  --onefile \
  --windowed \
  --name VoiceTabChanger \
  --add-data "$MODEL_PATH:models/vosk-model-small-en-us-0.15" \
  voice_tab_changer/main.py

echo "Build complete: dist/VoiceTabChanger"

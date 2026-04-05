@echo off
setlocal

set MODEL_PATH=%USERPROFILE%\.voicetabchanger\models\vosk-model-small-en-us-0.15

if not exist "%MODEL_PATH%" (
    echo Vosk model not found at %MODEL_PATH%
    echo Run the app once first to auto-download the model, then re-run this script.
    exit /b 1
)

pyinstaller ^
  --onefile ^
  --windowed ^
  --name VoiceTabChanger ^
  --add-data "%MODEL_PATH%;models\vosk-model-small-en-us-0.15" ^
  voice_tab_changer\main.py

echo Build complete: dist\VoiceTabChanger.exe
endlocal

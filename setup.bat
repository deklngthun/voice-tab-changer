@echo off
setlocal

echo Creating virtual environment...
python -m venv .venv

echo Activating and installing dependencies...
.venv\Scripts\pip install --upgrade pip -q
.venv\Scripts\pip install -r requirements.txt

echo.
echo Setup complete.
echo To activate: .venv\Scripts\activate
echo To run:      python voice_tab_changer\main.py
endlocal

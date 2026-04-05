#!/bin/bash
set -e

echo "Creating virtual environment (Python 3.14)..."
/usr/local/bin/python3.14 -m venv .venv

echo "Activating and installing dependencies..."
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -r requirements.txt

echo ""
echo "Setup complete."
echo "To activate: source .venv/bin/activate"
echo "To run:      python voice_tab_changer/main.py"

#!/bin/bash
set -e

REPO="deklngthun/voice-tab-changer"
ZIP_URL="https://github.com/$REPO/releases/latest/download/VoiceTabChanger-macOS.zip"
APP_NAME="VoiceTabChanger.app"
DEST="/Applications/$APP_NAME"

echo ""
echo "  Voice Tab Changer — Installer"
echo "  ────────────────────────────────"
echo ""

# Remove old version if present
if [ -d "$DEST" ]; then
  echo "  → Removing previous version..."
  rm -rf "$DEST"
fi

echo "  → Downloading..."
curl -L --progress-bar -o /tmp/VoiceTabChanger-macOS.zip "$ZIP_URL"

echo "  → Extracting..."
unzip -q -o /tmp/VoiceTabChanger-macOS.zip -d /tmp/vtc_extract

echo "  → Removing macOS quarantine flag..."
xattr -cr /tmp/vtc_extract/VoiceTabChanger.app

echo "  → Moving to Applications..."
mv /tmp/vtc_extract/VoiceTabChanger.app "$DEST"

# Cleanup
rm -rf /tmp/VoiceTabChanger-macOS.zip /tmp/vtc_extract

echo ""
echo "  ✅ Installed! Launching Voice Tab Changer..."
echo ""
open "$DEST"

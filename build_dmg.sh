#!/bin/bash
set -e

# ── Config ────────────────────────────────────────────────────────────────────
APP_NAME="VoiceTabChanger"
DMG_NAME="VoiceTabChanger-macOS"
MODEL_PATH="$HOME/.voicetabchanger/models/vosk-model-small-en-us-0.15"
STAGING="/tmp/vtc_dmg_staging"
DIST="$(cd "$(dirname "$0")" && pwd)/dist"

# ── Guard ─────────────────────────────────────────────────────────────────────
if [ ! -d "$MODEL_PATH" ]; then
  echo "Vosk model not found. Run the app once first to download it."
  exit 1
fi

# ── Build .app with PyInstaller ───────────────────────────────────────────────
echo "Building .app bundle..."
.venv/bin/pyinstaller \
  --name "$APP_NAME" \
  --windowed \
  --onedir \
  --noconfirm \
  --add-data "$MODEL_PATH:models/vosk-model-small-en-us-0.15" \
  voice_tab_changer/main.py

# ── Ad-hoc sign ───────────────────────────────────────────────────────────────
echo "Ad-hoc signing..."
codesign --deep --force --sign - "dist/$APP_NAME.app"
xattr -cr "dist/$APP_NAME.app"

# ── Create install script ─────────────────────────────────────────────────────
echo "Creating installer script..."
rm -rf "$STAGING" && mkdir -p "$STAGING"
cp -R "dist/$APP_NAME.app" "$STAGING/"

INSTALL_SCRIPT="$STAGING/Install Voice Tab Changer.command"
cat > "$INSTALL_SCRIPT" << 'SCRIPT'
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="/Applications/VoiceTabChanger.app"

# Remove old version
[ -d "$DEST" ] && rm -rf "$DEST"

# Copy from DMG and strip quarantine
cp -R "$SCRIPT_DIR/VoiceTabChanger.app" "$DEST"
xattr -cr "$DEST"

# Launch
open "$DEST"

osascript -e 'display dialog "Voice Tab Changer is installed!\n\nLook for the V icon in your menu bar.\nSay any app name to switch to it." buttons {"Got it!"} default button "Got it!" with icon note with title "Voice Tab Changer"'
SCRIPT
chmod +x "$INSTALL_SCRIPT"
xattr -cr "$INSTALL_SCRIPT"

# ── Create background image ───────────────────────────────────────────────────
echo "Generating DMG background..."
.venv/bin/python3 - << 'PYEOF'
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 540, 320
img = Image.new("RGB", (W, H), "#0d0f1a")
draw = ImageDraw.Draw(img)

# Subtle grid lines
for x in range(0, W, 40):
    draw.line([(x, 0), (x, H)], fill="#13162a", width=1)
for y in range(0, H, 40):
    draw.line([(0, y), (W, y)], fill="#13162a", width=1)

# Title
draw.text((W//2, 48), "Voice Tab Changer", fill="#e2e8f0", anchor="mm", font=None)
draw.text((W//2, 76), "Double-click  \"Install Voice Tab Changer\"  to install", fill="#8892b0", anchor="mm", font=None)

# Arrow pointing down-left toward the install script
draw.text((W//2, 240), "▼  Double-click to install  ▼", fill="#6c63ff", anchor="mm", font=None)

os.makedirs("/tmp/vtc_bg", exist_ok=True)
img.save("/tmp/vtc_bg/bg.png")
PYEOF

# ── Create DMG ────────────────────────────────────────────────────────────────
echo "Creating DMG..."
mkdir -p "$DIST"
rm -f "$DIST/$DMG_NAME.dmg"

# Create a writable DMG first
hdiutil create \
  -volname "Voice Tab Changer" \
  -srcfolder "$STAGING" \
  -ov \
  -fs HFS+ \
  -format UDRW \
  "/tmp/vtc_rw.dmg"

# Mount it and set Finder window size
MOUNT=$(hdiutil attach "/tmp/vtc_rw.dmg" -readwrite -nobrowse | grep "/Volumes/" | awk '{print $NF}' | sed 's/[[:space:]]*$//')

osascript << APPLESCRIPT
tell application "Finder"
  tell disk "Voice Tab Changer"
    open
    set current view of container window to icon view
    set toolbar visible of container window to false
    set statusbar visible of container window to false
    set bounds of container window to {100, 100, 640, 440}
    set icon size of the icon view options of container window to 80
    set arrangement of the icon view options of container window to not arranged
    set position of item "VoiceTabChanger.app" of container window to {160, 170}
    set position of item "Install Voice Tab Changer.command" of container window to {370, 170}
    close
    open
    update without registering applications
    delay 2
    close
  end tell
end tell
APPLESCRIPT

# Unmount and convert to compressed read-only
hdiutil detach "$MOUNT" 2>/dev/null || hdiutil detach "/Volumes/Voice Tab Changer" 2>/dev/null || true
sleep 2
hdiutil convert "/tmp/vtc_rw.dmg" -format UDZO -o "$DIST/$DMG_NAME.dmg"

# Cleanup
rm -rf "$STAGING" "/tmp/vtc_rw.dmg" "/tmp/vtc_bg"

echo ""
echo "✅ Done: dist/$DMG_NAME.dmg"
echo "   Size: $(du -sh "$DIST/$DMG_NAME.dmg" | cut -f1)"

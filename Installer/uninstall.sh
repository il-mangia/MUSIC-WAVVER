#!/bin/bash

APP_DIR="/opt/music-wavver"
DESKTOP_FILE="/usr/share/applications/music-wavver.desktop"
RUN_SCRIPT="$APP_DIR/run.sh"

echo "Uninstalling MUSIC WAVVER..."

# --- Require sudo ---
if [ "$EUID" -ne 0 ]; then
    echo "This uninstaller requires administrator privileges."
    exec sudo "$0" "$@"
fi

# --- Remove program files ---
if [ -d "$APP_DIR" ]; then
    rm -rf "$APP_DIR"
    echo "Program directory removed: $APP_DIR"
else
    echo "Program directory not found: $APP_DIR"
fi

# --- Remove desktop launcher ---
if [ -f "$DESKTOP_FILE" ]; then
    rm -f "$DESKTOP_FILE"
    echo "Desktop launcher removed: $DESKTOP_FILE"
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1
fi

# --- Ask for dependency removal ---
read -p "Do you want to remove dependencies? [y/N]: " REMOVE_DEPS

if [[ "$REMOVE_DEPS" =~ ^[Yy]$ ]]; then
    echo "Removing Python libraries..."
    pip3 uninstall -y customtkinter pillow

    echo "Removing system dependencies..."
    if command -v apt >/dev/null 2>&1; then
        apt remove -y ffmpeg python3-tk
    elif command -v dnf >/dev/null 2>&1; then
        dnf remove -y ffmpeg python3-tkinter
    elif command -v pacman >/dev/null 2>&1; then
        pacman -Rns --noconfirm ffmpeg tk
    else
        echo "Distribution not supported for automatic dependency removal."
    fi

    echo "Dependencies removed."
else
    echo "Dependencies have not been removed."
fi

echo "MUSIC WAVVER uninstallation completed."

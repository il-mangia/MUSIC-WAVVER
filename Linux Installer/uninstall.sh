#!/bin/bash

APP_NAME="music-wavver"
APP_DIR="/opt/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"
BIN_LINK="/usr/bin/$APP_NAME"

PYTHON_PACKAGES=("requests" "PyQt6" "mutagen" "spotipy")

echo "Uninstalling $APP_NAME..."

# SUDO
if [ "$EUID" -ne 0 ]; then
  echo "Administrator privileges required"
  exec sudo "$0" "$@"
fi

# App
if [ -d "$APP_DIR" ]; then
  echo "Removing application files..."
  rm -rf "$APP_DIR"
else
  echo "Application directory not found"
fi

# Desktop entry
if [ -f "$DESKTOP_FILE" ]; then
  echo "Removing desktop entry..."
  rm -f "$DESKTOP_FILE"
else
  echo "Desktop entry not found"
fi

# Binary link
if [ -e "$BIN_LINK" ]; then
  echo "Removing binary link..."
  rm -f "$BIN_LINK"
else
  echo "Binary link not found"
fi

# Python deps
echo ""
read -p "Do you want to remove Python dependencies installed? [y/N]: " answer

if [[ "$answer" == "y" || "$answer" == "Y" ]]; then
  echo "Removing Python dependencies..."

  for pkg in "${PYTHON_PACKAGES[@]}"; do
    pip3 show "$pkg" >/dev/null 2>&1 && pip3 uninstall -y "$pkg"
  done

  echo "Python dependencies removed"
else
  echo "Keeping Python dependencies"
fi

# Desktop DB update
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1
fi

echo ""
echo "$APP_NAME successfully removed!"
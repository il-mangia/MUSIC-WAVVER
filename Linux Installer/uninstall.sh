#!/bin/bash

APP_NAME="music-wavver"
APP_DIR="/opt/$APP_NAME"
DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"
BIN_LINK="/usr/bin/$APP_NAME"

echo "Uninstalling $APP_NAME..."

# Richiesta SUDO
if [ "$EUID" -ne 0 ]; then
  echo "Administrator privileges required"
  exec sudo "$0" "$@"
fi

# Rimozione directory applicazione
if [ -d "$APP_DIR" ]; then
  echo "Removing application files..."
  rm -rf "$APP_DIR"
else
  echo "Application directory not found"
fi

# Rimozione launcher desktop
if [ -f "$DESKTOP_FILE" ]; then
  echo "Removing desktop entry"
  rm -rf "$DESKTOP_FILE"
else
  echo "Desktop entry not found"
fi

# Rimozione comando da terminale
if [ -L "$BIN_LINK" ] || [ -f "$BIN_LINK" ]; then
  echo "Removing binary link..."
  rm -rf "$BIN_LINK"
else
  echo "Binary link not found..."
fi

# Aggiorna database desktop
if command -v update-desktop-database >/dev/null 2>&1, then
  update-desktop-database /usr/share/applications >/dev/null 2>&1
fi

echo ""
echo "$APP_NAME successfully removed!"
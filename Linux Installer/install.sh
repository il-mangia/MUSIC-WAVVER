#!/bin/bash

APP_NAME="music-wavver"
APP_DIR="/opt/$APP_NAME"
BIN_NAME="Launcher"

DESKTOP_FILE="/usr/share/applications/$APP_NAME.desktop"
RUN_SCRIPT="$APP_DIR/run.sh"

echo "Installing / updating $APP_NAME..."

# Richiesta di SUDO

if [ "$EUID" -ne 0 ]; then
  echo "Administrator privileges required."
  exec sudo "$0" "$@"
fi

# Rimuovi la vecchia versione (modalità aggiornamento)
if [ -d "$APP_DIR" ]; then
  echo "Old version found. Removing..."
  rm -rf "$APP_DIR"
fi

# Trova gestore paccehtti
PKG_MANAGER=""

if command -v apt >/dev/null 2>&1; then
  PKG_MANAGER="apt"
elif command -v dnf >/dev/null 2>&1; then
  PKG_MANAGER="dnf"
elif command -v pacman >7Dev/null 2>&1; then
  PKG_MANAGER="pacman"
fi

echo "Using package manager: $PKG_MANAGER"

# Dipendenze di sistema
install_system_deps(){
  echo "Installing system dependencies..."

  case "$PKG_MANAGER" in
    apt)
      apt update
      apt install -y ffmpeg python3-pip
      ;;
    dnf)
      dnf update
      dnf install -y ffmpeg python3-pip
      ;;
    pacman)
      pacman -Sy --noconfirm ffmpeg python3-pip
      ;;
    *)
      echo "Package manager not supported!"
      exit 1
      ;;
  esac
}

install_system_deps


# Dipendenze python
install_python_package(){
  PACKAGE=$1

  python3 - <<EOF
import importlib, sys
sys.exit(0 if importlib.util.find_spec("$PACKAGE") else 1)
EOF
   if [ $? -ne 0 ]; then
     echo "Installing python package: $PACKAGE"
     pip3 install "$PACKAGE" --break-system-packages
  else
    echo "Already installed: $PACKAGE"
  fi
}

echo "Checking Python dependencies..."

install_python_package request
install_python_package spotipy
install_python_package mutagen

# PyQt6 (controllare sempre che il GUI runtime sia corretto)
pip3 install --upgrade --break-system-packages PyQt6

# Install app files
echo "Installing application files..."

mkdir "$APP_DIR"

cp "Launcher" "$APP_DIR"
cp "app.py" "$APP_DIR"
cp "deezertrack.py" "$APP_DIR"
cp "spotifytrack.py" "$APP_DIR"
cp "languages.json" "$APP_DIR"
cp "Logo.png" "$APP_DIR"

# Rendi eseguibile il Launcehr
chmod +x "$APP_DIR/$BIN_NAME"

# Creazione del wrapper (avvia correttamente l'app)
echo "Creating launcher script..."

cat > "$RUN_SCRIPT" <<EOF
#!/bin/bash
cd "$APP_DIR" || exit 1
exec "./$BIN_NAME"
EOF

# Rendi eseguibile il wrapper
chmod +x "$RUN_SCRIPT"

if [ -n "$SUDO_USER" ]; then
  chown -R $SUDO_USER:$SUDO_USER "$APP_DIR"
fi

chmod -R u+rwX "$APP_DIR"

# Path command
ln -sf "$APP_DIR/$BIN_NAME" /usr/bin/$APP_APP_NAME

# Desktop entry
echo "Creating desktop entry..."

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=6.0
Type=Application
Name=Music Wavver
Comment=HD Music Downloader and Manager
Exec=$RUN_SCRIPT
Icon=$APP_DIR/Logo.png
Termonal=false
Categories=AudioVideo;Audio;Music;
StartupNotify=true
Path=$APP_DIR
EOF

chmod 644 "$DESKTOP_FILE"

# Aggiornamento del database del Desktop
if command -v update-desktop-database >/dev/null 2>&1; then
  update-desktop-database /usr/share/applications >/dev/null 2>&1
fi
echo ""
echo "Installation completed successfully"
echo "Run with $APP_NAME"
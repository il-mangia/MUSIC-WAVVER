#!/bin/bash

APP_DIR="/opt/music-wavver"
BIN_NAME="Music_Wavver"
DESKTOP_FILE="/usr/share/applications/music-wavver.desktop"
RUN_SCRIPT="$APP_DIR/run.sh"

echo "Installing / updating MUSIC WAVVER..."

# --- Require sudo ---
if [ "$EUID" -ne 0 ]; then
    echo "Administrator privileges required."
    exec sudo "$0" "$@"
fi

# --- System dependencies ---
install_deps_apt() {
    if ! command -v ffmpeg >/dev/null; then
        apt update
        apt install -y ffmpeg
    fi
    if ! dpkg -s python3-tk >/dev/null 2>&1; then
        apt install -y python3-tk
    fi
}

install_deps_dnf() {
    if ! command -v ffmpeg >/dev/null; then
        dnf install -y ffmpeg
    fi
    if ! rpm -q python3-tkinter >/dev/null 2>&1; then
        dnf install -y python3-tkinter
    fi
}

install_deps_pacman() {
    if ! command -v ffmpeg >/dev/null; then
        pacman -Sy --noconfirm ffmpeg
    fi
    if ! pacman -Qi tk >/dev/null 2>&1; then
        pacman -Sy --noconfirm tk
    fi
}

echo "Detecting distribution..."
if command -v apt >/dev/null 2>&1; then
    install_deps_apt
elif command -v dnf >/dev/null 2>&1; then
    install_deps_dnf
elif command -v pacman >/dev/null 2>&1; then
    install_deps_pacman
fi

# --- Python libraries ---
install_python_package() {
    PACKAGE=$1
    python3 - <<EOF
import importlib, sys
try:
    importlib.import_module("$PACKAGE")
    sys.exit(0)
except ImportError:
    sys.exit(1)
EOF

    if [ $? -ne 0 ]; then
        echo "Installing Python library: $PACKAGE"
        pip3 install "$PACKAGE" --break-system-packages
    else
        echo "Python library already installed: $PACKAGE"
    fi
}

install_python_package customtkinter
install_python_package pillow

pip3 install --upgrade --break-system-packages customtkinter
pip3 install --upgrade --break-system-packages pillow

# --- Installing program files ---
echo "Installing program files..."

mkdir -p "$APP_DIR"

cp "$BIN_NAME" "$APP_DIR/"
cp "playlists.py" "$APP_DIR/"
cp "languages.json" "$APP_DIR/"
cp "settings.json" "$APP_DIR/"
cp "Logo.png" "$APP_DIR/"
cp "Logo.ico" "$APP_DIR/"
cp "playlist_urls.log" "$APP_DIR/" 2>/dev/null
cp "ytdownloader.log" "$APP_DIR/" 2>/dev/null

chmod +x "$APP_DIR/$BIN_NAME"

# --- Create run.sh automatically ---
echo "Creating run.sh wrapper..."

cat > "$RUN_SCRIPT" <<EOF
#!/bin/bash
cd "$APP_DIR" || exit 1
exec "$APP_DIR/$BIN_NAME"
EOF

chmod +x "$RUN_SCRIPT"

# --- Fix permissions so user can write logs ---
echo "Fixing permissions..."
chown -R $SUDO_USER:$SUDO_USER "$APP_DIR"
chmod -R u+rwX "$APP_DIR"

# --- Create command in PATH ---
ln -sf "$APP_DIR/$BIN_NAME" /usr/bin/music-wavver

# --- Creating desktop launcher ---
echo "Creating launcher..."

cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Music Wavver
Comment=Music Wavver HD audio downloader
Exec=$RUN_SCRIPT
Icon=$APP_DIR/Logo.png
Terminal=false
Categories=AudioVideo;Audio;Music;Player;
StartupNotify=true
Path=$APP_DIR
EOF

chmod 644 "$DESKTOP_FILE"

# Update menu database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database /usr/share/applications >/dev/null 2>&1
fi

echo "Installation completed."
echo "You can launch Music Wavver from the application menu or by typing:"
echo "music-wavver"

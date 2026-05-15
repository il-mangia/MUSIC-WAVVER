#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA - 2026
MUSIC WAVVER 6 Launcher
MADE IN ITALY
"""

import sys
import os
import platform
import subprocess
import zipfile
import shutil
import tempfile
import locale
import webbrowser

import requests
from PyQt6.QtCore import (
    Qt, QTimer, QPropertyAnimation, QEasingCurve, pyqtSignal, QObject,
    QThread, QPoint, QRect
)
from PyQt6.QtGui import QPixmap, QFont, QColor
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QProgressBar, QStackedWidget, QFrame, QGraphicsOpacityEffect
)

# -----------------------------------------------------------------------------
# CONFIGURAZIONE GLOBALE
# -----------------------------------------------------------------------------
WIDTH = 440
HEIGHT = 600   # Aumentato ulteriormente per sicurezza

LOGO_START_Y = -220
LOGO_END_Y = 55

CURRENT_VERSION = "6"

GITHUB_REPO = "il-mangia/MUSIC-WAVVER"
GITHUB_TAGS_URL = f"https://api.github.com/repos/{GITHUB_REPO}/tags"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_LATEST_RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

FFMPEG_ZIP_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest"
    "/ffmpeg-master-latest-win64-gpl.zip"
)

# Colori UI
C_BG = "#1A1A2E"
C_PANEL = "#16213E"
C_ACCENT = "#7C5CBF"
C_GREEN = "#4CAF50"
C_RED = "#E53935"
C_BLUE = "#2196F3"
C_TEXT = "#EAEAEA"
C_MUTED = "#888888"
C_WARN = "#FFA726"

# -----------------------------------------------------------------------------
# MULTILINGUA (invariato, omesso per brevità ma presente nel file completo)
# -----------------------------------------------------------------------------
TRANSLATIONS = {
    "it": {
        "app_name": "MUSIC WAVVER",
        "window_title": f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates": "Controllo aggiornamenti...",
        "update_available": "Aggiornamento disponibile!",
        "beta_detected": "Versione beta rilevata!",
        "error_checking": "Errore nel controllo!",
        "version_updated": "Versione aggiornata",
        "update_title": "AGGIORNAMENTO DISPONIBILE",
        "current_version": "Versione attuale",
        "latest_stable": "Ultima stabile",
        "update_message": "Nuova versione di Music Wavver disponibile.",
        "download_install": "SCARICA E INSTALLA",
        "open_browser": "Apri nel browser",
        "continue_without": "CONTINUA SENZA AGGIORNARE",
        "downloading_update": "Download in corso...",
        "download_done": "Download completato. Avvio installer...",
        "download_error": "Errore nel download. Apertura browser...",
        "beta_title": "VERSIONE BETA",
        "beta_current": "Versione in uso",
        "beta_warning": "Stai usando una versione beta.\nSi consiglia di tornare all'ultima stabile.",
        "return_stable": "TORNA ALLA VERSIONE STABILE",
        "accept_risk": "CONTINUA IN OGNI CASO",
        "beta_note": "Segnala eventuali bug agli sviluppatori.",
        "error_title": "ERRORE DI CONNESSIONE",
        "error_message": "Impossibile verificare gli aggiornamenti.\nControlla la connessione Internet.",
        "retry_button": "RIPROVA",
        "continue_anyway": "CONTINUA COMUNQUE",
        "error_note": "L'applicazione potrebbe non essere aggiornata.",
        "ffmpeg_title": "FFMPEG NON TROVATO",
        "ffmpeg_message": "FFmpeg e' necessario per convertire l'audio.\nVuoi scaricarlo e installarlo automaticamente?\n(~45 MB, nessun admin richiesto)",
        "ffmpeg_install": "INSTALLA FFMPEG AUTOMATICAMENTE",
        "ffmpeg_skip": "Installa manualmente",
        "ffmpeg_progress": "Download FFmpeg in corso...",
        "ffmpeg_extract": "Estrazione in corso...",
        "ffmpeg_done": "FFmpeg installato correttamente!",
        "ffmpeg_error": "Errore nell'installazione di FFmpeg.",
        "ffmpeg_note": "Richiesto per la conversione audio (mp3, flac, ecc.)",
        "checking_for": "Controllo aggiornamenti per versione",
        "latest_found": "Ultima versione stabile trovata",
        "update_found": "Trovato aggiornamento",
        "up_to_date": "Sei aggiornato",
        "timeout": "Timeout nel controllo",
        "connection_error": "Errore di connessione",
        "no_tags": "Nessun tag nel repository",
        "no_stable": "Nessuna versione stabile",
        "starting_app": "Avvio applicazione...",
        "opening_release": "Apertura pagina release",
    },
    "en": {
        "app_name": "MUSIC WAVVER",
        "window_title": f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates": "Checking for updates...",
        "update_available": "Update available!",
        "beta_detected": "Beta version detected!",
        "error_checking": "Error checking updates!",
        "version_updated": "Up to date",
        "update_title": "UPDATE AVAILABLE",
        "current_version": "Current version",
        "latest_stable": "Latest stable",
        "update_message": "A new version of Music Wavver is available.",
        "download_install": "DOWNLOAD & INSTALL",
        "open_browser": "Open in browser",
        "continue_without": "CONTINUE WITHOUT UPDATING",
        "downloading_update": "Downloading...",
        "download_done": "Download complete. Launching installer...",
        "download_error": "Download error. Opening browser...",
        "beta_title": "BETA VERSION",
        "beta_current": "Current version",
        "beta_warning": "You are running a beta version.\nWe recommend returning to the latest stable.",
        "return_stable": "RETURN TO STABLE VERSION",
        "accept_risk": "CONTINUE ANYWAY",
        "beta_note": "Report any bugs to the developers.",
        "error_title": "CONNECTION ERROR",
        "error_message": "Unable to check for updates.\nCheck your Internet connection.",
        "retry_button": "RETRY",
        "continue_anyway": "CONTINUE ANYWAY",
        "error_note": "Application may not be up to date.",
        "ffmpeg_title": "FFMPEG NOT FOUND",
        "ffmpeg_message": "FFmpeg is required to convert audio.\nDo you want to download and install it automatically?\n(~45 MB, no admin required)",
        "ffmpeg_install": "INSTALL FFMPEG AUTOMATICALLY",
        "ffmpeg_skip": "Install manually",
        "ffmpeg_progress": "Downloading FFmpeg...",
        "ffmpeg_extract": "Extracting...",
        "ffmpeg_done": "FFmpeg installed successfully!",
        "ffmpeg_error": "Error installing FFmpeg.",
        "ffmpeg_note": "Required for audio conversion (mp3, flac, etc.)",
        "checking_for": "Checking updates for version",
        "latest_found": "Latest stable version found",
        "update_found": "Update found",
        "up_to_date": "Up to date",
        "timeout": "Update check timeout",
        "connection_error": "Connection error",
        "no_tags": "No tags in repository",
        "no_stable": "No stable version found",
        "starting_app": "Launching application...",
        "opening_release": "Opening release page",
    },
    # ... (altre lingue omesse per brevità, ma includile come nel codice originale)
}

def T(key, lang):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

# -----------------------------------------------------------------------------
# UTILITY PATHS
# -----------------------------------------------------------------------------
def get_launcher_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(get_launcher_dir(), relative_path)

def get_ffmpeg_install_dir():
    return os.path.join(get_launcher_dir(), "ffmpeg", "bin")

def ffmpeg_is_available():
    if shutil.which("ffmpeg"):
        return True
    ffmpeg_local = os.path.join(get_ffmpeg_install_dir(), "ffmpeg.exe")
    return os.path.isfile(ffmpeg_local)

# -----------------------------------------------------------------------------
# VERSIONI
# -----------------------------------------------------------------------------
def compare_versions(v1, v2):
    try:
        p1 = list(map(int, v1.split(".")))
        p2 = list(map(int, v2.split(".")))
        m = max(len(p1), len(p2))
        p1 += [0] * (m - len(p1))
        p2 += [0] * (m - len(p2))
        for a, b in zip(p1, p2):
            if a > b: return 1
            if a < b: return -1
        return 0
    except Exception:
        return 0 if v1 == v2 else (1 if v1 > v2 else -1)

def get_latest_stable(tags):
    stable = []
    for tag in tags:
        name = tag.get("name", "").lstrip("v").lower()
        if any(x in name for x in ["beta", "alpha", "rc", "pre", "dev"]):
            continue
        clean = "".join(c for c in name if c.isdigit() or c == ".")
        if clean and clean.replace(".", "").isdigit():
            stable.append((clean, tag))
    if not stable:
        return None, None
    best = max(stable, key=lambda x: list(map(int, x[0].split("."))))
    return best[0], best[1].get("tarball_url")

def check_for_updates(lang):
    print(f"{T('checking_for', lang)} {CURRENT_VERSION}...")
    try:
        headers = {"User-Agent": "MusicWavver-Launcher"}
        r = requests.get(GITHUB_TAGS_URL, headers=headers, timeout=10)
        if r.status_code != 200:
            return "error", None, None, None
        tags = r.json()
        if not tags:
            return "up_to_date", None, None, None
        latest, url = get_latest_stable(tags)
        if not latest:
            return "up_to_date", None, None, tags
        print(f"{T('latest_found', lang)}: {latest}")
        cmp = compare_versions(CURRENT_VERSION, latest)
        if cmp < 0:
            return "update_available", latest, url, tags
        elif cmp > 0:
            return "beta_version", latest, url, tags
        else:
            return "up_to_date", latest, None, tags
    except requests.exceptions.Timeout:
        print(T("timeout", lang))
        return "error", None, None, None
    except Exception as e:
        print(f"{T('connection_error', lang)}: {e}")
        return "error", None, None, None

# -----------------------------------------------------------------------------
# DOWNLOAD INSTALLER GITHUB
# -----------------------------------------------------------------------------
def get_latest_release_installer():
    try:
        headers = {"User-Agent": "MusicWavver-Launcher"}
        r = requests.get(GITHUB_RELEASES_API, headers=headers, timeout=10)
        r.raise_for_status()
        data = r.json()
        for asset in data.get("assets", []):
            name = asset.get("name", "")
            if name.lower().endswith(".exe"):
                return asset["browser_download_url"], name
    except Exception as e:
        print(f"Errore get_latest_release_installer: {e}")
    return None, None

# -----------------------------------------------------------------------------
# THREAD PER DOWNLOAD
# -----------------------------------------------------------------------------
class DownloadWorker(QObject):
    progress = pyqtSignal(float)
    status = pyqtSignal(str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            headers = {"User-Agent": "MusicWavver-Launcher"}
            r = requests.get(self.url, stream=True, timeout=60, headers=headers)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(self.dest_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(downloaded / total)
                            mb_d = downloaded / 1_048_576
                            mb_t = total / 1_048_576
                            self.status.emit(f"{mb_d:.1f} MB / {mb_t:.1f} MB")
            self.finished.emit(self.dest_path)
        except Exception as e:
            self.error.emit(str(e))

# -----------------------------------------------------------------------------
# THREAD PER INSTALLAZIONE FFMPEG (solo Windows)
# -----------------------------------------------------------------------------
class FFmpegInstallWorker(QObject):
    progress = pyqtSignal(float)
    status = pyqtSignal(str)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def run(self):
        try:
            install_dir = get_ffmpeg_install_dir()
            os.makedirs(install_dir, exist_ok=True)

            tmp_dir = tempfile.mkdtemp(prefix="mw_ffmpeg_")
            zip_path = os.path.join(tmp_dir, "ffmpeg.zip")

            self.status.emit("Download FFmpeg...")
            headers = {"User-Agent": "MusicWavver-Launcher"}
            r = requests.get(FFMPEG_ZIP_URL, stream=True, timeout=120, headers=headers)
            r.raise_for_status()
            total = int(r.headers.get("content-length", 0))
            downloaded = 0
            with open(zip_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=16384):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress.emit(downloaded / total)
                            mb_d = downloaded / 1_048_576
                            mb_t = total / 1_048_576
                            self.status.emit(f"Download {mb_d:.1f} MB / {mb_t:.1f} MB")
            self.progress.emit(0.0)
            self.status.emit("Estrazione...")

            ffmpeg_exe_dest = os.path.join(install_dir, "ffmpeg.exe")
            with zipfile.ZipFile(zip_path, "r") as zf:
                names = zf.namelist()
                target = None
                for n in names:
                    if n.endswith("bin/ffmpeg.exe") or n.endswith("bin\\ffmpeg.exe"):
                        target = n
                        break
                if not target:
                    for n in names:
                        if os.path.basename(n).lower() == "ffmpeg.exe":
                            target = n
                            break
                if not target:
                    raise FileNotFoundError("ffmpeg.exe non trovato nel file ZIP.")
                with zf.open(target) as src, open(ffmpeg_exe_dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)

            self.progress.emit(0.9)
            self.status.emit("Aggiorno PATH...")

            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Environment",
                    0, winreg.KEY_ALL_ACCESS
                )
                try:
                    current_path, _ = winreg.QueryValueEx(key, "PATH")
                except FileNotFoundError:
                    current_path = ""
                if install_dir.lower() not in current_path.lower():
                    new_path = f"{install_dir};{current_path}" if current_path else install_dir
                    winreg.SetValueEx(key, "PATH", 0, winreg.REG_EXPAND_SZ, new_path)
                winreg.CloseKey(key)
                import ctypes
                HWND_BROADCAST = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
            except Exception as e_reg:
                print(f"PATH update warning: {e_reg}")

            shutil.rmtree(tmp_dir, ignore_errors=True)
            self.progress.emit(1.0)
            self.status.emit("Installazione completata")
            self.finished.emit()
        except Exception as e:
            self.error.emit(str(e))

# -----------------------------------------------------------------------------
# AVVIO APP
# -----------------------------------------------------------------------------
def start_app():
    d = get_launcher_dir()
    py = os.path.join(d, "app.py")
    sys_os = platform.system()
    try:
        if sys_os == "Windows":
            exe = os.path.join(d, "MUSIC WAVVER.exe")
            if os.path.exists(exe):
                subprocess.Popen([exe])
                return
            if os.path.exists(py):
                subprocess.Popen(["python", py])
                return
        elif sys_os == "Linux":
            exe = os.path.join(d, "MUSIC WAVVER")
            if os.path.exists(exe):
                subprocess.Popen([exe])
                return
            if os.path.exists(py):
                subprocess.Popen(["python3", py])
                return
        elif sys_os == "Darwin":
            if os.path.exists(py):
                subprocess.Popen(["python3", py])
                return
        print("ERRORE: app non trovata")
    except Exception as e:
        print(f"ERRORE avvio app: {e}")

# -----------------------------------------------------------------------------
# WIDGET PRINCIPALE (Splash + Schermate)
# -----------------------------------------------------------------------------
class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.lang = self.get_system_language()
        self.setWindowTitle(T("window_title", self.lang))
        self.setFixedSize(WIDTH, HEIGHT)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint
        )
        self.setStyleSheet(f"background-color: {C_BG};")

        # Stack per contenuti
        self.stacked = QStackedWidget(self)
        self.stacked.setGeometry(0, 0, WIDTH, HEIGHT)

        # Crea schermata splash
        self.splash_widget = self.create_splash_widget()
        self.stacked.addWidget(self.splash_widget)

        self.center_on_screen()
        self.show()

        # Avvia animazione (defer di un ciclo event loop così Qt ha le geometrie pronte)
        QTimer.singleShot(0, self.start_splash_animation)

    def get_system_language(self):
        try:
            # Modern way: getlocale() after setlocale
            sys_lang = locale.getlocale()[0]
        except Exception:
            sys_lang = "en"
        if sys_lang:
            code = sys_lang.split("_")[0].lower()
            if code in TRANSLATIONS:
                return code
        return "en"

    def center_on_screen(self):
        screen = QApplication.primaryScreen().availableGeometry()
        x = (screen.width() - WIDTH) // 2   
        y = (screen.height() - HEIGHT) // 2
        self.move(x, y)

    def create_splash_widget(self):
        """Crea la schermata splash con layout verticale centrato."""
        widget = QWidget()
        widget.setStyleSheet(f"background-color: {C_BG};")

        # Layout principale verticale
        main_layout = QVBoxLayout(widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        # Spazio flessibile sopra
        main_layout.addStretch()

        # Contenitore per il logo
        self.logo_label = QLabel()
        logo_path = resource_path("Logo.png")
        pixmap = QPixmap(logo_path)
        if not pixmap.isNull():
            pixmap = pixmap.scaled(200, 200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pixmap)
        else:
            print(f"[WARNING] Logo non caricato da: {logo_path}")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(200, 200)
        self.logo_label.setStyleSheet("background: transparent;")

        # Il logo parte invisibile, poi viene animato con fade-in
        self.logo_opacity = QGraphicsOpacityEffect(self.logo_label)
        self.logo_opacity.setOpacity(0.0)
        self.logo_label.setGraphicsEffect(self.logo_opacity)

        main_layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Spazio dopo il logo
        main_layout.addSpacing(20)

        # Titolo
        self.title_label = QLabel(T("app_name", self.lang))
        # Usa un font generico disponibile su Linux
        title_font = QFont("Sans Serif", 30, QFont.Weight.Bold)
        self.title_label.setFont(title_font)
        self.title_label.setStyleSheet("color: #000000;")
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)

        # Sottotitolo
        self.subtitle_label = QLabel(f"v{CURRENT_VERSION}  by Il Mangia")
        subtitle_font = QFont("Sans Serif", 11)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setStyleSheet("color: #555577;")
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.subtitle_label)

        # Spazio
        main_layout.addSpacing(20)

        # Label di stato
        self.status_label = QLabel("")
        status_font = QFont("Sans Serif", 13)
        self.status_label.setFont(status_font)
        self.status_label.setStyleSheet(f"color: {C_MUTED};")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Spazio flessibile sotto
        main_layout.addStretch()

        return widget

    def start_splash_animation(self):
        """Fade-in del logo tramite opacità (evita problemi di clipping con posizionamento assoluto)."""
        self.logo_anim = QPropertyAnimation(self.logo_opacity, b"opacity")
        self.logo_anim.setDuration(700)
        self.logo_anim.setStartValue(0.0)
        self.logo_anim.setEndValue(1.0)
        self.logo_anim.setEasingCurve(QEasingCurve.Type.OutQuart)
        self.logo_anim.finished.connect(self.start_fade_in_text)
        self.logo_anim.start()

    def start_fade_in_text(self):
        """Fade-in del titolo tramite opacità."""
        self.fade_step = 0
        self.fade_timer = QTimer()
        self.fade_timer.timeout.connect(self._update_title_color)
        self.fade_timer.start(20)

    def _update_title_color(self):
        self.fade_step += 1
        progress = min(self.fade_step / 20, 1.0)
        r = int(0x00 + (0xEA - 0x00) * progress)
        g = int(0x00 + (0xEA - 0x00) * progress)
        b = int(0x00 + (0xEA - 0x00) * progress)
        color = f"#{r:02x}{g:02x}{b:02x}"
        self.title_label.setStyleSheet(f"color: {color};")
        if progress >= 1.0:
            self.fade_timer.stop()
            self.check_updates()

    def check_updates(self):
        self.status_label.setText(T("checking_updates", self.lang))
        self.worker_thread = QThread()
        self.worker = UpdateChecker(self.lang)
        self.worker.moveToThread(self.worker_thread)
        self.worker_thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.on_update_check_done)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)
        self.worker_thread.start()

    def on_update_check_done(self, status, latest, url, all_tags):
        status_text_map = {
            "update_available": "update_available",
            "beta_version": "beta_detected",
            "up_to_date": "version_updated",
            "error": "error_checking"
        }
        text_key = status_text_map.get(status, "checking_updates")
        self.status_label.setText(T(text_key, self.lang))

        if status == "update_available":
            QTimer.singleShot(800, lambda: self.show_update_screen(latest))
        elif status == "beta_version":
            QTimer.singleShot(800, lambda: self.show_beta_screen(latest))
        elif status == "up_to_date":
            QTimer.singleShot(1200, self.launch_or_ffmpeg)
        else:
            QTimer.singleShot(800, self.show_error_screen)

    def launch_or_ffmpeg(self):
        if platform.system() == "Windows" and not ffmpeg_is_available():
            self.show_ffmpeg_screen()
        else:
            self.close()
            start_app()

    def switch_to_widget(self, widget_creator):
        new_widget = widget_creator()
        self.stacked.addWidget(new_widget)
        self.stacked.setCurrentWidget(new_widget)

    # -------------------------------------------------------------------------
    # SCHERMATA AGGIORNAMENTO
    # -------------------------------------------------------------------------
    def show_update_screen(self, latest_ver):
        def create():
            w = QWidget()
            w.setStyleSheet(f"background-color: {C_BG};")
            layout = QVBoxLayout(w)
            layout.setContentsMargins(30, 50, 30, 30)
            layout.setSpacing(10)

            title = QLabel(T("update_title", self.lang))
            title.setFont(QFont("Sans Serif", 22, QFont.Weight.Bold))
            title.setStyleSheet("color: #FF6B6B;")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            info = QLabel(f"{T('current_version', self.lang)}: {CURRENT_VERSION}\n"
                          f"{T('latest_stable', self.lang)}: {latest_ver}")
            info.setFont(QFont("Sans Serif", 15))
            info.setStyleSheet(f"color: {C_TEXT};")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info)

            msg = QLabel(T("update_message", self.lang))
            msg.setFont(QFont("Sans Serif", 13))
            msg.setStyleSheet(f"color: {C_MUTED};")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(msg)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            self.progress_bar.setTextVisible(False)
            self.progress_bar.setFixedHeight(14)
            self.progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: #333344;
                    border-radius: 7px;
                }}
                QProgressBar::chunk {{
                    background-color: {C_GREEN};
                    border-radius: 7px;
                }}
            """)
            self.progress_bar.hide()
            layout.addWidget(self.progress_bar)

            self.progress_status = QLabel("")
            self.progress_status.setFont(QFont("Sans Serif", 11))
            self.progress_status.setStyleSheet(f"color: {C_MUTED};")
            self.progress_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.progress_status.hide()
            layout.addWidget(self.progress_status)

            layout.addSpacing(20)

            btn_dl = QPushButton(T("download_install", self.lang))
            btn_dl.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
            btn_dl.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C_GREEN};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px;
                }}
                QPushButton:hover {{
                    background-color: #388E3C;
                }}
                QPushButton:disabled {{
                    background-color: #555;
                }}
            """)
            btn_dl.clicked.connect(self.download_update)
            layout.addWidget(btn_dl)

            btn_open = QPushButton(T("open_browser", self.lang))
            btn_open.setFont(QFont("Sans Serif", 12))
            btn_open.setStyleSheet(f"""
                QPushButton {{
                    background-color: #334;
                    color: {C_MUTED};
                    border: none;
                    border-radius: 8px;
                    padding: 8px;
                }}
                QPushButton:hover {{
                    background-color: #445;
                }}
            """)
            btn_open.clicked.connect(lambda: webbrowser.open(GITHUB_LATEST_RELEASE_URL))
            layout.addWidget(btn_open)

            btn_skip = QPushButton(T("continue_without", self.lang))
            btn_skip.setFont(QFont("Sans Serif", 13))
            btn_skip.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)
            btn_skip.clicked.connect(self.skip_and_launch)
            layout.addWidget(btn_skip)

            self.dl_btn = btn_dl
            self.skip_btn = btn_skip

            return w
        self.switch_to_widget(create)

    def download_update(self):
        self.dl_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.progress_bar.show()
        self.progress_status.show()

        install_url, fname = get_latest_release_installer()
        if not install_url:
            self.progress_status.setText(T("download_error", self.lang))
            QTimer.singleShot(1500, lambda: webbrowser.open(GITHUB_LATEST_RELEASE_URL))
            QTimer.singleShot(2000, self.close)
            return

        tmp_dir = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, fname)

        self.dl_thread = QThread()
        self.dl_worker = DownloadWorker(install_url, tmp_path)
        self.dl_worker.moveToThread(self.dl_thread)
        self.dl_thread.started.connect(self.dl_worker.run)
        self.dl_worker.progress.connect(lambda p: self.progress_bar.setValue(int(p * 100)))
        self.dl_worker.status.connect(self.progress_status.setText)
        self.dl_worker.finished.connect(self.on_download_finished)
        self.dl_worker.error.connect(self.on_download_error)
        self.dl_thread.start()

    def on_download_finished(self, path):
        self.progress_status.setText(T("download_done", self.lang))
        QTimer.singleShot(800, lambda: self.launch_installer(path))

    def launch_installer(self, path):
        if platform.system() == "Windows":
            os.startfile(path)
        else:
            subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", path])
        QTimer.singleShot(500, self.close)

    def on_download_error(self, err):
        self.progress_status.setText(T("download_error", self.lang))
        QTimer.singleShot(1500, lambda: webbrowser.open(GITHUB_LATEST_RELEASE_URL))
        QTimer.singleShot(2000, self.close)

    def skip_and_launch(self):
        self.close()
        start_app()

    # -------------------------------------------------------------------------
    # SCHERMATA BETA
    # -------------------------------------------------------------------------
    def show_beta_screen(self, latest_ver):
        def create():
            w = QWidget()
            w.setStyleSheet(f"background-color: {C_BG};")
            layout = QVBoxLayout(w)
            layout.setContentsMargins(30, 50, 30, 30)
            layout.setSpacing(10)

            title = QLabel(T("beta_title", self.lang))
            title.setFont(QFont("Sans Serif", 22, QFont.Weight.Bold))
            title.setStyleSheet(f"color: {C_WARN};")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            warn_icon = QLabel("  !  ")
            warn_icon.setFont(QFont("Sans Serif", 40, QFont.Weight.Bold))
            warn_icon.setStyleSheet(f"color: {C_WARN}; background-color: #332800; border-radius: 30px;")
            warn_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            warn_icon.setFixedSize(60, 60)
            layout.addWidget(warn_icon, alignment=Qt.AlignmentFlag.AlignCenter)

            info = QLabel(f"{T('beta_current', self.lang)}: {CURRENT_VERSION}\n"
                          f"{T('latest_stable', self.lang)}: {latest_ver}")
            info.setFont(QFont("Sans Serif", 14))
            info.setStyleSheet(f"color: {C_TEXT};")
            info.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(info)

            warn_msg = QLabel(T("beta_warning", self.lang))
            warn_msg.setFont(QFont("Sans Serif", 13))
            warn_msg.setStyleSheet("color: #FFCC80;")
            warn_msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(warn_msg)

            layout.addSpacing(20)

            btn_stable = QPushButton(T("return_stable", self.lang))
            btn_stable.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
            btn_stable.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C_GREEN};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px;
                }}
                QPushButton:hover {{
                    background-color: #388E3C;
                }}
            """)
            btn_stable.clicked.connect(lambda: webbrowser.open(GITHUB_LATEST_RELEASE_URL))
            layout.addWidget(btn_stable)

            btn_accept = QPushButton(T("accept_risk", self.lang))
            btn_accept.setFont(QFont("Sans Serif", 13))
            btn_accept.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C_RED};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 10px;
                }}
                QPushButton:hover {{
                    background-color: #B71C1C;
                }}
            """)
            btn_accept.clicked.connect(self.skip_and_launch)
            layout.addWidget(btn_accept)

            note = QLabel(T("beta_note", self.lang))
            note.setFont(QFont("Sans Serif", 11))
            note.setStyleSheet(f"color: {C_MUTED};")
            note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(note)

            return w
        self.switch_to_widget(create)

    # -------------------------------------------------------------------------
    # SCHERMATA ERRORE
    # -------------------------------------------------------------------------
    def show_error_screen(self):
        def create():
            w = QWidget()
            w.setStyleSheet(f"background-color: {C_BG};")
            layout = QVBoxLayout(w)
            layout.setContentsMargins(30, 50, 30, 30)
            layout.setSpacing(10)

            err_icon = QLabel("  X  ")
            err_icon.setFont(QFont("Sans Serif", 36, QFont.Weight.Bold))
            err_icon.setStyleSheet(f"color: {C_RED}; background-color: #2A0000; border-radius: 31px;")
            err_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
            err_icon.setFixedSize(62, 62)
            layout.addWidget(err_icon, alignment=Qt.AlignmentFlag.AlignCenter)

            title = QLabel(T("error_title", self.lang))
            title.setFont(QFont("Sans Serif", 20, QFont.Weight.Bold))
            title.setStyleSheet(f"color: {C_RED};")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            msg = QLabel(T("error_message", self.lang))
            msg.setFont(QFont("Sans Serif", 13))
            msg.setStyleSheet(f"color: {C_TEXT};")
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(msg)

            layout.addSpacing(20)

            btn_retry = QPushButton(T("retry_button", self.lang))
            btn_retry.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
            btn_retry.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C_BLUE};
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 12px;
                }}
                QPushButton:hover {{
                    background-color: #1565C0;
                }}
            """)
            btn_retry.clicked.connect(self.restart_app)
            layout.addWidget(btn_retry)

            btn_continue = QPushButton(T("continue_anyway", self.lang))
            btn_continue.setFont(QFont("Sans Serif", 13))
            btn_continue.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)
            btn_continue.clicked.connect(self.skip_and_launch)
            layout.addWidget(btn_continue)

            note = QLabel(T("error_note", self.lang))
            note.setFont(QFont("Sans Serif", 11))
            note.setStyleSheet(f"color: {C_MUTED};")
            note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(note)

            return w
        self.switch_to_widget(create)

    def restart_app(self):
        self.close()
        subprocess.Popen([sys.executable] + sys.argv)
        sys.exit(0)

    # -------------------------------------------------------------------------
    # SCHERMATA FFMPEG
    # -------------------------------------------------------------------------
    def show_ffmpeg_screen(self):
        def create():
            w = QWidget()
            w.setStyleSheet(f"background-color: {C_BG};")
            layout = QVBoxLayout(w)
            layout.setContentsMargins(30, 50, 30, 30)
            layout.setSpacing(10)

            title = QLabel(T("ffmpeg_title", self.lang))
            title.setFont(QFont("Sans Serif", 20, QFont.Weight.Bold))
            title.setStyleSheet(f"color: {C_WARN};")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(title)

            msg = QLabel(T("ffmpeg_message", self.lang))
            msg.setFont(QFont("Sans Serif", 13))
            msg.setStyleSheet(f"color: {C_TEXT};")
            msg.setWordWrap(True)
            msg.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(msg)

            note = QLabel(T("ffmpeg_note", self.lang))
            note.setFont(QFont("Sans Serif", 11))
            note.setStyleSheet(f"color: {C_MUTED};")
            note.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(note)

            self.ff_progress_bar = QProgressBar()
            self.ff_progress_bar.setRange(0, 100)
            self.ff_progress_bar.setValue(0)
            self.ff_progress_bar.setTextVisible(False)
            self.ff_progress_bar.setFixedHeight(14)
            self.ff_progress_bar.setStyleSheet(f"""
                QProgressBar {{
                    border: none;
                    background-color: #332200;
                    border-radius: 7px;
                }}
                QProgressBar::chunk {{
                    background-color: {C_WARN};
                    border-radius: 7px;
                }}
            """)
            self.ff_progress_bar.hide()
            layout.addWidget(self.ff_progress_bar)

            self.ff_status_label = QLabel("")
            self.ff_status_label.setFont(QFont("Sans Serif", 11))
            self.ff_status_label.setStyleSheet(f"color: {C_MUTED};")
            self.ff_status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ff_status_label.hide()
            layout.addWidget(self.ff_status_label)

            layout.addSpacing(20)

            btn_install = QPushButton(T("ffmpeg_install", self.lang))
            btn_install.setFont(QFont("Sans Serif", 14, QFont.Weight.Bold))
            btn_install.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C_WARN};
                    color: black;
                    border: none;
                    border-radius: 10px;
                    padding: 12px;
                }}
                QPushButton:hover {{
                    background-color: #E65100;
                }}
                QPushButton:disabled {{
                    background-color: #555;
                }}
            """)
            btn_install.clicked.connect(self.install_ffmpeg)
            layout.addWidget(btn_install)

            btn_skip = QPushButton(T("ffmpeg_skip", self.lang))
            btn_skip.setFont(QFont("Sans Serif", 13))
            btn_skip.setStyleSheet("""
                QPushButton {
                    background-color: #444;
                    color: white;
                    border: none;
                    border-radius: 10px;
                    padding: 10px;
                }
                QPushButton:hover {
                    background-color: #555;
                }
            """)
            btn_skip.clicked.connect(self.skip_and_launch)
            layout.addWidget(btn_skip)

            self.ff_install_btn = btn_install
            self.ff_skip_btn = btn_skip

            return w
        self.switch_to_widget(create)

    def install_ffmpeg(self):
        self.ff_install_btn.setEnabled(False)
        self.ff_skip_btn.setEnabled(False)
        self.ff_progress_bar.show()
        self.ff_status_label.show()

        self.ff_thread = QThread()
        self.ff_worker = FFmpegInstallWorker()
        self.ff_worker.moveToThread(self.ff_thread)
        self.ff_thread.started.connect(self.ff_worker.run)
        self.ff_worker.progress.connect(lambda p: self.ff_progress_bar.setValue(int(p * 100)))
        self.ff_worker.status.connect(self.ff_status_label.setText)
        self.ff_worker.finished.connect(self.on_ffmpeg_installed)
        self.ff_worker.error.connect(self.on_ffmpeg_error)
        self.ff_thread.start()

    def on_ffmpeg_installed(self):
        self.ff_status_label.setText(T("ffmpeg_done", self.lang))
        QTimer.singleShot(1500, self.skip_and_launch)

    def on_ffmpeg_error(self, err):
        self.ff_status_label.setText(f"{T('ffmpeg_error', self.lang)}: {err}")
        QTimer.singleShot(2000, self.skip_and_launch)

# -----------------------------------------------------------------------------
# WORKER PER CONTROLLO AGGIORNAMENTI
# -----------------------------------------------------------------------------
class UpdateChecker(QObject):
    finished = pyqtSignal(str, str, str, object)

    def __init__(self, lang):
        super().__init__()
        self.lang = lang

    def run(self):
        status, latest, url, all_tags = check_for_updates(self.lang)
        self.finished.emit(status, latest, url, all_tags)

# -----------------------------------------------------------------------------
# MAIN
# -----------------------------------------------------------------------------
def main():
    try:
        locale.setlocale(locale.LC_ALL, "")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(f"""
        QWidget {{
            background-color: {C_BG};
            color: {C_TEXT};
        }}
    """)
    splash = SplashScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
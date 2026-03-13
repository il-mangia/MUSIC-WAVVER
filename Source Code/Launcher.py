#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA - 2026
MMUSIC WAVVER 5.0 Launcher
MADE IN ITALY
"""

import customtkinter as ctk
import subprocess
import os
import sys
import time
import platform
import threading
import zipfile
import shutil
import requests
import webbrowser
import locale
import tempfile
from PIL import Image

# ============================================================================
# CONFIGURAZIONE GLOBALE
# ============================================================================
WIDTH  = 440
HEIGHT = 540

LOGO_START_Y  = -220
LOGO_END_Y    = 55
TITLE_Y       = 290

CURRENT_VERSION = "5.0"

GITHUB_REPO              = "il-mangia/MUSIC-WAVVER"
GITHUB_TAGS_URL          = f"https://api.github.com/repos/{GITHUB_REPO}/tags"
GITHUB_RELEASES_API      = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
GITHUB_LATEST_RELEASE_URL= f"https://github.com/{GITHUB_REPO}/releases/latest"

# FFmpeg: BtbN GitHub Builds (ffmpeg-master-latest-win64-gpl.zip)
FFMPEG_ZIP_URL = (
    "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest"
    "/ffmpeg-master-latest-win64-gpl.zip"
)

# Colori UI
C_BG     = "#1A1A2E"
C_PANEL  = "#16213E"
C_ACCENT = "#7C5CBF"
C_GREEN  = "#4CAF50"
C_RED    = "#E53935"
C_BLUE   = "#2196F3"
C_TEXT   = "#EAEAEA"
C_MUTED  = "#888888"
C_WARN   = "#FFA726"

# ============================================================================
# MULTILINGUA
# ============================================================================
TRANSLATIONS = {
    "it": {
        "app_name":        "MUSIC WAVVER",
        "window_title":    f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates":"Controllo aggiornamenti...",
        "update_available":"Aggiornamento disponibile!",
        "beta_detected":   "Versione beta rilevata!",
        "error_checking":  "Errore nel controllo!",
        "version_updated": "Versione aggiornata",

        "update_title":    "AGGIORNAMENTO DISPONIBILE",
        "current_version": "Versione attuale",
        "latest_stable":   "Ultima stabile",
        "update_message":  "Nuova versione di Music Wavver disponibile.",
        "download_install":"SCARICA E INSTALLA",
        "open_browser":    "Apri nel browser",
        "continue_without":"CONTINUA SENZA AGGIORNARE",
        "downloading_update":"Download in corso...",
        "download_done":   "Download completato. Avvio installer...",
        "download_error":  "Errore nel download. Apertura browser...",

        "beta_title":      "VERSIONE BETA",
        "beta_current":    "Versione in uso",
        "beta_warning":    "Stai usando una versione beta.\nSi consiglia di tornare all'ultima stabile.",
        "return_stable":   "TORNA ALLA VERSIONE STABILE",
        "accept_risk":     "CONTINUA IN OGNI CASO",
        "beta_note":       "Segnala eventuali bug agli sviluppatori.",

        "error_title":     "ERRORE DI CONNESSIONE",
        "error_message":   "Impossibile verificare gli aggiornamenti.\nControlla la connessione Internet.",
        "retry_button":    "RIPROVA",
        "continue_anyway": "CONTINUA COMUNQUE",
        "error_note":      "L'applicazione potrebbe non essere aggiornata.",

        "ffmpeg_title":    "FFMPEG NON TROVATO",
        "ffmpeg_message":  "FFmpeg e' necessario per convertire l'audio.\nVuoi scaricarlo e installarlo automaticamente?\n(~45 MB, nessun admin richiesto)",
        "ffmpeg_install":  "INSTALLA FFMPEG AUTOMATICAMENTE",
        "ffmpeg_skip":     "Installa manualmente",
        "ffmpeg_progress": "Download FFmpeg in corso...",
        "ffmpeg_extract":  "Estrazione in corso...",
        "ffmpeg_done":     "FFmpeg installato correttamente!",
        "ffmpeg_error":    "Errore nell'installazione di FFmpeg.",
        "ffmpeg_note":     "Richiesto per la conversione audio (mp3, flac, ecc.)",

        "checking_for":    "Controllo aggiornamenti per versione",
        "latest_found":    "Ultima versione stabile trovata",
        "update_found":    "Trovato aggiornamento",
        "up_to_date":      "Sei aggiornato",
        "timeout":         "Timeout nel controllo",
        "connection_error":"Errore di connessione",
        "no_tags":         "Nessun tag nel repository",
        "no_stable":       "Nessuna versione stabile",
        "starting_app":    "Avvio applicazione...",
        "opening_release": "Apertura pagina release",
    },
    "en": {
        "app_name":        "MUSIC WAVVER",
        "window_title":    f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates":"Checking for updates...",
        "update_available":"Update available!",
        "beta_detected":   "Beta version detected!",
        "error_checking":  "Error checking updates!",
        "version_updated": "Up to date",

        "update_title":    "UPDATE AVAILABLE",
        "current_version": "Current version",
        "latest_stable":   "Latest stable",
        "update_message":  "A new version of Music Wavver is available.",
        "download_install":"DOWNLOAD & INSTALL",
        "open_browser":    "Open in browser",
        "continue_without":"CONTINUE WITHOUT UPDATING",
        "downloading_update":"Downloading...",
        "download_done":   "Download complete. Launching installer...",
        "download_error":  "Download error. Opening browser...",

        "beta_title":      "BETA VERSION",
        "beta_current":    "Current version",
        "beta_warning":    "You are running a beta version.\nWe recommend returning to the latest stable.",
        "return_stable":   "RETURN TO STABLE VERSION",
        "accept_risk":     "CONTINUE ANYWAY",
        "beta_note":       "Report any bugs to the developers.",

        "error_title":     "CONNECTION ERROR",
        "error_message":   "Unable to check for updates.\nCheck your Internet connection.",
        "retry_button":    "RETRY",
        "continue_anyway": "CONTINUE ANYWAY",
        "error_note":      "Application may not be up to date.",

        "ffmpeg_title":    "FFMPEG NOT FOUND",
        "ffmpeg_message":  "FFmpeg is required to convert audio.\nDo you want to download and install it automatically?\n(~45 MB, no admin required)",
        "ffmpeg_install":  "INSTALL FFMPEG AUTOMATICALLY",
        "ffmpeg_skip":     "Install manually",
        "ffmpeg_progress": "Downloading FFmpeg...",
        "ffmpeg_extract":  "Extracting...",
        "ffmpeg_done":     "FFmpeg installed successfully!",
        "ffmpeg_error":    "Error installing FFmpeg.",
        "ffmpeg_note":     "Required for audio conversion (mp3, flac, etc.)",

        "checking_for":    "Checking updates for version",
        "latest_found":    "Latest stable version found",
        "update_found":    "Update found",
        "up_to_date":      "Up to date",
        "timeout":         "Update check timeout",
        "connection_error":"Connection error",
        "no_tags":         "No tags in repository",
        "no_stable":       "No stable version found",
        "starting_app":    "Launching application...",
        "opening_release": "Opening release page",
    },
    "es": {
        "app_name":        "MUSIC WAVVER",
        "window_title":    f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates":"Buscando actualizaciones...",
        "update_available":"Actualizacion disponible!",
        "beta_detected":   "Version beta detectada!",
        "error_checking":  "Error al verificar!",
        "version_updated": "Actualizado",

        "update_title":    "ACTUALIZACION DISPONIBLE",
        "current_version": "Version actual",
        "latest_stable":   "Ultima estable",
        "update_message":  "Nueva version de Music Wavver disponible.",
        "download_install":"DESCARGAR E INSTALAR",
        "open_browser":    "Abrir en navegador",
        "continue_without":"CONTINUAR SIN ACTUALIZAR",
        "downloading_update":"Descargando...",
        "download_done":   "Descarga completa. Iniciando instalador...",
        "download_error":  "Error de descarga. Abriendo navegador...",

        "beta_title":      "VERSION BETA",
        "beta_current":    "Version en uso",
        "beta_warning":    "Estas usando una version beta.\nSe recomienda volver a la ultima estable.",
        "return_stable":   "VOLVER A VERSION ESTABLE",
        "accept_risk":     "CONTINUAR DE TODAS FORMAS",
        "beta_note":       "Reporta los errores a los desarrolladores.",

        "error_title":     "ERROR DE CONEXION",
        "error_message":   "No se pueden verificar actualizaciones.\nVerifica tu conexion a Internet.",
        "retry_button":    "REINTENTAR",
        "continue_anyway": "CONTINUAR",
        "error_note":      "La aplicacion puede no estar actualizada.",

        "ffmpeg_title":    "FFMPEG NO ENCONTRADO",
        "ffmpeg_message":  "FFmpeg es necesario para convertir audio.\nDescargar e instalar automaticamente?\n(~45 MB, sin admin)",
        "ffmpeg_install":  "INSTALAR FFMPEG",
        "ffmpeg_skip":     "Instalar manualmente",
        "ffmpeg_progress": "Descargando FFmpeg...",
        "ffmpeg_extract":  "Extrayendo...",
        "ffmpeg_done":     "FFmpeg instalado correctamente!",
        "ffmpeg_error":    "Error al instalar FFmpeg.",
        "ffmpeg_note":     "Requerido para conversion de audio",

        "checking_for":    "Verificando version",
        "latest_found":    "Ultima version estable encontrada",
        "update_found":    "Actualizacion encontrada",
        "up_to_date":      "Actualizado",
        "timeout":         "Timeout",
        "connection_error":"Error de conexion",
        "no_tags":         "Sin tags en repositorio",
        "no_stable":       "Sin version estable",
        "starting_app":    "Iniciando aplicacion...",
        "opening_release": "Abriendo pagina de release",
    },
    "de": {
        "app_name":        "MUSIC WAVVER",
        "window_title":    f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates":"Suche nach Updates...",
        "update_available":"Update verfugbar!",
        "beta_detected":   "Beta-Version erkannt!",
        "error_checking":  "Fehler beim Pruefen!",
        "version_updated": "Aktuell",

        "update_title":    "UPDATE VERFUGBAR",
        "current_version": "Aktuelle Version",
        "latest_stable":   "Neueste stabile",
        "update_message":  "Neue Version von Music Wavver verfugbar.",
        "download_install":"HERUNTERLADEN & INSTALLIEREN",
        "open_browser":    "Im Browser offnen",
        "continue_without":"OHNE UPDATE FORTFAHREN",
        "downloading_update":"Download laeuft...",
        "download_done":   "Download abgeschlossen. Installer wird gestartet...",
        "download_error":  "Download-Fehler. Browser wird geoffnet...",

        "beta_title":      "BETA-VERSION",
        "beta_current":    "Verwendete Version",
        "beta_warning":    "Sie verwenden eine Beta-Version.\nZuruck zur stabilen Version empfohlen.",
        "return_stable":   "ZUR STABILEN VERSION",
        "accept_risk":     "TROTZDEM FORTFAHREN",
        "beta_note":       "Bitte Fehler an die Entwickler melden.",

        "error_title":     "VERBINDUNGSFEHLER",
        "error_message":   "Updates koennen nicht geprueft werden.\nBitte Internetverbindung pruefen.",
        "retry_button":    "ERNEUT VERSUCHEN",
        "continue_anyway": "TROTZDEM FORTFAHREN",
        "error_note":      "Anwendung ist moeglicherweise nicht aktuell.",

        "ffmpeg_title":    "FFMPEG NICHT GEFUNDEN",
        "ffmpeg_message":  "FFmpeg wird fuer die Audio-Konvertierung benoetigt.\nAutomatisch herunterladen?\n(~45 MB, kein Admin erforderlich)",
        "ffmpeg_install":  "FFMPEG INSTALLIEREN",
        "ffmpeg_skip":     "Manuell installieren",
        "ffmpeg_progress": "FFmpeg wird heruntergeladen...",
        "ffmpeg_extract":  "Wird entpackt...",
        "ffmpeg_done":     "FFmpeg erfolgreich installiert!",
        "ffmpeg_error":    "Fehler bei der FFmpeg-Installation.",
        "ffmpeg_note":     "Erforderlich fur Audio-Konvertierung",

        "checking_for":    "Update-Prufung fur Version",
        "latest_found":    "Neueste stabile Version gefunden",
        "update_found":    "Update gefunden",
        "up_to_date":      "Aktuell",
        "timeout":         "Timeout",
        "connection_error":"Verbindungsfehler",
        "no_tags":         "Keine Tags im Repository",
        "no_stable":       "Keine stabile Version gefunden",
        "starting_app":    "Anwendung wird gestartet...",
        "opening_release": "Release-Seite wird geoffnet",
    },
}


def T(key, lang):
    return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)


# ============================================================================
# LINGUA DI SISTEMA
# ============================================================================

def get_system_language():
    try:
        try:
            sys_lang = locale.getlocale()[0]
        except Exception:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                sys_lang, _ = locale.getdefaultlocale()
        if sys_lang:
            code = sys_lang.split("_")[0].lower()
            if code in TRANSLATIONS:
                return code
        if platform.system() == "Windows":
            try:
                import ctypes
                lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
                mapping = {1040: "it", 1033: "en", 3082: "es", 1031: "de"}
                if lang_id in mapping:
                    return mapping[lang_id]
            except Exception:
                pass
    except Exception:
        pass
    return "en"


# ============================================================================
# UTILITY PATHS
# ============================================================================

def get_launcher_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(get_launcher_dir(), relative_path)


def get_ffmpeg_install_dir():
    """Cartella dove installiamo ffmpeg accanto all'eseguibile."""
    return os.path.join(get_launcher_dir(), "ffmpeg", "bin")


def ffmpeg_is_available():
    if shutil.which("ffmpeg"):
        return True
    ffmpeg_local = os.path.join(get_ffmpeg_install_dir(), "ffmpeg.exe")
    return os.path.isfile(ffmpeg_local)


# ============================================================================
# VERSIONI
# ============================================================================

def compare_versions(v1, v2):
    try:
        p1 = list(map(int, v1.split(".")))
        p2 = list(map(int, v2.split(".")))
        m  = max(len(p1), len(p2))
        p1 += [0] * (m - len(p1))
        p2 += [0] * (m - len(p2))
        for a, b in zip(p1, p2):
            if a > b: return  1
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


# ============================================================================
# DOWNLOAD INSTALLER GITHUB
# ============================================================================

def get_latest_release_installer():
    """
    Cerca il primo asset .exe nell'ultima release GitHub.
    Ritorna (download_url, filename) o (None, None).
    """
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


def download_file_with_progress(url, dest_path, progress_cb, label_cb=None):
    """
    Scarica un file mostrando il progresso (0.0 - 1.0).
    progress_cb(float), label_cb(str)
    """
    headers = {"User-Agent": "MusicWavver-Launcher"}
    r = requests.get(url, stream=True, timeout=60, headers=headers)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    downloaded = 0
    with open(dest_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=16384):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)
                if total > 0:
                    progress_cb(downloaded / total)
                if label_cb and total > 0:
                    mb_d = downloaded / 1_048_576
                    mb_t = total / 1_048_576
                    label_cb(f"{mb_d:.1f} MB / {mb_t:.1f} MB")


# ============================================================================
# INSTALL APP (scarica l'exe installer da GitHub e lo avvia)
# ============================================================================

def download_and_install_update(root, lang, status_lbl, prog_bar):
    """Chiamato in thread separato. Scarica l'installer e lo lancia."""
    def set_status(text):
        root.after(0, lambda: status_lbl.configure(text=text))

    def set_progress(val):
        root.after(0, lambda: prog_bar.set(val))

    set_status(T("downloading_update", lang))

    try:
        install_url, fname = get_latest_release_installer()
        if not install_url:
            raise RuntimeError("Nessun installer .exe trovato nella release.")

        tmp_dir  = tempfile.mkdtemp()
        tmp_path = os.path.join(tmp_dir, fname)

        def lbl_cb(text):
            set_status(f"{T('downloading_update', lang)}  {text}")

        download_file_with_progress(install_url, tmp_path, set_progress, lbl_cb)

        set_status(T("download_done", lang))
        set_progress(1.0)
        time.sleep(0.8)

        # Avvia installer
        if platform.system() == "Windows":
            os.startfile(tmp_path)
        else:
            subprocess.Popen(["open" if platform.system() == "Darwin" else "xdg-open", tmp_path])

        root.after(500, root.destroy)

    except Exception as e:
        print(f"download_and_install_update error: {e}")
        set_status(T("download_error", lang))
        time.sleep(1.5)
        webbrowser.open(GITHUB_LATEST_RELEASE_URL)
        root.after(500, root.destroy)


# ============================================================================
# INSTALL FFMPEG (Windows, senza admin, PATH utente)
# ============================================================================

def install_ffmpeg_windows(root, lang, status_lbl, prog_bar, done_cb):
    """
    Scarica il zip di FFmpeg da BtbN, estrae ffmpeg.exe nella cartella app,
    aggiunge al PATH utente (HKCU, nessun admin necessario).
    """
    def set_status(text):
        root.after(0, lambda: status_lbl.configure(text=text))

    def set_progress(val):
        root.after(0, lambda: prog_bar.set(val))

    try:
        install_dir = get_ffmpeg_install_dir()
        os.makedirs(install_dir, exist_ok=True)

        tmp_dir  = tempfile.mkdtemp(prefix="mw_ffmpeg_")
        zip_path = os.path.join(tmp_dir, "ffmpeg.zip")

        set_status(T("ffmpeg_progress", lang))

        def lbl_cb(text):
            set_status(f"{T('ffmpeg_progress', lang)}  {text}")

        download_file_with_progress(FFMPEG_ZIP_URL, zip_path, set_progress, lbl_cb)

        set_status(T("ffmpeg_extract", lang))
        set_progress(0)

        # Estrai solo ffmpeg.exe dal zip (evita di estrarre tutto)
        ffmpeg_exe_dest = os.path.join(install_dir, "ffmpeg.exe")
        with zipfile.ZipFile(zip_path, "r") as zf:
            names = zf.namelist()
            # Cerca ffmpeg.exe all'interno della struttura del zip
            target = None
            for n in names:
                if n.endswith("bin/ffmpeg.exe") or n.endswith("bin\\ffmpeg.exe"):
                    target = n
                    break
            if not target:
                # Fallback: cerca qualsiasi ffmpeg.exe
                for n in names:
                    if os.path.basename(n).lower() == "ffmpeg.exe":
                        target = n
                        break
            if not target:
                raise FileNotFoundError("ffmpeg.exe non trovato nel file ZIP.")

            # Estrai solo il file necessario
            with zf.open(target) as src, open(ffmpeg_exe_dest, "wb") as dst:
                shutil.copyfileobj(src, dst)

        set_progress(0.9)

        # Aggiungi al PATH utente (HKCU - nessun admin)
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
            # Notifica Windows della modifica PATH
            import ctypes
            HWND_BROADCAST   = 0xFFFF
            WM_SETTINGCHANGE = 0x001A
            ctypes.windll.user32.SendMessageW(HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment")
        except Exception as e_reg:
            print(f"PATH update warning: {e_reg}")

        # Pulizia
        try:
            shutil.rmtree(tmp_dir, ignore_errors=True)
        except Exception:
            pass

        set_progress(1.0)
        set_status(T("ffmpeg_done", lang))
        time.sleep(1.5)
        root.after(0, done_cb)

    except Exception as e:
        print(f"install_ffmpeg_windows error: {e}")
        set_status(f"{T('ffmpeg_error', lang)}: {e}")
        time.sleep(2)
        root.after(0, done_cb)


# ============================================================================
# AVVIO APP
# ============================================================================

def start_app():
    d = get_launcher_dir()
    py   = os.path.join(d, "app.py")
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


# ============================================================================
# ANIMAZIONE
# ============================================================================

def ease_out_quart(t):
    t = 1 - t
    return 1 - (t * t * t * t)


def get_center():
    import tkinter as tk
    tmp = tk.Tk(); tmp.withdraw()
    sw, sh = tmp.winfo_screenwidth(), tmp.winfo_screenheight()
    tmp.destroy()
    return f"{WIDTH}x{HEIGHT}+{(sw - WIDTH)//2}+{(sh - HEIGHT)//2}"


# ============================================================================
# SCHERMATA PROGRESSO (riusabile per update + ffmpeg)
# ============================================================================

def clear_window(root):
    for w in root.winfo_children():
        w.destroy()
    root.configure(fg_color=C_BG)


def make_progress_screen(root, title_text, message_text, title_color=C_ACCENT):
    """
    Costruisce una schermata con titolo, messaggio, progress bar e label stato.
    Ritorna (status_label, progress_bar).
    """
    clear_window(root)

    ctk.CTkLabel(
        root, text=title_text,
        font=("Segoe UI", 22, "bold"),
        text_color=title_color,
    ).place(x=WIDTH//2, y=90, anchor="center")

    ctk.CTkLabel(
        root, text=message_text,
        font=("Segoe UI", 13),
        text_color=C_TEXT,
        justify="center",
    ).place(x=WIDTH//2, y=155, anchor="center")

    prog = ctk.CTkProgressBar(root, width=340, height=14,
                               progress_color=title_color,
                               fg_color="#333344")
    prog.set(0)
    prog.place(x=WIDTH//2, y=240, anchor="center")

    lbl = ctk.CTkLabel(root, text="", font=("Segoe UI", 12),
                        text_color=C_MUTED)
    lbl.place(x=WIDTH//2, y=275, anchor="center")

    return lbl, prog


# ============================================================================
# SCHERMATE UPDATE / BETA / ERRORE / FFMPEG
# ============================================================================

def show_update_screen(root, latest_ver, lang):
    clear_window(root)

    ctk.CTkLabel(root, text=T("update_title", lang),
                 font=("Segoe UI", 22, "bold"),
                 text_color="#FF6B6B").place(x=WIDTH//2, y=75, anchor="center")

    ctk.CTkLabel(
        root,
        text=(
            f"{T('current_version', lang)}: {CURRENT_VERSION}\n"
            f"{T('latest_stable',   lang)}: {latest_ver}"
        ),
        font=("Segoe UI", 15), text_color=C_TEXT,
    ).place(x=WIDTH//2, y=135, anchor="center")

    ctk.CTkLabel(root, text=T("update_message", lang),
                 font=("Segoe UI", 13), text_color=C_MUTED,
                 ).place(x=WIDTH//2, y=185, anchor="center")

    # Progress bar (nascosta finche' non si preme download)
    prog = ctk.CTkProgressBar(root, width=320, height=12,
                               progress_color=C_GREEN, fg_color="#333344")
    prog.set(0)
    prog.place(x=WIDTH//2, y=285, anchor="center")
    prog.place_forget()

    status_lbl = ctk.CTkLabel(root, text="", font=("Segoe UI", 11),
                               text_color=C_MUTED)
    status_lbl.place(x=WIDTH//2, y=315, anchor="center")
    status_lbl.place_forget()

    def do_download():
        prog.place(x=WIDTH//2, y=285, anchor="center")
        status_lbl.place(x=WIDTH//2, y=315, anchor="center")
        dl_btn.configure(state="disabled")
        skip_btn.configure(state="disabled")
        threading.Thread(
            target=download_and_install_update,
            args=(root, lang, status_lbl, prog),
            daemon=True
        ).start()

    dl_btn = ctk.CTkButton(
        root,
        text=T("download_install", lang),
        font=("Segoe UI", 14, "bold"),
        fg_color=C_GREEN, hover_color="#388E3C",
        width=300, height=44, corner_radius=10,
        command=do_download,
    )
    dl_btn.place(x=WIDTH//2, y=235, anchor="center")

    ctk.CTkButton(
        root,
        text=T("open_browser", lang),
        font=("Segoe UI", 12),
        fg_color="#334", hover_color="#445", text_color=C_MUTED,
        width=150, height=30, corner_radius=8,
        command=lambda: webbrowser.open(GITHUB_LATEST_RELEASE_URL),
    ).place(x=WIDTH//2, y=365, anchor="center")

    skip_btn = ctk.CTkButton(
        root,
        text=T("continue_without", lang),
        font=("Segoe UI", 13),
        fg_color="#444", hover_color="#555",
        width=300, height=38, corner_radius=10,
        command=lambda: [root.destroy(), start_app()],
    )
    skip_btn.place(x=WIDTH//2, y=410, anchor="center")


def show_beta_screen(root, latest_ver, lang):
    clear_window(root)

    ctk.CTkLabel(root, text=T("beta_title", lang),
                 font=("Segoe UI", 22, "bold"),
                 text_color=C_WARN).place(x=WIDTH//2, y=70, anchor="center")

    ctk.CTkLabel(root, text="  !  ", font=("Segoe UI", 40, "bold"),
                 text_color=C_WARN, fg_color="#332800",
                 corner_radius=50, width=60, height=60,
                 ).place(x=WIDTH//2, y=128, anchor="center")

    ctk.CTkLabel(
        root,
        text=(
            f"{T('beta_current', lang)}: {CURRENT_VERSION}\n"
            f"{T('latest_stable', lang)}: {latest_ver}"
        ),
        font=("Segoe UI", 14), text_color=C_TEXT,
    ).place(x=WIDTH//2, y=185, anchor="center")

    ctk.CTkLabel(root, text=T("beta_warning", lang),
                 font=("Segoe UI", 13), text_color="#FFCC80",
                 justify="center").place(x=WIDTH//2, y=245, anchor="center")

    ctk.CTkButton(
        root,
        text=T("return_stable", lang),
        font=("Segoe UI", 14, "bold"),
        fg_color=C_GREEN, hover_color="#388E3C",
        width=300, height=44, corner_radius=10,
        command=lambda: webbrowser.open(GITHUB_LATEST_RELEASE_URL),
    ).place(x=WIDTH//2, y=320, anchor="center")

    ctk.CTkButton(
        root,
        text=T("accept_risk", lang),
        font=("Segoe UI", 13),
        fg_color=C_RED, hover_color="#B71C1C",
        width=300, height=38, corner_radius=10,
        command=lambda: [root.destroy(), start_app()],
    ).place(x=WIDTH//2, y=378, anchor="center")

    ctk.CTkLabel(root, text=T("beta_note", lang),
                 font=("Segoe UI", 11), text_color=C_MUTED,
                 justify="center").place(x=WIDTH//2, y=445, anchor="center")


def show_error_screen(root, lang):
    clear_window(root)

    ctk.CTkLabel(root, text="  X  ", font=("Segoe UI", 36, "bold"),
                 text_color=C_RED, fg_color="#2A0000",
                 corner_radius=50, width=62, height=62,
                 ).place(x=WIDTH//2, y=100, anchor="center")

    ctk.CTkLabel(root, text=T("error_title", lang),
                 font=("Segoe UI", 20, "bold"),
                 text_color=C_RED).place(x=WIDTH//2, y=155, anchor="center")

    ctk.CTkLabel(root, text=T("error_message", lang),
                 font=("Segoe UI", 13), text_color=C_TEXT,
                 justify="center").place(x=WIDTH//2, y=215, anchor="center")

    ctk.CTkButton(
        root,
        text=T("retry_button", lang),
        font=("Segoe UI", 14, "bold"),
        fg_color=C_BLUE, hover_color="#1565C0",
        width=220, height=42, corner_radius=10,
        command=lambda: [root.destroy(), main()],
    ).place(x=WIDTH//2, y=300, anchor="center")

    ctk.CTkButton(
        root,
        text=T("continue_anyway", lang),
        font=("Segoe UI", 13),
        fg_color="#444", hover_color="#555",
        width=220, height=38, corner_radius=10,
        command=lambda: [root.destroy(), start_app()],
    ).place(x=WIDTH//2, y=358, anchor="center")

    ctk.CTkLabel(root, text=T("error_note", lang),
                 font=("Segoe UI", 11), text_color=C_MUTED,
                 ).place(x=WIDTH//2, y=420, anchor="center")


def show_ffmpeg_screen(root, lang, on_done):
    """
    Schermata FFmpeg non trovato (solo Windows).
    on_done: callable da invocare dopo installazione o skip.
    """
    clear_window(root)

    ctk.CTkLabel(root, text=T("ffmpeg_title", lang),
                 font=("Segoe UI", 20, "bold"),
                 text_color=C_WARN).place(x=WIDTH//2, y=75, anchor="center")

    ctk.CTkLabel(root, text=T("ffmpeg_message", lang),
                 font=("Segoe UI", 13), text_color=C_TEXT,
                 justify="center", wraplength=360,
                 ).place(x=WIDTH//2, y=155, anchor="center")

    ctk.CTkLabel(root, text=T("ffmpeg_note", lang),
                 font=("Segoe UI", 11), text_color=C_MUTED,
                 ).place(x=WIDTH//2, y=225, anchor="center")

    prog = ctk.CTkProgressBar(root, width=320, height=12,
                               progress_color=C_WARN, fg_color="#332200")
    prog.set(0)
    prog.place(x=WIDTH//2, y=310, anchor="center")
    prog.place_forget()

    status_lbl = ctk.CTkLabel(root, text="", font=("Segoe UI", 11),
                               text_color=C_MUTED)
    status_lbl.place(x=WIDTH//2, y=340, anchor="center")
    status_lbl.place_forget()

    install_btn = [None]
    skip_btn_ref = [None]

    def do_install():
        prog.place(x=WIDTH//2, y=310, anchor="center")
        status_lbl.place(x=WIDTH//2, y=345, anchor="center")
        install_btn[0].configure(state="disabled")
        skip_btn_ref[0].configure(state="disabled")
        threading.Thread(
            target=install_ffmpeg_windows,
            args=(root, lang, status_lbl, prog, on_done),
            daemon=True
        ).start()

    install_btn[0] = ctk.CTkButton(
        root,
        text=T("ffmpeg_install", lang),
        font=("Segoe UI", 14, "bold"),
        fg_color=C_WARN, hover_color="#E65100", text_color="#000",
        width=300, height=44, corner_radius=10,
        command=do_install,
    )
    install_btn[0].place(x=WIDTH//2, y=268, anchor="center")

    skip_btn_ref[0] = ctk.CTkButton(
        root,
        text=T("ffmpeg_skip", lang),
        font=("Segoe UI", 13),
        fg_color="#444", hover_color="#555",
        width=200, height=36, corner_radius=10,
        command=on_done,
    )
    skip_btn_ref[0].place(x=WIDTH//2, y=390, anchor="center")


# ============================================================================
# MAIN
# ============================================================================

def main():
    lang = get_system_language()
    print(f"Lingua: {lang} | Versione: {CURRENT_VERSION} | OS: {platform.platform()}")

    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.geometry(get_center())
    root.title(T("window_title", lang))
    root.resizable(False, False)
    root.configure(fg_color=C_BG)
    root.attributes("-topmost", True)

    # ── Logo ──────────────────────────────────────────────────────────────────
    logo_path = resource_path("Logo.png")
    try:
        pil_img = Image.open(logo_path)
        img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 200))
    except Exception as e:
        print(f"Logo non trovato: {e}")
        root.destroy(); return

    logo = ctk.CTkLabel(root, text="", image=img, fg_color="transparent")
    logo.place(x=WIDTH//2, y=LOGO_START_Y, anchor="n")

    # ── Titolo ────────────────────────────────────────────────────────────────
    title = ctk.CTkLabel(
        root,
        text=T("app_name", lang),
        font=("Segoe UI", 30, "bold"),
        text_color="#000000",
    )
    title.place(x=WIDTH//2, y=TITLE_Y, anchor="center")

    subtitle = ctk.CTkLabel(
        root,
        text=f"v{CURRENT_VERSION}  by Il Mangia",
        font=("Segoe UI", 11),
        text_color="#555577",
    )
    subtitle.place(x=WIDTH//2, y=TITLE_Y + 32, anchor="center")

    status_lbl = ctk.CTkLabel(
        root, text="",
        font=("Segoe UI", 13),
        text_color=C_MUTED,
    )
    status_lbl.place(x=WIDTH//2, y=TITLE_Y + 65, anchor="center")

    # ─────────────────────────────────────────────────────────────────────────
    # 1. ANIMAZIONE LOGO (slide)
    FPS = 60
    SLIDE_S = 0.6
    SLIDE_F = int(SLIDE_S * FPS)
    y_range = LOGO_END_Y - LOGO_START_Y
    for frame in range(SLIDE_F + 1):
        t = ease_out_quart(frame / SLIDE_F)
        logo.place(x=WIDTH//2, y=LOGO_START_Y + y_range * t, anchor="n")
        root.update(); time.sleep(1/FPS)

    time.sleep(0.1)

    # 2. FADE-IN TESTO
    FADE_S = 0.4
    FADE_F = int(FADE_S * FPS)
    for frame in range(FADE_F + 1):
        t   = frame / FADE_F
        val = min(255, int(255 * t * t))
        col = f"#{val:02x}{val:02x}{val:02x}"
        title.configure(text_color=col)
        root.update(); time.sleep(1/FPS)

    subtitle.configure(text_color="#555577")
    time.sleep(0.4)

    # 3. CONTROLLO AGGIORNAMENTI
    status_lbl.configure(text=T("checking_updates", lang))
    root.update()

    status, latest, url, all_tags = check_for_updates(lang)

    def launch_or_ffmpeg():
        """Dopo update check OK: controlla ffmpeg (solo Windows), poi avvia app."""
        if platform.system() == "Windows" and not ffmpeg_is_available():
            show_ffmpeg_screen(root, lang, on_done=lambda: [root.destroy(), start_app()])
        else:
            root.destroy()
            start_app()

    # 4. FADE-OUT e passaggio alla schermata appropriata
    def fade_out_then(callback):
        FADE_OUT_S = 0.25
        FADE_OUT_F = int(FADE_OUT_S * FPS)
        for frame in range(FADE_OUT_F + 1):
            alpha = 1 - frame / FADE_OUT_F
            root.attributes("-alpha", alpha)
            root.update(); time.sleep(1/FPS)
        root.attributes("-alpha", 1)
        callback()

    if status == "update_available":
        status_lbl.configure(text=T("update_available", lang))
        root.update(); time.sleep(0.8)
        fade_out_then(lambda: show_update_screen(root, latest, lang))

    elif status == "beta_version":
        status_lbl.configure(text=T("beta_detected", lang))
        root.update(); time.sleep(0.8)
        fade_out_then(lambda: show_beta_screen(root, latest, lang))

    elif status == "up_to_date":
        status_lbl.configure(text=T("version_updated", lang))
        root.update(); time.sleep(1.2)
        fade_out_then(launch_or_ffmpeg)
        return  # root.destroy() gia' chiamato in launch_or_ffmpeg

    else:  # error
        status_lbl.configure(text=T("error_checking", lang))
        root.update(); time.sleep(0.8)
        fade_out_then(lambda: show_error_screen(root, lang))

    root.mainloop()


if __name__ == "__main__":
    main()
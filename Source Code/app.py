#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA - 2026
MUSIC WAVVER 5.0
MADE IN ITALY
"""

import os
import sys
import json
import threading
import queue
import logging
import platform
import time
import shutil
import re
import subprocess
import requests
from urllib.parse import urlparse, parse_qs
import importlib.util
import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk, PhotoImage, Menu
from tkinter.ttk import Treeview, Style
from yt_dlp import YoutubeDL  # type: ignore
from PIL import Image, ImageTk
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, TCON, APIC, error as ID3Error

# ── Tema iniziale ──────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# ── Palette colori ─────────────────────────────────────────────────────────────
C_BG     = "#1A1A2E"
C_PANEL  = "#16213E"
C_CARD   = "#0F3460"
C_ACCENT = "#7C5CBF"
C_GREEN  = "#4CAF50"
C_RED    = "#E53935"
C_BLUE   = "#2196F3"
C_WARN   = "#FFA726"
C_TEXT   = "#EAEAEA"
C_MUTED  = "#888899"
C_BORDER = "#2A2A4A"

# ── File paths ─────────────────────────────────────────────────────────────────
LOG_FILE          = "ytdownloader.log"
SETTINGS_FILE     = "settings.json"
LANGUAGES_FILE    = "languages.json"
PLAYLIST_LOG_FILE = "playlist_urls.log"

# ── Azzera log all'avvio ───────────────────────────────────────────────────────
try:
    open(LOG_FILE, "w", encoding="utf-8").close()
except Exception:
    pass

logging.basicConfig(
    filename=LOG_FILE, level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def log(msg, level="info"):
    print(msg)
    try:
        getattr(logging, level)(msg)
    except Exception:
        logging.info(msg)


# ==============================================================================
#  IMPORT DINAMICO playlists.py  (compatibile PyInstaller --onefile e --onedir)
# ==============================================================================

def _find_playlists_module():
    """Restituisce il path assoluto di playlists.py, o None se non trovato."""
    candidates = []
    # 1. Accanto all'exe (PyInstaller --onefile)
    if getattr(sys, "frozen", False):
        candidates.append(os.path.join(os.path.dirname(sys.executable), "playlists.py"))
    # 2. Bundle temp dir (PyInstaller --onedir)
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        candidates.append(os.path.join(meipass, "playlists.py"))
    # 3. Cartella dello script sorgente
    try:
        candidates.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlists.py"))
    except NameError:
        pass
    # 4. Working directory
    candidates.append(os.path.join(os.getcwd(), "playlists.py"))

    for p in candidates:
        if os.path.isfile(p):
            return p
    return None


def _import_playlists():
    path = _find_playlists_module()
    if not path:
        return None, None
    try:
        spec   = importlib.util.spec_from_file_location("playlists", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module, path
    except Exception as e:
        log(f"ERRORE import playlists.py: {e}", "error")
        return None, None


_playlists_mod, _playlists_path = _import_playlists()

if _playlists_mod is not None:
    open_playlist_downloader = _playlists_mod.open_playlist_downloader
    PLAYLIST_MODULE_AVAILABLE = True
    log(f"Playlists: import riuscito da {_playlists_path}")
else:
    open_playlist_downloader = None
    PLAYLIST_MODULE_AVAILABLE = False
    _missing_paths = []
    if getattr(sys, "frozen", False):
        _missing_paths.append(os.path.join(os.path.dirname(sys.executable), "playlists.py"))
    try:
        _missing_paths.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "playlists.py"))
    except NameError:
        pass
    _missing_paths.append(os.path.join(os.getcwd(), "playlists.py"))
    PLAYLIST_MODULE_ERROR = (
        "Il file 'playlists.py' non e' stato trovato.\n\n"
        "Assicurati che sia nella stessa cartella dell'applicazione.\n\n"
        "Percorsi cercati:\n" + "\n".join(f"  - {p}" for p in _missing_paths)
    )
    log("ATTENZIONE: playlists.py non trovato — download playlist disabilitato.")


# ==============================================================================
#  LINGUE
# ==============================================================================

def load_languages():
    if not os.path.exists(LANGUAGES_FILE):
        # Fallback minimale italiano
        return {"it": {
            "welcome": "MUSIC WAVVER 5.0",
            "ready": "Pronto",
            "search_btn": "Cerca / Incolla link",
            "download_btn": "Download selezionato",
            "play_btn": "Riproduci",
            "searching": "Ricerca in corso...",
            "complete": "Download completato",
            "complete_msg": "Download terminato con successo!",
            "settings": "Impostazioni",
            "open_log": "Apri log",
            "open_playlist_log": "Apri Traccia Playlist",
            "agreement_title": "Accordo legale",
            "agreement_text": "Questo software e' solo per uso personale. Accetti i Termini di Servizio di YouTube?",
            "agreement_close": "Non hai accettato l'accordo. Il programma si chiudera'.",
            "playlist_prompt_title": "Playlist Rilevata",
            "playlist_prompt_text": "Hai incollato un link con una playlist. Cosa vuoi scaricare?",
            "playlist_prompt_single": "Solo il video in riproduzione",
            "playlist_prompt_full": "Intera playlist",
            "playlist_prompt_error_no_v": "L'URL e' solo una playlist. Avvio download playlist...",
            "select_download_folder": "Seleziona cartella download",
            "change_folder": "Cambia",
            "format_label": "Formato:",
            "search_timeout_label": "Timeout ricerca (secondi):",
            "speed_limit_label": "Velocita' download (es. 500K, 2M, 0=illimitato):",
            "language_label": "Lingua:",
            "theme_label": "Tema interfaccia:",
            "save_settings": "Salva",
            "settings_title": "Impostazioni",
            "download_folder_label": "Cartella download:",
            "id3_enable_label": "Abilita scrittura ID3 Tag automatica per file MP3",
            "ffmpeg_missing_title": "FFmpeg Non Trovato",
            "ffmpeg_missing_windows": "FFmpeg e' richiesto.\n\nInstalla con:\n  winget install Gyan.FFmpeg",
            "ffmpeg_missing_linux": "FFmpeg e' richiesto.\n\nInstalla con:\n  sudo apt install ffmpeg",
            "ffmpeg_close_app": "Chiudi Applicazione",
            "updater_prompt_title": "Aggiornamento Consigliato",
            "updater_prompt_text": "Vuoi aggiornare yt-dlp ora?",
            "updater_running": "Aggiornamento yt-dlp in corso...",
            "updater_log_title": "Log Aggiornamento",
            "updater_success": "Aggiornamento completato!",
            "updater_fail": "Aggiornamento fallito.",
            "updater_skipped": "Aggiornamento saltato.",
        }}
    try:
        with open(LANGUAGES_FILE, "r", encoding="utf-8") as f:
            langs = json.load(f)
        log("File lingue caricato correttamente.")
        return langs
    except Exception as e:
        log(f"ERRORE caricamento lingue: {e}", "error")
        sys.exit(1)


LANGUAGES = load_languages()


def T(key):
    lang = SETTINGS.get("language", "it") if "SETTINGS" in globals() else "it"
    return (
        LANGUAGES.get(lang, {}).get(key)
        or LANGUAGES.get("it", {}).get(key)
        or key
    )


# ==============================================================================
#  IMPOSTAZIONI
# ==============================================================================

DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Music")
_user_lang = (os.getenv("LANG") or "it")[:2]

DEFAULT_SETTINGS = {
    "download_dir":       DEFAULT_DOWNLOAD_DIR,
    "theme":              "dark",
    "speed_limit":        "0",
    "search_timeout":     60,
    "agreement_accepted": False,
    "language":           _user_lang if _user_lang in ("it", "en", "es", "de") else "it",
    "max_retries":        3,
    "retry_delay":        2,
    "write_id3":          True,
    "audio_quality":      "320",
    "playlist_format":    "mp3",
    "playlist_subfolder": True,
    "notify_on_complete": True,
    "max_search_results": "10",
    "ytdlp_last_update":  "",
}


def load_settings():
    s = DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if k in s:
                    s[k] = v
            # Forza max_search_results a stringa
            s["max_search_results"] = str(s.get("max_search_results", "10"))
        except Exception as e:
            log(f"ATTENZIONE settings.json: {e}")
    return s


def save_settings():
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(SETTINGS, f, indent=4)
    except Exception as e:
        log(f"ERRORE salvataggio settings: {e}", "error")


SETTINGS = load_settings()


# ==============================================================================
#  RILEVAMENTO OS / FFMPEG
# ==============================================================================

def get_linux_distro():
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.split("=")[1].strip().strip('"').lower()
    except Exception:
        pass
    return "unknown"


def detect_ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        log(f"ffmpeg trovato: {found}")
        return found

    # Cerca anche accanto all'exe (Windows con ffmpeg bundled)
    if getattr(sys, "frozen", False):
        exe_dir = os.path.dirname(sys.executable)
        for candidate in [
            os.path.join(exe_dir, "ffmpeg.exe"),
            os.path.join(exe_dir, "ffmpeg", "win", "ffmpeg.exe"),
            os.path.join(exe_dir, "ffmpeg"),
        ]:
            if os.path.isfile(candidate):
                log(f"ffmpeg trovato (locale): {candidate}")
                return candidate

    log("FFmpeg non trovato nel sistema", "error")
    _show_ffmpeg_error()
    sys.exit(1)


def _show_ffmpeg_error():
    root = ctk.CTk()
    root.title(T("ffmpeg_missing_title"))
    root.geometry("620x380")
    root.resizable(False, False)
    root.eval("tk::PlaceWindow . center")

    frm = ctk.CTkFrame(root)
    frm.pack(fill="both", expand=True, padx=20, pady=20)

    ctk.CTkLabel(frm, text=T("ffmpeg_missing_title"),
                 font=("Segoe UI", 18, "bold")).pack(pady=(15, 8))

    sys_os = platform.system()
    if sys_os == "Windows":
        msg = T("ffmpeg_missing_windows")
    else:
        msg = T("ffmpeg_missing_linux")

    txt = ctk.CTkTextbox(frm, height=200, font=("Consolas", 11), wrap="word")
    txt.pack(fill="x", padx=10, pady=5)
    txt.insert("1.0", msg)
    txt.configure(state="disabled")

    ctk.CTkButton(frm, text=T("ffmpeg_close_app"), command=sys.exit,
                  fg_color="#dc3545", hover_color="#c82333", height=38).pack(pady=12)
    root.mainloop()


FFMPEG_PATH = detect_ffmpeg()



# ==============================================================================
#  ACCORDO LEGALE
# ==============================================================================

def show_agreement():
    root = ctk.CTk()
    root.withdraw()
    accept = messagebox.askyesno(T("agreement_title"), T("agreement_text"))
    root.destroy()
    if accept:
        SETTINGS["agreement_accepted"] = True
        save_settings()
        return True
    messagebox.showinfo(T("agreement_title"), T("agreement_close"))
    return False


# ==============================================================================
#  DEEZER ID3 TAGGER
# ==============================================================================

class DeezerID3Tagger:

    API_BASE = "https://api.deezer.com"

    _COMMON_TERMS = [
        "official", "video", "audio", "lyric", "lyrics", "hq", "hd",
        "4k", "1080p", "720p", "full", "song", "version", "oficial",
        "official video", "official audio", "music video", "mv", "clip",
        "visualizer", "live", "performance", "remix", "mix", "cover",
        "original", "extended", "radio edit",
    ]

    def clean_query(self, q):
        q = os.path.splitext(q)[0]
        q = re.sub(r"[\[\(].*?[\]\)]", "", q)
        pattern = r"\b(" + "|".join(re.escape(t) for t in self._COMMON_TERMS) + r")\b"
        q = re.sub(pattern, "", q, flags=re.IGNORECASE)
        q = re.sub(r"\s+", " ", q).strip()
        q = re.sub(r"[^\w\s\-]", "", q)
        return q or os.path.splitext(os.path.basename(q))[0]

    def search_track(self, query, limit=5):
        try:
            r = requests.get(f"{self.API_BASE}/search",
                             params={"q": self.clean_query(query), "limit": limit},
                             timeout=10)
            r.raise_for_status()
            tracks = []
            for t in r.json().get("data", []):
                tracks.append({
                    "title":        t.get("title", ""),
                    "artist":       t.get("artist", {}).get("name", ""),
                    "album":        t.get("album", {}).get("title", ""),
                    "year":         (t.get("release_date") or "").split("-")[0],
                    "genre":        (t.get("genre") or {}).get("name", ""),
                    "cover_url":    t.get("album", {}).get("cover_medium", ""),
                    "track_number": t.get("track_position", ""),
                    "duration":     t.get("duration", 0),
                })
            return tracks
        except Exception as e:
            log(f"Errore ricerca Deezer: {e}")
            return []

    def calculate_score(self, yt_title, yt_uploader, dz_track,
                        yt_duration=None, position=0):
        score = 0
        yt_tl = yt_title.lower()
        yt_ul = yt_uploader.lower()
        dz_tl = dz_track["title"].lower()
        dz_al = dz_track["artist"].lower()

        # Uploader / artista (20 pt)
        if dz_al in yt_ul or yt_ul in dz_al:
            score += 20
        else:
            aw = set(dz_al.split()); uw = set(yt_ul.split())
            common = aw & uw
            if common:
                sim = len(common) / max(len(aw), len(uw))
                if sim > 0.5:
                    score += int(sim * 20)

        # Titolo (20 pt)
        yt_clean = re.sub(
            r"\b(official|video|audio|lyric|lyrics|hd|hq|4k|mv|clip|music|song|remix|cover)\b",
            "", yt_tl, flags=re.IGNORECASE)
        yt_clean = re.sub(r"[\[\(].*?[\]\)]", "", yt_clean)
        yt_clean = re.sub(r"\s+", " ", yt_clean).strip()
        dz_clean = re.sub(r"[^\w\s]", "", dz_tl)

        if yt_clean == dz_tl or dz_tl in yt_clean or yt_clean in dz_tl:
            score += 20
        else:
            yw = set(yt_clean.split()); dw = set(dz_clean.split())
            common = yw & dw
            if common:
                score += int(len(common) / max(len(yw), len(dw)) * 20)

        # Tipo contenuto (5-30 pt)
        if "official audio" in yt_tl:   score += 30
        elif "official music video" in yt_tl: score += 25
        elif "official video" in yt_tl: score += 20
        elif "audio" in yt_tl:          score += 18
        elif "lyric" in yt_tl:          score += 5
        elif "cover" in yt_tl or "remix" in yt_tl: score += 8
        else:                           score += 10

        # Durata (fino a 40 pt)
        if yt_duration and dz_track.get("duration"):
            diff = abs(int(yt_duration) - int(dz_track["duration"]))
            if diff <= 5:    score += 40
            elif diff <= 15: score += 15
            elif diff <= 30: score += 10
            elif diff <= 60: score += 5

        # Posizione (2-10 pt)
        if position < 5:
            score += [10, 8, 6, 4, 2][position]

        return min(score, 100)

    def find_best_match(self, yt_title, yt_uploader, yt_duration=None,
                         position=0, limit=5):
        tracks = self.search_track(yt_title, limit=limit)
        if not tracks:
            return None
        scored = sorted(
            [{**t, "score": self.calculate_score(yt_title, yt_uploader, t,
                                                  yt_duration, position)}
             for t in tracks],
            key=lambda x: x["score"], reverse=True
        )
        best = scored[0] if scored else None
        if best and best["score"] >= 40:
            log(f"Match Deezer: '{best['title']}' — score {best['score']}/100")
            return best
        return None

    def download_cover(self, url):
        try:
            if not url:
                return None
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.content
        except Exception:
            return None

    def apply_id3_tags(self, filepath, metadata, cover_data=None):
        try:
            audio = MP3(filepath, ID3=ID3)
            try:
                audio.add_tags()
            except ID3Error:
                pass
            if metadata.get("title"):
                audio.tags.add(TIT2(encoding=3, text=metadata["title"]))
            if metadata.get("artist"):
                audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))
            if metadata.get("album"):
                audio.tags.add(TALB(encoding=3, text=metadata["album"]))
            if metadata.get("year"):
                audio.tags.add(TYER(encoding=3, text=metadata["year"]))
            if metadata.get("genre"):
                audio.tags.add(TCON(encoding=3, text=metadata["genre"]))
            if cover_data:
                audio.tags.add(APIC(encoding=3, mime="image/jpeg",
                                    type=3, desc="Cover", data=cover_data))
            audio.save()
            log(f"Tag ID3 applicati: {filepath}")
            return True
        except Exception as e:
            log(f"Errore ID3: {e}", "error")
            return False


# ==============================================================================
#  UTILITY
# ==============================================================================

def is_playlist(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    return "playlist" in parsed.path or "list" in params


def extract_video_id(url):
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "v" in params:
        return params["v"][0]
    m = re.search(r"(youtu\.be/|v=)([a-zA-Z0-9_-]{11})", url)
    return m.group(2) if m else None


def fmt_duration(sec):
    if not isinstance(sec, (int, float)):
        return str(sec) if sec else "?"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"


def fmt_views(n):
    if not n:
        return "—"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.0f}K"
    return str(n)


def open_folder(path):
    try:
        sys_os = platform.system()
        if sys_os == "Windows":
            os.startfile(path)
        elif sys_os == "Darwin":
            subprocess.call(["open", path])
        else:
            subprocess.call(["xdg-open", path])
    except Exception as e:
        log(f"Impossibile aprire cartella: {e}")


def open_file(path):
    try:
        sys_os = platform.system()
        if sys_os == "Windows":
            os.startfile(path)
        elif sys_os == "Darwin":
            subprocess.call(["open", path])
        else:
            try:
                subprocess.call(["xdg-open", path])
            except Exception:
                subprocess.call(["gio", "open", path])
    except Exception as e:
        log(f"Impossibile aprire file: {e}")


def notify_desktop(title, message):
    try:
        sys_os = platform.system()
        if sys_os == "Darwin":
            subprocess.run(
                ["osascript", "-e",
                 f'display notification "{message}" with title "{title}"'],
                check=False
            )
        elif sys_os == "Linux":
            subprocess.run(["notify-send", title, message], check=False)
    except Exception:
        pass


def log_playlist_url(url):
    """Scrive l'URL in playlist_urls.log (senza duplicati)."""
    try:
        existing = set()
        if os.path.exists(PLAYLIST_LOG_FILE):
            with open(PLAYLIST_LOG_FILE, "r", encoding="utf-8") as f:
                existing = {line.strip() for line in f if line.strip()}
        if url not in existing:
            with open(PLAYLIST_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(url + "\n")
    except Exception as e:
        log(f"Impossibile scrivere playlist_urls.log: {e}")


def _set_win_icon(win):
    try:
        sys_os = platform.system()
        if sys_os == "Windows" and os.path.exists("Logo.ico"):
            win.iconbitmap("Logo.ico")
        elif os.path.exists("Logo.png"):
            win.iconphoto(True, PhotoImage(file="Logo.png"))
    except Exception:
        pass


# ==============================================================================
#  RICERCA YOUTUBE
# ==============================================================================

def _yt_search_worker(query, max_results, result_queue, deezer_tagger):
    log(f"Ricerca: '{query}', max={max_results}")
    max_retries = SETTINGS.get("max_retries", 3)
    retry_delay = SETTINGS.get("retry_delay", 2)

    for attempt in range(max_retries):
        try:
            is_url = query.startswith("http")
            opts = {
                "quiet":           True,
                "extract_flat":    True,
                "skip_download":   True,
                "default_search":  "auto" if is_url else "ytsearch",
                "socket_timeout":  30,
                "extractor_retries": 3,
            }
            search_query = f"ytsearch{max_results}:{query}" if not is_url else query

            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search_query, download=False)

            if not is_url:
                results = []
                for pos, e in enumerate(info.get("entries", []) or []):
                    if not e or not e.get("id"):
                        continue
                    yt_title    = e.get("title", "Sconosciuto")
                    yt_uploader = e.get("uploader", "Sconosciuto")
                    yt_dur      = e.get("duration")
                    dz_match    = None
                    if deezer_tagger:
                        dz_match = deezer_tagger.find_best_match(
                            yt_title, yt_uploader, yt_dur, pos, limit=3)
                    results.append({
                        "title":        yt_title,
                        "url":          f"https://www.youtube.com/watch?v={e['id']}",
                        "duration":     yt_dur,
                        "uploader":     yt_uploader,
                        "deezer_match": dz_match,
                        "view_count":   e.get("view_count", 0),
                    })
                log(f"Trovati {len(results)} risultati.")
                result_queue.put(("ok", results))
                return

            elif info and info.get("id"):
                yt_title    = info.get("title", "Sconosciuto")
                yt_uploader = info.get("uploader", "Sconosciuto")
                yt_dur      = info.get("duration")
                dz_match    = None
                if deezer_tagger:
                    dz_match = deezer_tagger.find_best_match(
                        yt_title, yt_uploader, yt_dur, 0, 3)
                result_queue.put(("ok", [{
                    "title":        yt_title,
                    "url":          info.get("webpage_url", query),
                    "duration":     yt_dur,
                    "uploader":     yt_uploader,
                    "deezer_match": dz_match,
                    "view_count":   info.get("view_count", 0),
                }]))
                return
            else:
                result_queue.put(("ok", []))
                return

        except Exception as ex:
            log(f"Tentativo {attempt + 1}/{max_retries} fallito: {ex}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                result_queue.put(("err", str(ex)))


def search_youtube(query, max_results=10, timeout_seconds=60, deezer_tagger=None):
    rq = queue.Queue()
    video_id = extract_video_id(query)
    if video_id and query.startswith("http"):
        query = f"https://www.youtube.com/watch?v={video_id}"

    t = threading.Thread(
        target=_yt_search_worker,
        args=(query, max_results, rq, deezer_tagger),
        daemon=True
    )
    t.start()
    try:
        typ, payload = rq.get(timeout=timeout_seconds)
        if typ == "ok":
            return payload
        raise RuntimeError(payload)
    except queue.Empty:
        raise TimeoutError("Ricerca scaduta")


# ==============================================================================
#  DOWNLOAD SINGOLO
# ==============================================================================

LAST_FILE = None


def download_with_yt_dlp(url, fmt, out_dir, speed_limit, progress_cb=None, noplaylist=True):
    global LAST_FILE
    max_retries = SETTINGS.get("max_retries", 3)
    retry_delay = SETTINGS.get("retry_delay", 2)
    outtmpl     = os.path.join(out_dir, "%(title)s.%(ext)s")

    def hook(d):
        if d["status"] == "downloading":
            total = d.get("total_bytes_estimate") or d.get("total_bytes")
            if total and total > 0:
                pct = d.get("downloaded_bytes", 0) / total * 100
                if progress_cb:
                    progress_cb(pct)
        elif d["status"] == "finished":
            if progress_cb:
                progress_cb(100)

    for attempt in range(max_retries):
        try:
            postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": fmt}]
            if fmt == "mp3" and SETTINGS.get("audio_quality"):
                postprocessors[0]["preferredquality"] = str(SETTINGS["audio_quality"])

            ydl_opts = {
                "outtmpl":           outtmpl,
                "format":            "bestaudio/best",
                "quiet":             True,
                "noplaylist":        noplaylist,
                "postprocessors":    postprocessors,
                "progress_hooks":    [hook],
                "socket_timeout":    30,
                "extractor_retries": 3,
            }
            if speed_limit and str(speed_limit) != "0":
                ydl_opts["ratelimit"] = speed_limit

            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    LAST_FILE = ydl.prepare_filename(info).rsplit(".", 1)[0] + f".{fmt}"

            log(f"Download completato: {LAST_FILE}")
            return True

        except Exception as e:
            log(f"Tentativo {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                raise


# ==============================================================================
#  GUI PRINCIPALE
# ==============================================================================

class YTDownloaderApp(ctk.CTk):

    def __init__(self):
        super().__init__()
        self.title("MUSIC WAVVER 5.0")
        self.geometry("1000x660")
        self.minsize(800, 540)
        self.configure(fg_color=C_BG)

        self._set_icon()
        self._set_logo()

        self.queue         = queue.Queue()
        self.results       = []
        self.downloading   = False
        self.query         = ctk.StringVar()
        self.format        = ctk.StringVar(value="mp3")
        self.status        = ctk.StringVar(value=T("ready"))
        self.search_max    = ctk.StringVar(value=SETTINGS.get("max_search_results", "10"))
        self.deezer_tagger = DeezerID3Tagger()
        self.session_count = 0

        log("MUSIC WAVVER 5.0 avviato")

        self._build_ui()
        self.after(150, self._loop)


    # ──────────────────────────────────────────────────────────────────────────
    #  ICONA / LOGO
    # ──────────────────────────────────────────────────────────────────────────

    def _set_icon(self):
        try:
            sys_os = platform.system()
            if sys_os == "Windows" and os.path.exists("Logo.ico"):
                self.iconbitmap("Logo.ico")
            elif os.path.exists("Logo.png"):
                self.iconphoto(True, PhotoImage(file="Logo.png"))
        except Exception:
            pass

    def _set_logo(self):
        self.logo_image = None
        for fname in ("Logo.png", "logo.png"):
            if os.path.exists(fname):
                try:
                    self.logo_image = ctk.CTkImage(
                        light_image=Image.open(fname),
                        dark_image=Image.open(fname),
                        size=(36, 36))
                    break
                except Exception:
                    pass

    # ──────────────────────────────────────────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self)
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        hdr.grid_columnconfigure(1, weight=1)

        title_row = ctk.CTkFrame(hdr, fg_color="transparent")
        title_row.grid(row=0, column=0, sticky="w", padx=10, pady=8)

        if self.logo_image:
            ctk.CTkLabel(title_row, image=self.logo_image, text="").pack(
                side="left", padx=(0, 10))

        ctk.CTkLabel(
            title_row,
            text=T("welcome"),
            font=("Segoe UI", 17, "bold")
        ).pack(side="left")

        btn_row = ctk.CTkFrame(hdr, fg_color="transparent")
        btn_row.grid(row=0, column=2, sticky="e", padx=10)

        ctk.CTkButton(
            btn_row, text="Log Playlist",
            command=self._open_playlist_log, width=130,
            fg_color="#1e2a4a", hover_color="#2a3a5a"
        ).pack(side="right", padx=3)
        ctk.CTkButton(
            btn_row, text="# Log",
            command=self.open_log, width=80,
            fg_color="#1e2a4a", hover_color="#2a3a5a"
        ).pack(side="right", padx=3)
        ctk.CTkButton(
            btn_row, text="= Impostazioni",
            command=self.open_settings, width=140,
            fg_color=C_ACCENT, hover_color="#9B7FD4"
        ).pack(side="right", padx=3)

        # ── Barra ricerca ─────────────────────────────────────────────────────
        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))
        search_frame.grid_columnconfigure(0, weight=1)

        entry_row = ctk.CTkFrame(search_frame, fg_color="transparent")
        entry_row.grid(row=0, column=0, sticky="ew", padx=10, pady=8)
        entry_row.grid_columnconfigure(0, weight=1)

        self.entry = ctk.CTkEntry(
            entry_row,
            textvariable=self.query,
            placeholder_text="Cerca su YouTube / incolla URL video o playlist / SoundCloud ...",
            height=42,
            font=("Segoe UI", 13),
            fg_color=C_CARD,
            border_color=C_BORDER,
            border_width=1,
            text_color=C_TEXT,
            corner_radius=10,
        )
        self.entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self.entry.bind("<Return>", lambda e: self.on_search())

        self.btn_clear = ctk.CTkButton(
            entry_row, text="X", width=38, height=38,
            fg_color="gray35", hover_color="gray25",
            command=self._clear_search
        )
        self.btn_clear.grid(row=0, column=1, padx=2)

        self.btn_search = ctk.CTkButton(
            search_frame,
            text="Q Cerca",
            command=self.on_search,
            width=130, height=42,
            font=("Segoe UI", 12, "bold"),
            fg_color=C_ACCENT, hover_color="#9B7FD4",
            corner_radius=10
        )
        self.btn_search.grid(row=0, column=1, padx=(0, 8))

        # Max risultati
        max_row = ctk.CTkFrame(search_frame, fg_color="transparent")
        max_row.grid(row=0, column=2, padx=(0, 10))
        ctk.CTkLabel(max_row, text="Max:").pack(side="left")
        ctk.CTkOptionMenu(
            max_row,
            variable=self.search_max,
            values=["5", "10", "15", "20"],
            width=68
        ).pack(side="left", padx=4)

        # ── Treeview risultati ────────────────────────────────────────────────
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 6))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self._configure_tree_style()

        cols = ("Titolo", "Uploader", "Durata", "Visualizzazioni", "Score", "Stato")
        self.tree = Treeview(tree_frame, columns=cols, show="headings", height=14)

        self.tree.tag_configure("best_match",      background="#1a3a1a", foreground="#81C784")
        self.tree.tag_configure("good_match",      background="#2a2a00", foreground="#FFD54F")
        self.tree.tag_configure("no_match",        background=C_BG,      foreground=C_MUTED)
        self.tree.tag_configure("downloading_tag", background=C_CARD,    foreground="white")

        self.tree.column("Titolo",          width=330, anchor="w",      minwidth=200)
        self.tree.column("Uploader",        width=130, anchor="w",      minwidth=80)
        self.tree.column("Durata",          width=68,  anchor="center")
        self.tree.column("Visualizzazioni", width=95,  anchor="center")
        self.tree.column("Score",           width=62,  anchor="center")
        self.tree.column("Stato",           width=70,  anchor="center")

        for c in cols:
            self.tree.heading(c, text=c)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        vsb.grid(row=0, column=1, sticky="ns", pady=5, padx=(0, 5))

        self.tree.bind("<Double-1>", lambda e: self.on_download())
        self.tree.bind("<Button-3>", self._context_menu)

        # ── Controlli download ────────────────────────────────────────────────
        ctrl = ctk.CTkFrame(self)
        ctrl.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 6))

        ctk.CTkLabel(ctrl, text=T("format_label")).pack(side="left", padx=(10, 4))
        ctk.CTkOptionMenu(
            ctrl, variable=self.format,
            values=["mp3", "wav", "flac", "m4a", "opus"]
        ).pack(side="left", padx=4)

        self.btn_download = ctk.CTkButton(
            ctrl, text="v  Scarica",
            command=self.on_download,
            fg_color=C_GREEN, hover_color="#2E7D32",
            width=140, height=38, font=("Segoe UI", 12, "bold"),
            corner_radius=10
        )
        self.btn_download.pack(side="left", padx=12)

        self.btn_play = ctk.CTkButton(
            ctrl, text="> Riproduci",
            command=self.play_file,
            state="disabled", width=120, height=38,
            fg_color=C_BLUE, hover_color="#1565C0",
            corner_radius=10
        )
        self.btn_play.pack(side="left", padx=4)

        # Destra: cartella + contatore
        ctk.CTkButton(
            ctrl, text="[ ] Apri Cartella",
            command=lambda: open_folder(SETTINGS["download_dir"]),
            width=140, height=38,
            fg_color=C_CARD, hover_color="#1a4090",
            corner_radius=10
        ).pack(side="right", padx=(4, 10))

        self.session_label = ctk.CTkLabel(ctrl, text="Sessione: 0")
        self.session_label.pack(side="right", padx=8)

        # ── Barra progresso ───────────────────────────────────────────────────
        prog_frame = ctk.CTkFrame(self)
        prog_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 12))
        prog_frame.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(prog_frame, height=8,
                                               progress_color=C_ACCENT,
                                               fg_color="#222233",
                                               corner_radius=4)
        self.progress.set(0)
        self.progress.grid(row=0, column=0, sticky="ew", padx=10, pady=10)

        ctk.CTkLabel(
            prog_frame, textvariable=self.status, font=("Segoe UI", 12)
        ).grid(row=0, column=1, padx=(4, 10))

    # ──────────────────────────────────────────────────────────────────────────
    #  STILE TREEVIEW
    # ──────────────────────────────────────────────────────────────────────────

    def _configure_tree_style(self):
        s = Style()
        s.theme_use("clam")
        s.configure("Treeview",
                    background=C_BG, foreground=C_TEXT,
                    fieldbackground=C_BG, borderwidth=0,
                    rowheight=26,
                    font=("Segoe UI", 11))
        s.configure("Treeview.Heading",
                    background=C_CARD, foreground=C_MUTED,
                    relief="flat", font=("Segoe UI", 10, "bold"))
        s.map("Treeview.Heading", background=[("active", "#1e4080")])
        s.map("Treeview",
              background=[("selected", C_ACCENT)],
              foreground=[("selected", "white")])
        s.configure("Vertical.TScrollbar",
                    background=C_PANEL, troughcolor=C_BG, arrowcolor=C_MUTED)

    # ──────────────────────────────────────────────────────────────────────────
    #  AZIONI UI
    # ──────────────────────────────────────────────────────────────────────────

    def _clear_search(self):
        self.query.set("")
        self.entry.focus()

    def lock_ui(self, state):
        s = "disabled" if state else "normal"
        for w in [self.btn_search, self.btn_download, self.entry, self.btn_clear]:
            w.configure(state=s)

    def _context_menu(self, event):
        sel = self.tree.identify_row(event.y)
        if not sel:
            return
        self.tree.selection_set(sel)
        idx = self.tree.index(sel)
        if idx >= len(self.results):
            return
        url = self.results[idx]["url"]

        menu = Menu(self, tearoff=0)
        menu.add_command(label="Scarica",         command=self.on_download)
        menu.add_command(label="Copia URL",       command=lambda: self._copy(url))
        menu.add_command(label="Apri in browser", command=lambda: self._open_browser(url))
        menu.add_separator()
        menu.add_command(label="Riproduci ultimo file",
                         command=self.play_file,
                         state="normal" if LAST_FILE else "disabled")
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _copy(self, text):
        self.clipboard_clear()
        self.clipboard_append(text)

    def _open_browser(self, url):
        import webbrowser
        webbrowser.open(url)

    # ──────────────────────────────────────────────────────────────────────────
    #  RICERCA
    # ──────────────────────────────────────────────────────────────────────────

    def on_search(self):
        q = self.query.get().strip()
        if not q:
            return

        if q.startswith("http") and is_playlist(q):
            self._handle_playlist_prompt(q)
            return

        self.lock_ui(True)
        self.btn_play.configure(state="disabled")
        self.status.set(T("searching"))
        self.progress.set(0)
        threading.Thread(
            target=self._search_thread,
            args=(q, int(self.search_max.get())),
            daemon=True
        ).start()

    def _search_thread(self, q, maxr):
        try:
            results = search_youtube(
                q,
                max_results=maxr,
                timeout_seconds=int(SETTINGS.get("search_timeout", 60)),
                deezer_tagger=self.deezer_tagger,
            )
            self.results = results

            # Trova miglior match
            best_idx, best_score = -1, -1
            for i, r in enumerate(results):
                sc = (r.get("deezer_match") or {}).get("score", 0)
                if sc > best_score:
                    best_score, best_idx = sc, i

            self.tree.delete(*self.tree.get_children())

            for i, r in enumerate(results):
                dz    = r.get("deezer_match")
                score = dz.get("score", 0) if dz else 0

                score_str = f"{score}/100" if dz else "N/A"
                dur_str   = fmt_duration(r.get("duration"))
                views_str = fmt_views(r.get("view_count", 0))

                if dz:
                    yt_dur = r.get("duration")
                    dz_dur = dz.get("duration")
                    dur_ok = yt_dur and dz_dur and abs(int(yt_dur) - int(dz_dur)) <= 10
                    if score >= 40:
                        status = "OK+" if dur_ok else "OK"
                    else:
                        status = "?" + ("+" if dur_ok else "")
                else:
                    status = "—"

                if i == best_idx and best_score >= 40:
                    tag = "best_match"
                elif dz and score >= 30:
                    tag = "good_match"
                else:
                    tag = "no_match"

                self.tree.insert("", "end",
                                  values=(r["title"], r["uploader"], dur_str,
                                          views_str, score_str, status),
                                  tags=(tag,))

            count = len(results)
            self.status.set(
                f"{count} risultati — miglior match: {best_score}/100"
                if best_score > 0 else f"{count} risultati"
            )

            # Auto-seleziona miglior match
            children = self.tree.get_children()
            if best_idx >= 0 and best_idx < len(children):
                self.tree.selection_set(children[best_idx])
                self.tree.focus(children[best_idx])
                self.tree.see(children[best_idx])

        except TimeoutError:
            self.status.set("Ricerca scaduta")
            messagebox.showwarning("Timeout",
                                   "La ricerca ha impiegato troppo tempo. Riprova.")
        except Exception as e:
            self.status.set("Errore ricerca")
            messagebox.showerror("Errore", str(e))
        finally:
            self.lock_ui(False)

    # ──────────────────────────────────────────────────────────────────────────
    #  PLAYLIST PROMPT
    # ──────────────────────────────────────────────────────────────────────────

    def _handle_playlist_prompt(self, url):
        if not PLAYLIST_MODULE_AVAILABLE:
            messagebox.showerror(
                "Modulo Playlist Non Trovato",
                PLAYLIST_MODULE_ERROR,
                parent=self
            )
            return

        video_id = extract_video_id(url)

        if not video_id:
            # URL pura di playlist: apri direttamente
            log_playlist_url(url)
            try:
                open_playlist_downloader(self, url)
            except Exception as e:
                messagebox.showerror("Errore",
                                     f"Impossibile aprire il downloader playlist:\n{e}",
                                     parent=self)
            return

        # URL con sia video che playlist: chiedi cosa fare
        win = ctk.CTkToplevel(self)
        win.title(T("playlist_prompt_title"))
        win.geometry("440x180")
        win.transient(self)
        win.grab_set()
        win.resizable(False, False)
        _set_win_icon(win)

        ctk.CTkLabel(
            win, text=T("playlist_prompt_text"),
            font=("Segoe UI", 13), wraplength=410
        ).pack(pady=20)

        btn_f = ctk.CTkFrame(win, fg_color="transparent")
        btn_f.pack()

        def do_single():
            win.destroy()
            self.query.set(f"https://www.youtube.com/watch?v={video_id}")
            self.on_search()

        def do_playlist():
            win.destroy()
            log_playlist_url(url)
            try:
                open_playlist_downloader(self, url)
            except Exception as e:
                messagebox.showerror("Errore",
                                     f"Impossibile aprire il downloader playlist:\n{e}",
                                     parent=self)

        ctk.CTkButton(btn_f, text=T("playlist_prompt_single"),
                      command=do_single, width=180).pack(side="left", padx=12)
        ctk.CTkButton(btn_f, text=T("playlist_prompt_full"),
                      command=do_playlist, width=190,
                      fg_color="#28a745", hover_color="#218838").pack(side="left", padx=12)

    # ──────────────────────────────────────────────────────────────────────────
    #  DOWNLOAD
    # ──────────────────────────────────────────────────────────────────────────

    def on_download(self):
        if self.downloading:
            return
        sel = self.tree.focus()
        if not sel:
            messagebox.showinfo("Info", "Seleziona un risultato dalla lista.")
            return

        index = self.tree.index(sel)
        if index >= len(self.results):
            return

        title = self.tree.item(sel)["values"][0]
        url   = self.results[index]["url"]

        self.downloading = True
        self.lock_ui(True)
        self.status.set(f"Download: {str(title)[:50]}...")
        self.progress.set(0)

        try:
            self.tree.item(sel, tags=("downloading_tag",))
        except Exception:
            pass

        threading.Thread(
            target=self._download_thread,
            args=(url, self.format.get(), sel, index),
            daemon=True
        ).start()

    def _download_thread(self, url, fmt, tree_item_id, result_index):
        try:
            def update_progress(p):
                self.queue.put(("progress", p))

            download_with_yt_dlp(
                url, fmt,
                SETTINGS["download_dir"],
                SETTINGS.get("speed_limit", "0"),
                progress_cb=update_progress,
            )

            global LAST_FILE
            if (fmt == "mp3" and SETTINGS.get("write_id3", True)
                    and LAST_FILE and os.path.exists(LAST_FILE)):
                result = self.results[result_index]
                dz = result.get("deezer_match")
                if dz:
                    cover = self.deezer_tagger.download_cover(dz.get("cover_url", ""))
                    meta  = {k: dz.get(k, "") for k in
                             ("title", "artist", "album", "year", "genre")}
                    meta["track_number"] = str(dz.get("track_number", ""))
                    ok = self.deezer_tagger.apply_id3_tags(LAST_FILE, meta, cover)
                    if ok:
                        self.queue.put(("id3_done", (tree_item_id, dz.get("score", 0))))
                        return
                # Fallback: cerca per nome file
                fname  = os.path.basename(LAST_FILE)
                tracks = self.deezer_tagger.search_track(fname, limit=1)
                if tracks:
                    trk   = tracks[0]
                    cover = self.deezer_tagger.download_cover(trk.get("cover_url", ""))
                    meta  = {k: trk.get(k, "") for k in
                             ("title", "artist", "album", "year", "genre")}
                    meta["track_number"] = str(trk.get("track_number", ""))
                    self.deezer_tagger.apply_id3_tags(LAST_FILE, meta, cover)

            self.queue.put(("done", tree_item_id))

        except Exception as e:
            self.queue.put(("error", str(e)))

    # ──────────────────────────────────────────────────────────────────────────
    #  PLAY
    # ──────────────────────────────────────────────────────────────────────────

    def play_file(self):
        global LAST_FILE
        if LAST_FILE and os.path.exists(LAST_FILE):
            open_file(LAST_FILE)
        else:
            messagebox.showinfo("Info", "Nessun file da riprodurre. Scarica prima un brano.")

    # ──────────────────────────────────────────────────────────────────────────
    #  LOG
    # ──────────────────────────────────────────────────────────────────────────

    def open_log(self):
        self._open_text_file(LOG_FILE, "Log del Programma")

    def _open_playlist_log(self):
        self._open_text_file(PLAYLIST_LOG_FILE, T("open_playlist_log"))

    def _open_text_file(self, filepath, title):
        if not os.path.exists(filepath):
            messagebox.showinfo(title, f"Nessun file trovato:\n{filepath}")
            return

        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("860x560")
        _set_win_icon(win)

        txt = ctk.CTkTextbox(win, font=("Consolas", 11), wrap="word")
        txt.pack(fill="both", expand=True, padx=10, pady=(10, 4))

        content = ""
        for enc in ("utf-8", "latin-1", "cp1252"):
            try:
                with open(filepath, "r", encoding=enc) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue

        txt.insert("1.0", content or "(File vuoto o illeggibile)")
        txt.configure(state="disabled")

        bar = ctk.CTkFrame(win, fg_color="transparent")
        bar.pack(pady=(0, 10))

        ctk.CTkButton(bar, text="Pulisci",
                      command=lambda: self._clear_text_file(filepath, txt),
                      width=100).pack(side="left", padx=6)
        ctk.CTkButton(bar, text="Apri File",
                      command=lambda: open_file(filepath),
                      width=100).pack(side="left", padx=6)

    def _clear_text_file(self, filepath, txt_widget):
        try:
            open(filepath, "w", encoding="utf-8").close()
            txt_widget.configure(state="normal")
            txt_widget.delete("1.0", "end")
            txt_widget.configure(state="disabled")
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    #  IMPOSTAZIONI
    # ──────────────────────────────────────────────────────────────────────────

    def open_settings(self):
        win = ctk.CTkToplevel(self)
        win.title(T("settings_title"))
        win.geometry("540x620")
        win.transient(self)
        win.grab_set()
        _set_win_icon(win)

        sf = ctk.CTkScrollableFrame(win)
        sf.pack(fill="both", expand=True, padx=10, pady=10)
        sf.grid_columnconfigure(0, weight=1)
        row = 0

        def sec(text):
            nonlocal row
            ctk.CTkLabel(sf, text=text, font=("Segoe UI", 13, "bold")).grid(
                row=row, column=0, sticky="w", pady=(14, 3), padx=10)
            row += 1

        def add(widget):
            nonlocal row
            widget.grid(row=row, column=0, sticky="ew", padx=10, pady=3)
            row += 1

        # Cartella download
        sec(T("download_folder_label"))
        dir_f = ctk.CTkFrame(sf)
        dir_f.grid(row=row, column=0, sticky="ew", padx=10, pady=3)
        dir_f.grid_columnconfigure(0, weight=1)
        row += 1
        self.dir_label = ctk.CTkLabel(dir_f, text=SETTINGS["download_dir"], anchor="w")
        self.dir_label.grid(row=0, column=0, sticky="ew", padx=8)
        ctk.CTkButton(dir_f, text=T("change_folder"),
                      command=lambda: self.change_dir(win), width=80
                      ).grid(row=0, column=1, padx=8)

        # Qualita' MP3
        sec("Qualita' Audio MP3")
        self.quality_var = ctk.StringVar(value=str(SETTINGS.get("audio_quality", "320")))
        add(ctk.CTkComboBox(sf, variable=self.quality_var,
                             values=["128", "192", "256", "320"], state="readonly"))

        # Formato playlist
        sec("Formato Download Playlist")
        self.pl_fmt_var = ctk.StringVar(value=SETTINGS.get("playlist_format", "mp3"))
        add(ctk.CTkComboBox(sf, variable=self.pl_fmt_var,
                             values=["mp3", "wav", "flac", "m4a"], state="readonly"))

        # ID3
        sec("ID3 Tag (Metadati automatici da Deezer)")
        self.id3_var = ctk.BooleanVar(value=SETTINGS.get("write_id3", True))
        add(ctk.CTkCheckBox(sf, text=T("id3_enable_label"), variable=self.id3_var))

        # Sottocartella playlist
        self.pl_sub_var = ctk.BooleanVar(value=SETTINGS.get("playlist_subfolder", True))
        add(ctk.CTkCheckBox(sf, text="Crea sottocartella per ogni playlist",
                             variable=self.pl_sub_var))

        # Notifiche
        self.notify_var = ctk.BooleanVar(value=SETTINGS.get("notify_on_complete", True))
        add(ctk.CTkCheckBox(sf, text="Notifica desktop al completamento download",
                             variable=self.notify_var))

        # Lingua
        sec(T("language_label"))
        self.lang_var = ctk.StringVar(value=SETTINGS.get("language", "it"))
        add(ctk.CTkComboBox(sf, variable=self.lang_var,
                             values=["it", "en", "es", "de"], state="readonly"))

        # Tema
        sec(T("theme_label"))
        self.theme_var = ctk.StringVar(value=SETTINGS.get("theme", "system"))
        add(ctk.CTkComboBox(sf, variable=self.theme_var,
                             values=["system", "dark", "light"], state="readonly"))

        # Limite velocita'
        sec(T("speed_limit_label"))
        self.speed_var = ctk.StringVar(value=SETTINGS.get("speed_limit", "0"))
        add(ctk.CTkEntry(sf, textvariable=self.speed_var,
                          placeholder_text="es: 500K  2M  0=illimitato"))

        # Timeout ricerca
        sec(T("search_timeout_label"))
        self.timeout_var = ctk.StringVar(value=str(SETTINGS.get("search_timeout", 60)))
        add(ctk.CTkEntry(sf, textvariable=self.timeout_var))

        # Max risultati ricerca
        sec("Numero massimo risultati ricerca")
        self.maxres_var = ctk.StringVar(value=str(SETTINGS.get("max_search_results", "10")))
        add(ctk.CTkComboBox(sf, variable=self.maxres_var,
                             values=["5", "10", "15", "20"], state="readonly"))


        # Salva
        ctk.CTkButton(
            sf, text="OK  Salva Impostazioni",
            command=lambda: self._save_settings(win),
            fg_color=C_GREEN, hover_color="#2E7D32", height=46,
            corner_radius=10, font=("Segoe UI", 13, "bold")
        ).grid(row=row, column=0, sticky="ew", padx=10, pady=20)

    def change_dir(self, parent_win):
        d = filedialog.askdirectory(
            initialdir=SETTINGS["download_dir"],
            title=T("select_download_folder")
        )
        if d:
            SETTINGS["download_dir"] = d
            self.dir_label.configure(text=d)
            save_settings()

    def _save_settings(self, win):
        SETTINGS["language"]           = self.lang_var.get()
        SETTINGS["theme"]              = self.theme_var.get()
        SETTINGS["write_id3"]          = self.id3_var.get()
        SETTINGS["audio_quality"]      = self.quality_var.get()
        SETTINGS["playlist_format"]    = self.pl_fmt_var.get()
        SETTINGS["playlist_subfolder"] = self.pl_sub_var.get()
        SETTINGS["notify_on_complete"] = self.notify_var.get()
        SETTINGS["speed_limit"]        = self.speed_var.get().strip() or "0"
        SETTINGS["max_search_results"] = self.maxres_var.get()

        raw_timeout = self.timeout_var.get().strip()
        SETTINGS["search_timeout"] = int(raw_timeout) if raw_timeout.isdigit() else 60

        save_settings()
        ctk.set_appearance_mode(SETTINGS["theme"])
        messagebox.showinfo("Impostazioni", "Impostazioni salvate!", parent=win)
        win.destroy()

    # ──────────────────────────────────────────────────────────────────────────
    #  EVENT LOOP QUEUE
    # ──────────────────────────────────────────────────────────────────────────

    def _loop(self):
        try:
            while True:
                typ, payload = self.queue.get_nowait()

                if typ in ("done", "id3_done", "id3_failed"):
                    self.downloading = False
                    self.lock_ui(False)
                    self.btn_play.configure(state="normal")
                    self.progress.set(1.0)
                    self.status.set(T("complete"))
                    self.session_count += 1
                    self.session_label.configure(text=f"Sessione: {self.session_count}")

                    if typ == "id3_done":
                        _, score = payload
                        msg = T("complete_msg")
                        if score > 0:
                            msg += f"\nTag ID3 applicati (score {score}/100)"
                        messagebox.showinfo("Download Completato", msg)
                    else:
                        messagebox.showinfo("Download Completato", T("complete_msg"))

                    if SETTINGS.get("notify_on_complete", True):
                        notify_desktop("Music Wavver", T("complete_msg"))

                    self.after(8000, self._soft_reset)

                elif typ == "error":
                    self.downloading = False
                    self.lock_ui(False)
                    self.progress.set(0)
                    self.status.set("Errore download")
                    messagebox.showerror("Errore Download", payload)

                elif typ == "progress":
                    self.progress.set(payload / 100)
                    self.status.set(f"Download: {payload:.0f}%")

        except queue.Empty:
            pass

        self.after(150, self._loop)

    def _soft_reset(self):
        """Reset parziale dopo completamento."""
        self.status.set(T("ready"))
        self.progress.set(0)
        self.lock_ui(False)


# ==============================================================================
#  MAIN
# ==============================================================================

def main():
    log("Avvio MUSIC WAVVER 5.0...")
    log("Controllo FFmpeg...")
    detect_ffmpeg()

    if not SETTINGS.get("agreement_accepted", False):
        if not show_agreement():
            log("Accordo rifiutato — chiusura.")
            sys.exit(0)

    app = YTDownloaderApp()
    app.mainloop()


if __name__ == "__main__":
    main()
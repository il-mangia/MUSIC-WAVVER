#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════╗
║   MUSIC WAVVER 6  —  PyQt6 Edition  ║
║   github.com/il-mangia              ║
╚══════════════════════════════════════╝
"""

import sys
import os
import re
import json
import locale
import requests
import subprocess
import shutil
import spotipy
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTableWidget, QTableWidgetItem, QLabel,
    QComboBox, QProgressBar, QDialog, QTextEdit, QHeaderView,
    QMessageBox, QFrame, QSizePolicy, QFileDialog, QScrollBar,
    QAbstractItemView
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QColor, QPalette, QCursor, QFontDatabase, QPixmap, QIcon

import concurrent.futures
import deezertrack
import spotifytrack

try:
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, APIC
    from mutagen.mp3 import MP3
    MUTAGEN_OK = True
except ImportError:
    MUTAGEN_OK = False


# ──────────────────────────────────────────────────────────────────
#  LANGUAGE SYSTEM
# ──────────────────────────────────────────────────────────────────

_LANG: dict = {}


def _base_dir() -> str:
    """Directory del file .py o del .exe compilato."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _load_languages() -> bool:
    """
    Carica languages.json dalla stessa cartella dell'applicazione.
    Rileva la lingua di sistema e seleziona il blocco corretto.
    Restituisce True se il caricamento va a buon fine.
    """
    global _LANG
    lang_file = os.path.join(_base_dir(), "languages.json")
    if not os.path.exists(lang_file):
        return False
    try:
        with open(lang_file, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        
        # Modern replacement for locale.getdefaultlocale()
        sys_locale = "en"
        try:
            # Dopo aver chiamato setlocale(LC_ALL, ""), getlocale() ritorna la lingua di sistema
            loc = locale.getlocale()[0]
            if loc:
                sys_locale = loc
        except Exception:
            pass
            
        code = sys_locale[:2].lower()
        if code not in data:
            code = "en" if "en" in data else list(data.keys())[0]
        _LANG = data[code]
        return True
    except Exception:
        return False


def T(key: str, **kwargs) -> str:
    """Restituisce la stringa tradotta per la chiave data."""
    val = _LANG.get(key, key)
    if kwargs:
        try:
            val = val.format(**kwargs)
        except Exception:
            pass
    return val


# ──────────────────────────────────────────────────────────────────
#  FILE LOG  (wavver.log)
# ──────────────────────────────────────────────────────────────────

_LOG_PATH = os.path.join(_base_dir(), "wavver.log")


def _write_log(msg: str) -> None:
    """Scrive una riga nel file wavver.log con timestamp ISO."""
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Rimuovi tag HTML eventualmente presenti
    clean = re.sub(r"<[^>]+>", "", msg)
    try:
        with open(_LOG_PATH, "a", encoding="utf-8") as fh:
            fh.write(f"[{ts}] {clean}\n")
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────
#  URL DETECTION
# ──────────────────────────────────────────────────────────────────

def _detect_link(query: str):
    """
    Analizza la stringa di ricerca.
    Ritorna:
      ('spotify.com', type, id)  — link Spotify (type: track, album, playlist)
      ('deezer.com',  track_id)  — link Deezer
      ('search',  query)     — testo libero
    """
    q = query.strip()
    # Spotify: track, album, playlist
    sp = re.match(
        r"https?://open\.spotify\.com/(?:[\w-]+/)?(track|album|playlist)/([A-Za-z0-9]+)",
        q
    )
    if sp:
        return ("spotify", sp.group(1), sp.group(2))
    # Deezer: track o playlist
    dz = re.match(
        r"https?://(?:www\.)?deezer\.com(?:/[a-z]{2})?/(track|playlist)/(\d+)",
        q
    )
    if dz:
        return ("deezer", dz.group(1), dz.group(2))
    return ("search", query)


# ──────────────────────────────────────────────────────────────────
#  PALETTE
# ──────────────────────────────────────────────────────────────────

C = {
    "bg":         "#090914",
    "bg2":        "#0e0e22",
    "bg3":        "#151530",
    "bg4":        "#1c1c3a",
    "border":     "#252550",
    "border_lt":  "#35356a",
    "purple":     "#7c3aed",
    "purple_lt":  "#a78bfa",
    "purple_dk":  "#5b21b6",
    "blue_dk":    "#1e3060",
    "blue":       "#3b82f6",
    "green":      "#10b981",
    "green_dk":   "#065f46",
    "cyan":       "#22d3ee",
    "cyan_dk":    "#164e63",
    "text":       "#e2e8f0",
    "text2":      "#8892aa",
    "text3":      "#4a5270",
    "red":        "#f87171",
    "row_alt":    "#0c0c1e",
    "sel":        "#2d1869",
}

# ──────────────────────────────────────────────────────────────────
#  STYLESHEET
# ──────────────────────────────────────────────────────────────────

STYLE = f"""
/* ── Base ── */
QWidget {{
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', sans-serif;
    font-size: 13px;
    color: {C['text']};
    background: transparent;
}}
QMainWindow, QWidget#root {{
    background: {C['bg']};
}}

/* ── Header ── */
QWidget#header {{
    background: {C['bg2']};
    border-bottom: 1px solid {C['border']};
}}
QLabel#appTitle {{
    font-size: 18px;
    font-weight: 800;
    color: {C['purple_lt']};
    letter-spacing: 3px;
}}
QLabel#appSub {{
    font-size: 11px;
    color: {C['text3']};
    letter-spacing: 0px;
    padding-left: 2px;
}}

/* ── Search ── */
QWidget#searchPanel {{
    background: {C['bg']};
    border-bottom: 1px solid {C['border']};
}}
QLineEdit#searchBar {{
    background: {C['bg3']};
    border: 1.5px solid {C['border']};
    border-radius: 9px;
    padding: 9px 16px;
    font-size: 14px;
    color: {C['text']};
    selection-background-color: {C['purple']};
}}
QLineEdit#searchBar:focus {{
    border-color: {C['purple']};
    background: {C['bg4']};
}}
QLineEdit#searchBar::placeholder {{
    color: {C['text3']};
}}

/* ── Buttons ── */
QPushButton {{
    border: none;
    border-radius: 8px;
    font-weight: 600;
    padding: 8px 16px;
}}
QPushButton#btnSearch {{
    background: {C['purple']};
    color: #fff;
    font-size: 13px;
    padding: 9px 20px;
    letter-spacing: 0px;
}}
QPushButton#btnSearch:hover  {{ background: {C['purple_lt']}; color: #1a0050; }}
QPushButton#btnSearch:pressed {{ background: {C['purple_dk']}; }}

QPushButton#btnClear {{
    background: {C['bg3']};
    border: 1.5px solid {C['border']};
    color: {C['text2']};
    font-size: 14px;
    padding: 8px 12px;
    border-radius: 8px;
}}
QPushButton#btnClear:hover {{ background: {C['border']}; color: {C['text']}; }}

QPushButton#btnSettings {{
    background: {C['purple_dk']};
    color: #ddd6fe;
    font-size: 12px;
    padding: 6px 14px;
    letter-spacing: 0px;
}}
QPushButton#btnSettings:hover {{ background: {C['purple']}; color: #fff; }}

QPushButton#btnLog {{
    background: {C['blue_dk']};
    color: #93c5fd;
    font-size: 12px;
    padding: 6px 14px;
    letter-spacing: 0px;
}}
QPushButton#btnLog:hover {{ background: {C['blue']}; color: #fff; }}

QPushButton#btnDownload {{
    background: {C['green']};
    color: #ecfdf5;
    font-size: 13px;
    font-weight: 700;
    padding: 9px 22px;
    letter-spacing: 0px;
}}
QPushButton#btnDownload:hover  {{ background: #34d399; color: #064e3b; }}
QPushButton#btnDownload:pressed {{ background: {C['green_dk']}; color: #a7f3d0; }}
QPushButton#btnDownload:disabled {{
    background: #0d2e20;
    color: {C['text3']};
}}

QPushButton#btnPlay {{
    background: {C['cyan_dk']};
    color: {C['cyan']};
    font-size: 13px;
    font-weight: 700;
    padding: 9px 20px;
}}
QPushButton#btnPlay:hover  {{ background: {C['cyan']}; color: #083344; }}
QPushButton#btnPlay:pressed {{ background: #0e7490; }}
QPushButton#btnPlay:disabled {{
    background: #0a1e24;
    color: {C['text3']};
}}

QPushButton#btnFolder {{
    background: {C['blue_dk']};
    color: #93c5fd;
    font-size: 13px;
    font-weight: 700;
    padding: 9px 20px;
}}
QPushButton#btnFolder:hover  {{ background: {C['blue']}; color: #fff; }}
QPushButton#btnFolder:pressed {{ background: #1d4ed8; }}

/* ── Table ── */
QTableWidget {{
    background: {C['bg2']};
    alternate-background-color: {C['row_alt']};
    color: {C['text']};
    border: 1.5px solid {C['border']};
    border-radius: 10px;
    gridline-color: {C['border']};
    selection-background-color: {C['sel']};
    selection-color: #c4b5fd;
    outline: none;
    font-size: 13px;
}}
QTableWidget::item {{
    padding: 6px 14px;
    border: none;
}}
QTableWidget::item:selected {{
    background: {C['sel']};
    color: #c4b5fd;
}}
QHeaderView::section {{
    background: {C['bg3']};
    color: {C['text3']};
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    padding: 9px 14px;
    border: none;
    border-bottom: 1.5px solid {C['border']};
}}
QHeaderView::section:first  {{ border-top-left-radius:  8px; }}
QHeaderView::section:last   {{ border-top-right-radius: 8px; }}

/* ── Scrollbar ── */
QScrollBar:vertical {{
    background: {C['bg2']};
    width: 7px;
    border-radius: 4px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C['border_lt']};
    border-radius: 4px;
    min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['purple']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: none; }}

/* ── Footer ── */
QWidget#footer {{
    background: {C['bg2']};
    border-top: 1px solid {C['border']};
}}

/* ── Combo ── */
QComboBox#fmtCombo {{
    background: {C['bg3']};
    border: 1.5px solid {C['border']};
    border-radius: 8px;
    padding: 7px 14px;
    color: {C['text']};
    font-size: 13px;
    font-weight: 600;
    min-width: 80px;
}}
QComboBox#fmtCombo:hover {{ border-color: {C['border_lt']}; }}
QComboBox#fmtCombo::drop-down {{
    border: none;
    width: 22px;
}}
QComboBox#fmtCombo::down-arrow {{
    width: 10px;
    height: 10px;
}}
QComboBox#fmtCombo QAbstractItemView {{
    background: {C['bg3']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 6px;
    selection-background-color: {C['purple']};
    selection-color: #fff;
    padding: 4px;
}}

/* ── Status bar ── */
QWidget#statusBar {{
    background: {C['bg']};
    border-top: 1px solid {C['border']};
}}
QProgressBar#progress {{
    background: {C['bg3']};
    border: none;
    border-radius: 3px;
    max-height: 5px;
    text-align: center;
}}
QProgressBar#progress::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 {C['purple']}, stop:1 {C['cyan']});
    border-radius: 3px;
}}
QLabel#statusMsg {{
    color: {C['text2']};
    font-size: 11px;
    letter-spacing: 0px;
}}

/* ── Dialogs ── */
QDialog {{
    background: {C['bg']};
    color: {C['text']};
}}
QTextEdit {{
    background: {C['bg2']};
    color: {C['text']};
    border: 1px solid {C['border']};
    border-radius: 8px;
    font-family: 'Cascadia Code', 'Consolas', 'Courier New', monospace;
    font-size: 12px;
    padding: 6px;
}}
QLabel {{
    color: {C['text']};
}}
"""

HEADERS_HTTP = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}


# ──────────────────────────────────────────────────────────────────
#  WORKERS
# ──────────────────────────────────────────────────────────────────

class SearchWorker(QThread):
    result_ready = pyqtSignal(list)
    error        = pyqtSignal(str)
    log          = pyqtSignal(str)

    def __init__(self, query: str):
        super().__init__()
        self.query = query

    # ── dispatcher ────────────────────────────────────────────────

    def run(self):
        try:
            q = self.query
            detected = _detect_link(q)
            if detected[0] == "spotify":
                self._handle_spotify(detected[1], detected[2])
            elif detected[0] == "deezer":
                self._handle_deezer_url(detected[1])
            else:
                self._handle_text_search(q)
        except Exception as e:
            self.error.emit(str(e))
            self.log.emit(f"[SEARCH] ❌ {e}")

    def _handle_text_search(self, query: str):
        self.log.emit(T("search_start_log", query=query))
        url = f"https://api.deezer.com/search?q={requests.utils.quote(query)}"
        try:
            data = requests.get(url, headers=HEADERS_HTTP, timeout=12).json()
            items = data.get("data", [])[:15] # Limita a 15 per velocità
            
            if not items:
                self.error.emit(T("search_no_results"))
                return

            self.log.emit(f"[SEARCH] Risoluzione dettagli per {len(items)} brani...")
            
            tracks = []
            # Usiamo ThreadPoolExecutor per fetchare i dettagli (ISRC + Cover) in parallelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                # Mappiamo gli ID alle chiamate get_track_detail
                future_to_id = {executor.submit(deezertrack.get_track_detail, i["id"]): i for i in items}
                for future in concurrent.futures.as_completed(future_to_id):
                    res = future.result()
                    if res:
                        tracks.append(res)
            
            if not tracks:
                self.error.emit(T("search_no_results"))
                return
            
            self.log.emit(T("search_result_log", n=len(tracks)))
            self.result_ready.emit(tracks)
        except Exception as e:
            self.error.emit(str(e))
            self.log.emit(f"[SEARCH] ❌ {e}")

    def _handle_deezer_url(self, track_id: str):
        self.log.emit(f"[SEARCH] Link Deezer rilevato — ID: {track_id}")
        res = deezertrack.handle_deezer_url(track_id)
        if res:
            self.log.emit(T("search_single_done"))
            self.result_ready.emit(res)
        else:
            self.error.emit(T("search_no_results"))

    def _handle_spotify(self, sp_type: str, sp_id: str):
        res = spotifytrack.handle_spotify(sp_type, sp_id, log_callback=self.log.emit)
        if res:
            self.log.emit(T("search_result_log", n=len(res)))
            self.result_ready.emit(res)
        else:
            self.error.emit(T("search_no_results"))


    def _fmt_dur(self, sec: int) -> str:
        m, s = divmod(sec, 60)
        return f"{m}:{s:02d}"

    # ── Deezer link ────────────────────────────────────────────────

    def _handle_deezer_url(self, track_id: str):
        self.log.emit(T("search_deezer_url_log", track_id=track_id))

        dz = requests.get(
            f"https://api.deezer.com/track/{track_id}",
            headers=HEADERS_HTTP,
            timeout=12,
        ).json()

        if dz.get("error") or not dz.get("id"):
            self.error.emit(T("err_deezer_url"))
            return

        isrc = dz.get("isrc", "")
        if isrc:
            self.log.emit(T("search_isrc_found_log", isrc=isrc))

        dur  = dz.get("duration", 0)
        m, s = divmod(dur, 60)

        track = {
            "deezer_id": dz["id"],
            "title":     dz.get("title", "—"),
            "artist":    dz.get("artist", {}).get("name", "—"),
            "album":     dz.get("album",  {}).get("title", "—"),
            "duration":  f"{m}:{s:02d}",
        }
        self.log.emit(T("search_single_done"))
        self.result_ready.emit([track])

    # ── Ricerca testo libero ───────────────────────────────────────

    def _handle_text_search(self, query: str):
        self.log.emit(T("search_query_log", query=query))
        url  = f"https://api.deezer.com/search?q={requests.utils.quote(query)}"
        data = requests.get(url, headers=HEADERS_HTTP, timeout=12).json()

        if not data.get("data"):
            self.error.emit(T("search_no_results"))
            return

        tracks = []
        for item in data["data"][:10]:
            dur  = item.get("duration", 0)
            m, s = divmod(dur, 60)
            tracks.append({
                "deezer_id": item["id"],
                "title":     item.get("title", "—"),
                "artist":    item["artist"]["name"],
                "album":     item["album"]["title"],
                "duration":  f"{m}:{s:02d}",
            })
            self.log.emit(
                f"[SEARCH]  {item.get('title')} — {item['artist']['name']}"
            )

        self.log.emit(T("search_result_log", n=len(tracks)))
        self.result_ready.emit(tracks)


# ──────────────────────────────────────────────────────────────────

class DownloadWorker(QThread):
    progress = pyqtSignal(int)
    status   = pyqtSignal(str)
    finished = pyqtSignal(str)
    error    = pyqtSignal(str)
    log      = pyqtSignal(str)
 
    def __init__(self, deezer_id, title, artist, album, fmt, isrc=None, custom_dir=None):
        super().__init__()
        self.deezer_id  = deezer_id
        self.title      = title
        self.artist     = artist
        self.album      = album
        self.fmt        = fmt   # 'mp3' | 'flac' | 'wav'
        self.isrc       = isrc
        self.custom_dir = custom_dir
 
    def run(self):
        try:
            self.log.emit(T("dl_start_log", title=self.title, artist=self.artist, fmt=self.fmt.upper()))
            # ── 7. File Finale ────────────────────────────────────
            out_dir = Path(self.custom_dir if self.custom_dir else self._music_dir())
            filename = self._clean(f"{self.artist} - {self.title}")
            final_path = out_dir / f"{filename}.{self.fmt}"
            
            # ── 1. ISRC ───────────────────────────────────────────
            isrc = self.isrc
            if not isrc:
                self.status.emit(T("dl_status_isrc"))
                self.progress.emit(5)
                track_info = requests.get(
                    f"https://api.deezer.com/track/{self.deezer_id}",
                    headers=HEADERS_HTTP, timeout=12
                ).json()
                isrc = track_info.get("isrc")
 
            if not isrc:
                self.error.emit(T("err_isrc_not_found"))
                return
            self.log.emit(T("dl_log_isrc", isrc=isrc))

            # ── 2. Qobuz ID via Monochrome ────────────────────────
            self.status.emit(T("dl_status_mono"))
            self.progress.emit(15)
            mono_url = (
                f"https://qdl-api.monochrome.tf/api/get-music?q={isrc}&offset=0"
            )
            mdata = requests.get(mono_url, headers=HEADERS_HTTP, timeout=20).json()

            if not mdata.get("success") or not mdata["data"]["tracks"]["items"]:
                self.error.emit(T("err_mono_not_found", isrc=isrc))
                return

            track     = mdata["data"]["tracks"]["items"][0]
            q_id      = track.get("id")
            cover_url = (
                track.get("album", {})
                     .get("image", {})
                     .get("large", "")
            )
            self.log.emit(
                T("dl_log_qobuz", q_id=q_id, has_cover=bool(cover_url))
            )

            # ── 3. Streaming URL ───────────────────────────────────
            self.status.emit(T("dl_status_stream"))
            self.progress.emit(25)
            dl_url  = (
                f"https://qdl-api.monochrome.tf/api/download-music"
                f"?track_id={q_id}&quality=6"
            )
            dl_data = requests.get(dl_url, headers=HEADERS_HTTP, timeout=25).json()

            if not dl_data.get("success") or "url" not in dl_data.get("data", {}):
                self.error.emit(T("err_stream_url"))
                return

            stream_url = dl_data["data"]["url"]
            self.log.emit(T("dl_log_stream"))

            # ── 4. Download audio ──────────────────────────────────
            self.status.emit(T("dl_status_audio"))
            self.progress.emit(30)

            music_dir = self._music_dir()
            resp  = requests.get(stream_url, stream=True, timeout=90)
            ct    = resp.headers.get("Content-Type", "").lower()
            src_ext = ".flac" if "flac" in ct else ".wav"

            total      = int(resp.headers.get("content-length", 0))
            temp_audio = os.path.join(music_dir, f"_wavver_tmp{src_ext}")
            downloaded = 0

            with open(temp_audio, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=32768):
                    fh.write(chunk)
                    downloaded += len(chunk)
                    if total:
                        pct = 30 + int(downloaded / total * 35)
                        self.progress.emit(pct)

            self.progress.emit(65)
            self.log.emit(
                T("dl_log_audio", kb=downloaded // 1024, ext=src_ext)
            )

            # ── 5. Download cover ──────────────────────────────────
            temp_cover = os.path.join(music_dir, "_wavver_cover.jpg")
            if cover_url:
                self.status.emit(T("dl_status_cover"))
                self.progress.emit(67)
                cr = requests.get(cover_url, timeout=12)
                with open(temp_cover, "wb") as fh:
                    fh.write(cr.content)
                self.log.emit(T("dl_log_cover"))

            # ── 6. Convert / copy ──────────────────────────────────
            self.status.emit(T("dl_status_convert", fmt=self.fmt.upper()))
            self.progress.emit(70)

            clean_name = (
                f"{self._clean(self.artist)} - {self._clean(self.title)}"
                f".{self.fmt}"
            )
            final_path = os.path.join(music_dir, clean_name)

            if self.fmt == "mp3":
                cmd = [
                    "ffmpeg", "-y", "-i", temp_audio,
                    "-codec:a", "libmp3lame", "-b:a", "320k",
                    final_path,
                ]
                subprocess.run(
                    cmd, check=True,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            elif self.fmt == "flac":
                if src_ext == ".flac":
                    shutil.copy2(temp_audio, final_path)
                else:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", temp_audio, final_path],
                        check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
            else:   # wav
                if src_ext == ".wav":
                    shutil.copy2(temp_audio, final_path)
                else:
                    subprocess.run(
                        ["ffmpeg", "-y", "-i", temp_audio, final_path],
                        check=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )

            self.progress.emit(88)
            self.log.emit(T("dl_log_convert", fmt=self.fmt.upper()))

            # ── 7. ID3 tags (MP3 only) ─────────────────────────────
            if self.fmt == "mp3" and MUTAGEN_OK:
                self.status.emit(T("dl_status_meta"))
                self.progress.emit(92)
                audio = MP3(final_path, ID3=ID3)
                try:
                    audio.add_tags()
                except Exception:
                    pass
                audio.tags.add(TIT2(encoding=3, text=self.title))
                audio.tags.add(TPE1(encoding=3, text=self.artist))
                audio.tags.add(TALB(encoding=3, text=self.album))
                if cover_url and os.path.exists(temp_cover):
                    with open(temp_cover, "rb") as img:
                        audio.tags.add(APIC(
                            encoding=3, mime="image/jpeg",
                            type=3, desc="Front Cover",
                            data=img.read()
                        ))
                audio.save()
                self.log.emit(T("dl_log_meta"))

            # ── 8. Cleanup ─────────────────────────────────────────
            for f in [temp_audio, temp_cover]:
                try:
                    if os.path.exists(f):
                        os.remove(f)
                except Exception:
                    pass

            self.progress.emit(100)
            self.status.emit(f"✅  {os.path.basename(final_path)}")
            self.log.emit(T("dl_log_done", path=final_path))
            self.finished.emit(final_path)

        except subprocess.CalledProcessError:
            self.error.emit(T("err_ffmpeg"))
            self.log.emit(T("err_ffmpeg_log"))
        except Exception as e:
            self.error.emit(str(e))
            self.log.emit(f"[DL] ❌ {e}")

    @staticmethod
    def _clean(s: str) -> str:
        return re.sub(r'[\\/*?:"<>|]', "", s).strip()

    @staticmethod
    def _music_dir() -> str:
        for candidate in ["~/Music", "~/Musica", "~/Música", "~/Musique"]:
            p = Path(candidate).expanduser()
            if p.exists():
                return str(p)
        p = Path("~/Music").expanduser()
        p.mkdir(parents=True, exist_ok=True)
        return str(p)


# ──────────────────────────────────────────────────────────────────
#  COVER LOADER THREAD
# ──────────────────────────────────────────────────────────────────

class CoverLoaderThread(QThread):
    """Scarica le copertine in background ed emette (riga, QPixmap)."""
    cover_loaded = pyqtSignal(int, QPixmap)

    def __init__(self, tracks: list):
        super().__init__()
        self._tracks = tracks
        self._stop   = False

    def stop(self):
        self._stop = True

    def run(self):
        for i, t in enumerate(self._tracks):
            if self._stop:
                break
            url = t.get("cover")
            if not url:
                continue
            try:
                r = requests.get(url, headers=HEADERS_HTTP, timeout=6)
                if r.status_code == 200:
                    px = QPixmap()
                    px.loadFromData(r.content)
                    if not px.isNull():
                        self.cover_loaded.emit(i, px)
            except Exception:
                pass


# ──────────────────────────────────────────────────────────────────
#  PLAYLIST WORKERS
# ──────────────────────────────────────────────────────────────────

class PlaylistResolverWorker(QThread):
    """Risolve un link playlist Spotify o Deezer in una lista di brani."""
    finished = pyqtSignal(list)
    error    = pyqtSignal(str)
    log      = pyqtSignal(str)

    def __init__(self, url: str):
        super().__init__()
        self.url = url

    def run(self):
        try:
            q = self.url.strip()
            # Spotify playlist
            sp = re.match(r"https?://open\.spotify\.com/(?:[\w-]+/)?playlist/([A-Za-z0-9]+)", q)
            if sp:
                self.log.emit(T("search_spotify_playlist_log", playlist_id=sp.group(1)))
                entity = spotifytrack.scrape_spotify_data("playlist", sp.group(1))
                if not entity:
                    self.log.emit("[PLAYLIST] ❌ Errore durante lo scraping di Spotify. La playlist potrebbe essere privata o il link non valido.")
                    self.error.emit(T("err_playlist_url"))
                    return
                
                self.log.emit("[PLAYLIST] Dati Spotify ricevuti, risoluzione brani su Deezer...")
                tracks = spotifytrack.handle_spotify("playlist", sp.group(1), log_callback=self.log.emit)
                if tracks:
                    self.finished.emit(tracks)
                else:
                    self.log.emit("[PLAYLIST] ❌ Nessun brano risolto. Assicurati che la playlist sia pubblica.")
                    self.error.emit(T("err_playlist_empty"))
                return

            # Deezer playlist
            dz = re.match(r"https?://(?:www\.)?deezer\.com(?:/[a-z]{2})?/playlist/(\d+)", q)
            if dz:
                self.log.emit(f"[PLAYLIST] Link Deezer rilevato: {dz.group(1)}")
                tracks = deezertrack.get_deezer_playlist(dz.group(1), log_cb=self.log.emit)
                if tracks:
                    self.finished.emit(tracks)
                else:
                    self.error.emit(T("err_playlist_empty"))
                return

            self.error.emit(T("err_playlist_url"))
        except Exception as e:
            self.error.emit(str(e))
            self.log.emit(f"[PLAYLIST] ❌ {e}")


class PlaylistDownloadWorker(QThread):
    """Scarica i brani di una playlist in modo sequenziale."""
    progress_item = pyqtSignal(int, int, str) # current, total, title
    progress_pct  = pyqtSignal(int)
    item_finished = pyqtSignal(int, str)      # row, status
    log           = pyqtSignal(str)
    finished      = pyqtSignal(int)           # total downloaded

    def __init__(self, tracks: list, fmt: str, save_dir: str = None):
        super().__init__()
        self.tracks   = tracks
        self.fmt      = fmt
        self.save_dir = save_dir
        self._stop    = False

    def stop(self):
        self._stop = True

    def run(self):
        count = 0
        total = len(self.tracks)
        for i, t in enumerate(self.tracks):
            if self._stop:
                break
            
            self.progress_item.emit(i + 1, total, t["title"])
            self.item_finished.emit(i, T("playlist_status_downloading"))
            
            try:
                dw = DownloadWorker(
                    t.get("deezer_id"), t["title"], t["artist"], t["album"], self.fmt,
                    isrc=t.get("isrc"), custom_dir=self.save_dir
                )
                # Colleghiamo solo il log per vedere cosa succede
                dw.log.connect(self.log.emit)
                # Eseguiamo dw.run() direttamente (è un metodo sincrono se chiamato così)
                dw.run()
                
                # Check se ha avuto successo (dovremmo idealmente avere un flag nel dw)
                # Per ora assumiamo successo se non lancia eccezioni critiche
                self.item_finished.emit(i, T("playlist_status_done"))
                count += 1
            except Exception as e:
                self.log.emit(T("playlist_dl_error", title=t["title"], err=str(e)))
                self.item_finished.emit(i, T("playlist_status_error"))

            self.progress_pct.emit(int((i + 1) / total * 100))

        self.finished.emit(count)


# ──────────────────────────────────────────────────────────────────
#  PLAYLIST DIALOG
# ──────────────────────────────────────────────────────────────────

class PlaylistDialog(QDialog):
    def __init__(self, parent=None, initial_url: str = ""):
        super().__init__(parent)
        self.setWindowTitle(T("playlist_title"))
        self.resize(800, 500)
        self.setStyleSheet(STYLE)

        self._tracks = []
        self._resolver_wk = None
        self._dl_wk = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(20, 20, 20, 20)
        lay.setSpacing(15)

        # Header
        hdr = QLabel(T("playlist_title"))
        hdr.setStyleSheet(f"font-size: 20px; font-weight: 800; color: {C['purple_lt']};")
        sub = QLabel(T("playlist_sub"))
        sub.setStyleSheet(f"font-size: 12px; color: {C['text2']};")
        lay.addWidget(hdr)
        lay.addWidget(sub)

        # Search box
        search_row = QHBoxLayout()
        self.url_edit = QLineEdit(initial_url)
        self.url_edit.setObjectName("searchBar")
        self.url_edit.setPlaceholderText(T("playlist_placeholder"))
        search_row.addWidget(self.url_edit, stretch=1)
        
        self.btn_load = QPushButton(T("btn_load_playlist"))
        self.btn_load.setObjectName("btnSearch")
        self.btn_load.clicked.connect(self._resolve_playlist)
        search_row.addWidget(self.btn_load)
        lay.addLayout(search_row)

        # Folder selection
        dir_row = QHBoxLayout()
        self.dir_edit = QLineEdit(DownloadWorker._music_dir())
        self.dir_edit.setObjectName("searchBar")
        self.dir_edit.setReadOnly(True)
        dir_row.addWidget(self.dir_edit, stretch=1)
        
        self.btn_dir = QPushButton("📁")
        self.btn_dir.setObjectName("btnSearch")
        self.btn_dir.setFixedWidth(40)
        self.btn_dir.clicked.connect(self._select_dir)
        dir_row.addWidget(self.btn_dir)
        lay.addLayout(dir_row)

        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels([
            T("playlist_col_num"), T("playlist_col_title"), T("playlist_col_artist"), T("playlist_col_status")
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.table.setColumnWidth(0, 40)
        self.table.setColumnWidth(3, 120)
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        lay.addWidget(self.table, stretch=1)

        # Footer
        footer = QHBoxLayout()
        
        fmt_lbl = QLabel(T("lbl_format"))
        footer.addWidget(fmt_lbl)
        
        self.fmt_combo = QComboBox()
        self.fmt_combo.setObjectName("fmtCombo")
        self.fmt_combo.addItems(["mp3", "flac", "wav"])
        footer.addWidget(self.fmt_combo)
        
        footer.addStretch()
        
        self.btn_dl = QPushButton(T("btn_download_all"))
        self.btn_dl.setObjectName("btnDownload")
        self.btn_dl.setEnabled(False)
        self.btn_dl.clicked.connect(self._start_download)
        footer.addWidget(self.btn_dl)
        
        self.btn_cancel = QPushButton(T("btn_cancel"))
        self.btn_cancel.setObjectName("btnClear")
        self.btn_cancel.clicked.connect(self._cancel)
        footer.addWidget(self.btn_cancel)

        self.btn_log = QPushButton(T("btn_log"))
        self.btn_log.setObjectName("btnLog")
        self.btn_log.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_log.clicked.connect(self._show_log)
        footer.addWidget(self.btn_log)
        
        lay.addLayout(footer)

        # Progress
        self.status_lbl = QLabel(T("status_ready"))
        self.status_lbl.setStyleSheet(f"font-size: 11px; color: {C['text3']};")
        lay.addWidget(self.status_lbl)
        
        self.prog = QProgressBar()
        self.prog.setObjectName("progress")
        self.prog.setFixedHeight(6)
        self.prog.setValue(0)
        self.prog.setTextVisible(False)
        lay.addWidget(self.prog)

        if initial_url:
            QTimer.singleShot(200, self._resolve_playlist)

    def _resolve_playlist(self):
        url = self.url_edit.text().strip()
        if not url: return
        
        self.btn_load.setEnabled(False)
        self.btn_dl.setEnabled(False)
        self.status_lbl.setText(T("playlist_loading"))
        self.table.setRowCount(0)
        
        self._resolver_wk = PlaylistResolverWorker(url)
        self._resolver_wk.finished.connect(self._on_resolved)
        self._resolver_wk.error.connect(self._on_error)
        self._resolver_wk.log.connect(self._log)
        self._resolver_wk.start()

    def _on_resolved(self, tracks):
        self._tracks = tracks
        self.btn_load.setEnabled(True)
        self.btn_dl.setEnabled(True)
        self.status_lbl.setText(T("playlist_loaded", n=len(tracks)))
        self._log(T("playlist_loaded", n=len(tracks)))
        
        for i, t in enumerate(tracks):
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(str(i+1)))
            self.table.setItem(i, 1, QTableWidgetItem(t["title"]))
            self.table.setItem(i, 2, QTableWidgetItem(t["artist"]))
            st_item = QTableWidgetItem(T("playlist_status_waiting"))
            st_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(i, 3, st_item)

    def _start_download(self):
        if not self._tracks: return
        
        self.btn_dl.setEnabled(False)
        self.btn_load.setEnabled(False)
        fmt = self.fmt_combo.currentText()
        save_dir = self.dir_edit.text().strip()
        
        self._log(f"[PLAYLIST] Avvio download sequenziale di {len(self._tracks)} brani in formato {fmt.upper()} in {save_dir}")

        self._dl_wk = PlaylistDownloadWorker(self._tracks, fmt, save_dir=save_dir)
        self._dl_wk.progress_item.connect(self._on_dl_item_progress)
        self._dl_wk.progress_pct.connect(self.prog.setValue)
        self._dl_wk.item_finished.connect(self._on_dl_item_finished)
        self._dl_wk.finished.connect(self._on_dl_finished)
        self._dl_wk.log.connect(self._log)
        self._dl_wk.start()

    def _on_dl_item_progress(self, current, total, title):
        self.status_lbl.setText(T("playlist_dl_progress", current=current, total=total, title=title))

    def _on_dl_item_finished(self, row, status):
        item = self.table.item(row, 3)
        if item:
            item.setText(status)
            if "✅" in status:
                item.setForeground(QColor(C["green"]))
            elif "❌" in status:
                item.setForeground(QColor(C["red"]))
            elif "⏳" in status:
                item.setForeground(QColor(C["cyan"]))
        self.table.scrollToItem(item)

    def _on_dl_finished(self, count):
        self.status_lbl.setText(T("playlist_dl_done", n=count))
        self.btn_load.setEnabled(True)
        self.btn_dl.setEnabled(True)
        self._log(T("playlist_dl_done", n=count))
        QMessageBox.information(self, T("playlist_title"), T("playlist_dl_done", n=count))

    def _on_error(self, msg):
        self.btn_load.setEnabled(True)
        self.status_lbl.setText(f"❌ {msg}")
        QMessageBox.critical(self, T("err_download_title"), msg)

    def _select_dir(self):
        d = QFileDialog.getExistingDirectory(self, "Seleziona Cartella", self.dir_edit.text())
        if d:
            self.dir_edit.setText(d)

    def _cancel(self):
        if self._dl_wk and self._dl_wk.isRunning():
            self._dl_wk.stop()
            self.status_lbl.setText(T("playlist_dl_cancelled"))
        else:
            self.reject()

    def _log(self, msg):
        # We can pipe this to the main window log if we want
        if self.parent() and hasattr(self.parent(), "_log"):
            self.parent()._log(msg)

    def _show_log(self):
        if self.parent() and hasattr(self.parent(), "_log_dlg"):
            self.parent()._log_dlg.show()
            self.parent()._log_dlg.raise_()


# ──────────────────────────────────────────────────────────────────
#  LOG DIALOG
# ──────────────────────────────────────────────────────────────────

class LogDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(T("log_title"))
        self.resize(680, 420)
        self.setStyleSheet(STYLE)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        hdr = QLabel(T("log_header"))
        hdr.setStyleSheet(
            f"font-size: 14px; font-weight: 700; color: {C['purple_lt']};"
        )
        lay.addWidget(hdr)

        self.view = QTextEdit()
        self.view.setReadOnly(True)
        lay.addWidget(self.view)

        row = QHBoxLayout()
        row.addStretch()
        btn = QPushButton(T("btn_clear_log"))
        btn.setObjectName("btnLog")
        btn.clicked.connect(self.view.clear)
        row.addWidget(btn)
        lay.addLayout(row)

    def append(self, msg: str):
        # ── Scrivi anche su file ──
        _write_log(msg)

        ts = datetime.now().strftime("%H:%M:%S")
        # Colour-code severity
        if "❌" in msg or "errore" in msg.lower() or "error" in msg.lower():
            col = C["red"]
        elif "✅" in msg:
            col = C["green"]
        elif "[SEARCH]" in msg:
            col = C["cyan"]
        else:
            col = C["text"]
        self.view.append(
            f'<span style="color:{C["text3"]}">[{ts}]</span> '
            f'<span style="color:{col}">{msg}</span>'
        )
        sb = self.view.verticalScrollBar()
        sb.setValue(sb.maximum())


# ──────────────────────────────────────────────────────────────────
#  SETTINGS DIALOG
# ──────────────────────────────────────────────────────────────────

class SettingsDialog(QDialog):
    def __init__(self, parent=None, music_dir: str = ""):
        super().__init__(parent)
        self.setWindowTitle(T("settings_title"))
        self.resize(440, 160)
        self.setStyleSheet(STYLE)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.setSpacing(12)

        lay.addWidget(QLabel(T("settings_lbl_folder")))

        row = QHBoxLayout()
        self.path_edit = QLineEdit(music_dir)
        self.path_edit.setObjectName("searchBar")
        row.addWidget(self.path_edit)

        btn_browse = QPushButton("…")
        btn_browse.setFixedWidth(38)
        btn_browse.setStyleSheet(
            f"background:{C['bg3']};border:1.5px solid {C['border']};"
            f"border-radius:8px;color:{C['text']};"
        )
        btn_browse.clicked.connect(self._browse)
        row.addWidget(btn_browse)
        lay.addLayout(row)

        lay.addStretch()

        btn_ok = QPushButton(T("btn_save"))
        btn_ok.setObjectName("btnDownload")
        btn_ok.clicked.connect(self.accept)
        lay.addWidget(btn_ok, alignment=Qt.AlignmentFlag.AlignRight)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(
            self, T("settings_browse_title"), self.path_edit.text()
        )
        if d:
            self.path_edit.setText(d)

    def get_dir(self) -> str:
        return self.path_edit.text().strip()


# ──────────────────────────────────────────────────────────────────
#  MAIN WINDOW
# ──────────────────────────────────────────────────────────────────

class MusicWavver(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(T("window_title"))
        self.setMinimumSize(820, 580)
        self.resize(960, 680)
        self.setStyleSheet(STYLE)

        self._tracks:    list  = []
        self._last_file: str   = ""
        self._log_dlg          = LogDialog(self)
        self._search_wk        = None
        self._dl_wk            = None
        self._cover_wk         = None

        root = QWidget()
        root.setObjectName("root")
        self.setCentralWidget(root)

        vbox = QVBoxLayout(root)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(0)

        vbox.addWidget(self._mk_header())
        vbox.addWidget(self._mk_search())
        vbox.addWidget(self._mk_table(), stretch=1)
        vbox.addWidget(self._mk_footer())
        vbox.addWidget(self._mk_statusbar())

    # ── Builder helpers ────────────────────────────────────────────

    def _mk_header(self) -> QWidget:
        w = QWidget()
        w.setObjectName("header")
        row = QHBoxLayout(w)
        row.setContentsMargins(22, 14, 22, 14)
        row.setSpacing(15)

        # Logo
        lbl_logo = QLabel()
        pix = QPixmap("Logo.png")
        if not pix.isNull():
            lbl_logo.setPixmap(
                pix.scaled(
                    40, 40,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        row.addWidget(lbl_logo)

        # Title column
        col = QVBoxLayout()
        col.setSpacing(2)
        lbl_title = QLabel(T("app_title"))
        lbl_title.setObjectName("appTitle")
        lbl_sub   = QLabel(T("app_sub"))
        lbl_sub.setObjectName("appSub")
        col.addWidget(lbl_title)
        col.addWidget(lbl_sub)

        row.addLayout(col)
        row.addStretch()

        btn_playlist = QPushButton(T("btn_playlist"))
        btn_playlist.setObjectName("btnPlay")
        btn_playlist.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_playlist.clicked.connect(self._open_playlist)

        btn_settings = QPushButton(T("btn_settings"))
        btn_settings.setObjectName("btnSettings")
        btn_settings.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_settings.clicked.connect(self._open_settings)

        btn_log = QPushButton(T("btn_log"))
        btn_log.setObjectName("btnLog")
        btn_log.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_log.clicked.connect(self._log_dlg.show)

        row.addWidget(btn_playlist)
        row.addSpacing(8)
        row.addWidget(btn_settings)
        row.addSpacing(8)
        row.addWidget(btn_log)
        return w

    def _mk_search(self) -> QWidget:
        w = QWidget()
        w.setObjectName("searchPanel")
        row = QHBoxLayout(w)
        row.setContentsMargins(22, 12, 22, 12)
        row.setSpacing(8)

        self.search_edit = QLineEdit()
        self.search_edit.setObjectName("searchBar")
        self.search_edit.setPlaceholderText(T("search_placeholder"))
        self.search_edit.returnPressed.connect(self._do_search)

        btn_clear = QPushButton("✕")
        btn_clear.setObjectName("btnClear")
        btn_clear.setFixedSize(36, 36)
        btn_clear.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_clear.clicked.connect(self.search_edit.clear)
        btn_clear.setToolTip(T("btn_clear_tooltip"))

        btn_search = QPushButton(T("btn_search"))
        btn_search.setObjectName("btnSearch")
        btn_search.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_search.clicked.connect(self._do_search)

        row.addWidget(self.search_edit, stretch=1)
        row.addWidget(btn_clear)
        row.addWidget(btn_search)
        return w

    def _mk_table(self) -> QWidget:
        w = QWidget()
        w.setStyleSheet(f"background: {C['bg']};")
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(22, 14, 22, 10)

        # ── Placeholder ──
        self._placeholder = QLabel(T("placeholder_empty"))
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet(
            f"color:{C['text3']}; font-size:15px; padding:50px;"
        )

        # ── Table ──
        self.table = QTableWidget(0, 4)
        self.table.setIconSize(QSize(42, 42))
        self.table.setHorizontalHeaderLabels(
            ["", T("col_title"), T("col_artist"), T("col_duration")]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Fixed
        )
        self.table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Fixed
        )
        self.table.setColumnWidth(0, 48)
        self.table.setColumnWidth(3, 76)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.NoEditTriggers
        )
        self.table.setAlternatingRowColors(True)
        self.table.setShowGrid(False)
        self.table.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.table.doubleClicked.connect(lambda _: self._do_download())

        self.table.hide()

        vbox.addWidget(self._placeholder, stretch=1)
        vbox.addWidget(self.table, stretch=1)
        return w

    def _mk_footer(self) -> QWidget:
        w = QWidget()
        w.setObjectName("footer")
        row = QHBoxLayout(w)
        row.setContentsMargins(22, 12, 22, 12)
        row.setSpacing(10)

        lbl_fmt = QLabel(T("lbl_format"))
        lbl_fmt.setStyleSheet(f"color:{C['text2']}; font-size:12px;")
        row.addWidget(lbl_fmt)

        self.fmt_combo = QComboBox()
        self.fmt_combo.setObjectName("fmtCombo")
        self.fmt_combo.addItems(["mp3", "flac", "wav"])
        row.addWidget(self.fmt_combo)

        row.addStretch()

        self.btn_dl = QPushButton(T("btn_download"))
        self.btn_dl.setObjectName("btnDownload")
        self.btn_dl.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_dl.clicked.connect(self._do_download)
        self.btn_dl.setEnabled(False)

        self.btn_play = QPushButton(T("btn_play"))
        self.btn_play.setObjectName("btnPlay")
        self.btn_play.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_play.clicked.connect(self._do_play)
        self.btn_play.setEnabled(False)

        btn_folder = QPushButton(T("btn_folder"))
        btn_folder.setObjectName("btnFolder")
        btn_folder.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_folder.clicked.connect(self._open_folder)

        row.addWidget(self.btn_dl)
        row.addWidget(self.btn_play)
        row.addWidget(btn_folder)
        return w

    def _mk_statusbar(self) -> QWidget:
        w = QWidget()
        w.setObjectName("statusBar")
        row = QHBoxLayout(w)
        row.setContentsMargins(22, 7, 22, 7)
        row.setSpacing(14)

        self.prog = QProgressBar()
        self.prog.setObjectName("progress")
        self.prog.setFixedWidth(200)
        self.prog.setFixedHeight(5)
        self.prog.setValue(0)
        self.prog.setTextVisible(False)

        self.status_lbl = QLabel(T("status_ready"))
        self.status_lbl.setObjectName("statusMsg")

        row.addWidget(self.prog)
        row.addStretch()
        row.addWidget(self.status_lbl)
        return w

    # ── Actions ────────────────────────────────────────────────────

    def _do_search(self):
        q = self.search_edit.text().strip()
        if not q:
            return

        # Rileva se è una playlist e apri il modulo dedicato
        detected = _detect_link(q)
        if (detected[0] == "spotify" and detected[1] == "playlist") or \
           (detected[0] == "deezer" and detected[1] == "playlist"):
            self.search_edit.clear()
            self._open_playlist(initial_url=q)
            return

        self._set_status(T("status_searching"), 0)
        self.btn_dl.setEnabled(False)
        self.table.hide()
        self._placeholder.setText(T("placeholder_searching"))
        self._placeholder.show()

        self._search_wk = SearchWorker(q)
        self._search_wk.result_ready.connect(self._on_results)
        self._search_wk.error.connect(self._on_search_err)
        self._search_wk.log.connect(self._log)
        self._search_wk.start()

    def _on_results(self, tracks: list):
        self._tracks = tracks
        self.table.setRowCount(0)

        # Stop previous cover loading if any
        if self._cover_wk:
            self._cover_wk.stop()
            self._cover_wk.wait()

        for i, t in enumerate(tracks):
            self.table.insertRow(i)
            self.table.setRowHeight(i, 52)

            title_item  = QTableWidgetItem(t["title"])
            artist_item = QTableWidgetItem(t["artist"])
            dur_item    = QTableWidgetItem(t["duration"])
            
            dur_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter
            )
            dur_item.setForeground(QColor(C["text2"]))

            self.table.setItem(i, 1, title_item)
            self.table.setItem(i, 2, artist_item)
            self.table.setItem(i, 3, dur_item)

        # Start cover loading thread
        self._cover_wk = CoverLoaderThread(tracks)
        self._cover_wk.cover_loaded.connect(self._on_cover_loaded)
        self._cover_wk.start()

        self._placeholder.hide()
        self.table.show()
        self.table.selectRow(0)
        self.btn_dl.setEnabled(True)

        if len(tracks) == 1:
            self._set_status(T("status_single"), 0)
        else:
            self._set_status(T("status_found", n=len(tracks)), 0)

    def _on_search_err(self, msg: str):
        self._placeholder.setText(f"❌  {msg}")
        self._set_status(f"❌  {msg}", 0)

    def _do_download(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._tracks):
            QMessageBox.warning(
                self,
                T("err_no_selection_title"),
                T("err_no_selection_msg"),
            )
            return

        t   = self._tracks[row]
        fmt = self.fmt_combo.currentText()
 
        self.btn_dl.setEnabled(False)
        self.btn_play.setEnabled(False)
        self._set_status(T("status_preparing", title=t["title"]), 5)
 
        self._dl_wk = DownloadWorker(
            t.get("deezer_id"), t["title"], t["artist"], t["album"], fmt,
            isrc=t.get("isrc")
        )
        self._dl_wk.progress.connect(self.prog.setValue)
        self._dl_wk.status.connect(lambda s: self._set_status(s))
        self._dl_wk.finished.connect(self._on_dl_done)
        self._dl_wk.error.connect(self._on_dl_err)
        self._dl_wk.log.connect(self._log)
        self._dl_wk.start()

    def _on_dl_done(self, path: str):
        self._last_file = path
        self.btn_dl.setEnabled(True)
        self.btn_play.setEnabled(True)
        self._set_status(
            T("status_saved", filename=os.path.basename(path)), 100
        )
        QTimer.singleShot(4000, lambda: self.prog.setValue(0))
        self._log(T("dl_log_ready", path=path))

    def _on_dl_err(self, msg: str):
        self.btn_dl.setEnabled(True)
        self._set_status(f"❌  {msg.splitlines()[0]}", 0)
        self.prog.setValue(0)
        QMessageBox.critical(self, T("err_download_title"), msg)

    def _do_play(self):
        if not self._last_file or not os.path.exists(self._last_file):
            self._set_status(T("status_no_file"), 0)
            return
        try:
            if sys.platform == "win32":
                os.startfile(self._last_file)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", self._last_file])
            else:
                subprocess.Popen(["xdg-open", self._last_file])
        except Exception as e:
            QMessageBox.warning(self, T("dlg_play_title"), str(e))

    def _open_folder(self):
        d = DownloadWorker._music_dir()
        try:
            if sys.platform == "win32":
                os.startfile(d)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", d])
            else:
                subprocess.Popen(["xdg-open", d])
        except Exception as e:
            QMessageBox.warning(self, T("dlg_folder_title"), str(e))

    def _open_settings(self):
        dlg = SettingsDialog(self, DownloadWorker._music_dir())
        dlg.exec()

    def _open_playlist(self, initial_url: str = ""):
        dlg = PlaylistDialog(self, initial_url=initial_url)
        dlg.exec()

    def _on_cover_loaded(self, row: int, pix: QPixmap):
        lbl = QLabel()
        lbl.setPixmap(pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setCellWidget(row, 0, lbl)

    def _set_status(self, msg: str, progress: int | None = None):
        self.status_lbl.setText(msg)
        if progress is not None:
            self.prog.setValue(progress)

    def _log(self, msg: str):
        """Invia il messaggio alla finestra di log (che lo scrive anche su file)."""
        self._log_dlg.append(msg)


# ──────────────────────────────────────────────────────────────────
#  ENTRY POINT
# ──────────────────────────────────────────────────────────────────

def main():
    # ── Set locale ──
    try:
        locale.setlocale(locale.LC_ALL, "")
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setApplicationName("Music Wavver 6")
    app.setApplicationVersion("6.0")

    # ── Carica le traduzioni — se manca il file, esci ──
    if not _load_languages():
        QMessageBox.critical(
            None,
            "Configuration Error",
            "languages.json not found.\nThe program will now close.",
        )
        sys.exit(1)

    # ── Prima riga nel log di avvio ──
    _write_log(T("startup_log", dt=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    # ── Palette ──
    pal = QPalette()
    bg  = QColor(C["bg"])
    txt = QColor(C["text"])
    pal.setColor(QPalette.ColorRole.Window,          bg)
    pal.setColor(QPalette.ColorRole.WindowText,      txt)
    pal.setColor(QPalette.ColorRole.Base,            QColor(C["bg2"]))
    pal.setColor(QPalette.ColorRole.AlternateBase,   QColor(C["row_alt"]))
    pal.setColor(QPalette.ColorRole.Text,            txt)
    pal.setColor(QPalette.ColorRole.Button,          QColor(C["bg3"]))
    pal.setColor(QPalette.ColorRole.ButtonText,      txt)
    pal.setColor(QPalette.ColorRole.Highlight,       QColor(C["purple"]))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    pal.setColor(QPalette.ColorRole.ToolTipBase,     QColor(C["bg3"]))
    pal.setColor(QPalette.ColorRole.ToolTipText,     txt)
    app.setPalette(pal)

    win = MusicWavver()
    win.show()
    ret = app.exec()

    _write_log(T("shutdown_log", dt=datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    sys.exit(ret)


if __name__ == "__main__":
    main()
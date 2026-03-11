#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA - 2026
MMUSIC WAVVER 5.0 Playlist Downloader
MADE IN ITALY
"""

import os
import sys
import re
import time
import json
import logging
import platform
import threading
import queue
import shutil
import requests

# ── Tkinter / CustomTkinter ────────────────────────────────────────────────────
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk, PhotoImage
from tkinter.ttk import Treeview, Style

# ── yt-dlp ─────────────────────────────────────────────────────────────────────
from yt_dlp import YoutubeDL  # type: ignore

# ── Mutagen (ID3) ───────────────────────────────────────────────────────────────
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, TCON, APIC, error as ID3Error
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

# ── Pillow ──────────────────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageTk
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


# ==============================================================================
#  COSTANTI / DEFAULTS
# ==============================================================================
DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Music")
LOG_FILE = "ytdownloader.log"
SETTINGS_FILE = "settings.json"

_DEFAULT_SETTINGS = {
    "download_dir": DEFAULT_DOWNLOAD_DIR,
    "speed_limit": "0",
    "audio_quality": "320",
    "playlist_format": "mp3",
    "playlist_subfolder": True,
    "write_id3": True,
    "notify_on_complete": True,
    "max_retries": 3,
    "retry_delay": 2,
    "language": "it",
}


def _load_settings() -> dict:
    settings = _DEFAULT_SETTINGS.copy()
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, v in data.items():
                if k in settings:
                    settings[k] = v
        except Exception:
            pass
    return settings


def _log(msg: str):
    print(msg)
    try:
        logging.info(msg)
    except Exception:
        pass


# ==============================================================================
#  UTILITY
# ==============================================================================

def _fmt_duration(sec) -> str:
    if not isinstance(sec, (int, float)):
        return str(sec) if sec else "?"
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"


def _safe_filename(name: str) -> str:
    """Rimuove caratteri non validi per nomi di cartelle/file."""
    return re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name).strip()


def _open_folder(path: str):
    try:
        sys_os = platform.system()
        if sys_os == "Windows":
            os.startfile(path)
        elif sys_os == "Darwin":
            import subprocess
            subprocess.call(["open", path])
        else:
            import subprocess
            subprocess.call(["xdg-open", path])
    except Exception as e:
        _log(f"WARN: Impossibile aprire cartella: {e}")


def _open_file(path: str):
    try:
        sys_os = platform.system()
        if sys_os == "Windows":
            os.startfile(path)
        elif sys_os == "Darwin":
            import subprocess
            subprocess.call(["open", path])
        else:
            import subprocess
            try:
                import subprocess
                subprocess.call(["xdg-open", path])
            except Exception:
                pass
    except Exception:
        pass


def _notify_desktop(title: str, message: str):
    try:
        sys_os = platform.system()
        if sys_os == "Darwin":
            import subprocess
            subprocess.run(
                ["osascript", "-e", f'display notification "{message}" with title "{title}"'],
                check=False
            )
        elif sys_os == "Linux":
            import subprocess
            subprocess.run(["notify-send", title, message], check=False)
        # Windows: usa messagebox come fallback (non blocca)
    except Exception:
        pass


# ==============================================================================
#  DEEZER ID3 TAGGER (copia autonoma, non dipende da app.py)
# ==============================================================================

class _DeezerTagger:
    API_BASE = "https://api.deezer.com"

    def clean_query(self, q: str) -> str:
        q = os.path.splitext(q)[0]
        q = re.sub(r"[\[\(].*?[\]\)]", "", q)
        terms = [
            "official", "video", "audio", "lyric", "lyrics", "hq", "hd",
            "4k", "1080p", "720p", "full", "song", "version", "oficial",
            "official video", "official audio", "music video", "mv", "clip",
            "visualizer", "live", "performance", "remix", "mix", "cover",
            "original", "extended", "radio edit",
        ]
        pattern = r"\b(" + "|".join(re.escape(t) for t in terms) + r")\b"
        q = re.sub(pattern, "", q, flags=re.IGNORECASE)
        q = re.sub(r"\s+", " ", q).strip()
        q = re.sub(r"[^\w\s\-]", "", q)
        return q or os.path.splitext(q)[0]

    def search(self, query: str, limit: int = 3) -> list:
        try:
            r = requests.get(f"{self.API_BASE}/search",
                             params={"q": self.clean_query(query), "limit": limit},
                             timeout=10)
            r.raise_for_status()
            data = r.json()
            results = []
            for t in data.get("data", []):
                results.append({
                    "title":        t.get("title", ""),
                    "artist":       t.get("artist", {}).get("name", ""),
                    "album":        t.get("album", {}).get("title", ""),
                    "year":         (t.get("release_date") or "").split("-")[0],
                    "genre":        (t.get("genre") or {}).get("name", ""),
                    "cover_url":    t.get("album", {}).get("cover_medium", ""),
                    "track_number": t.get("track_position", ""),
                    "duration":     t.get("duration", 0),
                })
            return results
        except Exception as e:
            _log(f"Deezer search error: {e}")
            return []

    def best_match(self, yt_title: str, yt_uploader: str, yt_dur=None):
        tracks = self.search(yt_title)
        if not tracks:
            return None
        scored = []
        for t in tracks:
            score = 0
            # Artista vs uploader
            if t["artist"].lower() in yt_uploader.lower() or yt_uploader.lower() in t["artist"].lower():
                score += 20
            # Titolo
            if t["title"].lower() in yt_title.lower() or yt_title.lower() in t["title"].lower():
                score += 20
            # Durata
            if yt_dur and t.get("duration"):
                diff = abs(int(yt_dur) - int(t["duration"]))
                if diff <= 5:
                    score += 40
                elif diff <= 15:
                    score += 15
                elif diff <= 30:
                    score += 10
            scored.append({**t, "score": score})
        scored.sort(key=lambda x: x["score"], reverse=True)
        best = scored[0] if scored else None
        return best if best and best["score"] >= 30 else None

    def download_cover(self, url: str):
        try:
            if not url:
                return None
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            return r.content
        except Exception:
            return None

    def apply_tags(self, filepath: str, meta: dict, cover=None) -> bool:
        if not MUTAGEN_AVAILABLE:
            return False
        try:
            audio = MP3(filepath, ID3=ID3)
            try:
                audio.add_tags()
            except ID3Error:
                pass
            if meta.get("title"):
                audio.tags.add(TIT2(encoding=3, text=meta["title"]))
            if meta.get("artist"):
                audio.tags.add(TPE1(encoding=3, text=meta["artist"]))
            if meta.get("album"):
                audio.tags.add(TALB(encoding=3, text=meta["album"]))
            if meta.get("year"):
                audio.tags.add(TYER(encoding=3, text=meta["year"]))
            if meta.get("genre"):
                audio.tags.add(TCON(encoding=3, text=meta["genre"]))
            if cover:
                audio.tags.add(APIC(encoding=3, mime="image/jpeg",
                                    type=3, desc="Cover", data=cover))
            audio.save()
            return True
        except Exception as e:
            _log(f"ID3 error: {e}")
            return False


# ==============================================================================
#  FUNZIONE PRINCIPALE PUBBLICA — chiamata da app.py
# ==============================================================================

def open_playlist_downloader(parent_window, url: str):
    """
    Punto d'ingresso pubblico.
    Viene chiamato da app.py con:
        from playlists import open_playlist_downloader
        open_playlist_downloader(self, url)
    """
    win = PlaylistDownloaderWindow(parent_window, url)
    # Non chiamare win.mainloop() — è un CTkToplevel, viene gestito dal loop del parent.


# ==============================================================================
#  FINESTRA PLAYLIST
# ==============================================================================

class PlaylistDownloaderWindow(ctk.CTkToplevel):
    """
    Finestra completa per il download di playlist YouTube (e altri siti yt-dlp).
    Funziona sia come Toplevel di app.py sia standalone.
    """

    def __init__(self, parent, url: str):
        super().__init__(parent)

        self._settings = _load_settings()
        self._url = url
        self._entries = []  # list of dicts
        self._playlist_info: dict = {}
        self._is_running = False
        self._is_paused = False
        self._is_cancelled = False
        self._done_count = 0
        self._fail_count = 0
        self._tagger = _DeezerTagger()

        self.title("Playlist Downloader — Music Wavver")
        self.geometry("820x640")
        self.minsize(700, 500)
        self.resizable(True, True)
        self.transient(parent)

        self._fmt_var      = ctk.StringVar(value=self._settings.get("playlist_format", "mp3"))
        self._subfolder_var = ctk.BooleanVar(value=self._settings.get("playlist_subfolder", True))
        self._outdir_var   = ctk.StringVar(value=self._settings.get("download_dir", DEFAULT_DOWNLOAD_DIR))
        self._status_var   = ctk.StringVar(value="Recupero informazioni playlist...")
        self._id3_var      = ctk.BooleanVar(value=self._settings.get("write_id3", True) and MUTAGEN_AVAILABLE)

        self._set_icon()
        self._build_ui()

        # Avvia fetch in background
        threading.Thread(target=self._fetch_thread, daemon=True).start()

    # ──────────────────────────────────────────────────────────────────────────
    #  ICON
    # ──────────────────────────────────────────────────────────────────────────

    def _set_icon(self):
        try:
            sys_os = platform.system()
            if sys_os == "Windows" and os.path.exists("logo.ico"):
                self.iconbitmap("logo.ico")
            elif sys_os == "Linux" and os.path.exists("logo.png"):
                self.iconphoto(True, PhotoImage(file="logo.png"))
            elif os.path.exists("logo.png") and PILLOW_AVAILABLE:
                img = ctk.CTkImage(
                    light_image=Image.open("logo.png"),
                    dark_image=Image.open("logo.png"),
                    size=(32, 32))
                # non applicabile direttamente a Toplevel come immagine
        except Exception:
            pass

    # ──────────────────────────────────────────────────────────────────────────
    #  BUILD UI
    # ──────────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # lista espandibile

        # ── Header ────────────────────────────────────────────────────────────
        hdr = ctk.CTkFrame(self)
        hdr.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 4))
        hdr.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(hdr, text="Download Playlist",
                     font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w", padx=12, pady=8)

        self._status_label = ctk.CTkLabel(hdr, textvariable=self._status_var,
                                           font=("Segoe UI", 11), text_color="gray",
                                           wraplength=480, anchor="e")
        self._status_label.grid(row=0, column=1, sticky="e", padx=12)

        # ── Lista brani ────────────────────────────────────────────────────────
        list_frame = ctk.CTkFrame(self)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=12, pady=4)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(0, weight=1)

        self._configure_tree_style()
        cols = ("#", "Titolo", "Durata", "Stato")
        self._tree = Treeview(list_frame, columns=cols, show="headings", height=16)
        self._tree.column("#",      width=44,  anchor="center", stretch=False)
        self._tree.column("Titolo", width=450, anchor="w")
        self._tree.column("Durata", width=75,  anchor="center", stretch=False)
        self._tree.column("Stato",  width=110, anchor="center", stretch=False)
        for c in cols:
            self._tree.heading(c, text=c)

        self._tree.tag_configure("pending",     foreground="#777799", background="#1A1A2E")
        self._tree.tag_configure("downloading", background="#0F3460", foreground="#90CAF9")
        self._tree.tag_configure("done",        foreground="#81C784", background="#1a3a1a")
        self._tree.tag_configure("failed",      foreground="#EF9A9A", background="#2a0000")
        self._tree.tag_configure("skipped",     foreground="#FFCC80")

        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        vsb.grid(row=0, column=1, sticky="ns", pady=5, padx=(0, 5))

        # ── Opzioni ────────────────────────────────────────────────────────────
        opts = ctk.CTkFrame(self)
        opts.grid(row=2, column=0, sticky="ew", padx=12, pady=2)

        ctk.CTkLabel(opts, text="Formato:").pack(side="left", padx=(10, 4))
        ctk.CTkOptionMenu(opts, variable=self._fmt_var,
                          values=["mp3", "wav", "flac", "m4a", "opus"],
                          width=90).pack(side="left", padx=(0, 12))

        ctk.CTkCheckBox(opts, text="Sottocartella col nome playlist",
                        variable=self._subfolder_var).pack(side="left", padx=(0, 12))

        if MUTAGEN_AVAILABLE:
            ctk.CTkCheckBox(opts, text="Scrivi tag ID3 (Deezer)",
                            variable=self._id3_var).pack(side="left", padx=(0, 12))

        # Cartella output
        dir_row = ctk.CTkFrame(opts, fg_color="transparent")
        dir_row.pack(side="left", padx=4)
        ctk.CTkLabel(dir_row, text="[ ]").pack(side="left")
        self._dir_lbl = ctk.CTkLabel(dir_row, textvariable=self._outdir_var,
                                      width=160, anchor="w",
                                      font=("Segoe UI", 11))
        self._dir_lbl.pack(side="left", padx=4)
        ctk.CTkButton(dir_row, text="Cambia", width=68,
                      command=self._choose_dir).pack(side="left")

        # ── Barre progresso ────────────────────────────────────────────────────
        prog_f = ctk.CTkFrame(self)
        prog_f.grid(row=3, column=0, sticky="ew", padx=12, pady=4)
        prog_f.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(prog_f, text="File corrente:").grid(
            row=0, column=0, sticky="w", padx=12, pady=(6, 0))
        self._prog_single = ctk.CTkProgressBar(prog_f, height=8,
                                               progress_color="#7C5CBF",
                                               fg_color="#222233", corner_radius=4)
        self._prog_single.set(0)
        self._prog_single.grid(row=1, column=0, sticky="ew", padx=12, pady=(2, 4))

        ctk.CTkLabel(prog_f, text="Progresso totale:").grid(
            row=2, column=0, sticky="w", padx=12)
        self._prog_total = ctk.CTkProgressBar(prog_f, height=12,
                                              progress_color="#4CAF50",
                                              fg_color="#222233", corner_radius=4)
        self._prog_total.set(0)
        self._prog_total.grid(row=3, column=0, sticky="ew", padx=12, pady=(2, 4))

        self._count_lbl = ctk.CTkLabel(prog_f,
                                        text="0 / 0  |  OK: 0  Err: 0",
                                        font=("Segoe UI", 12))
        self._count_lbl.grid(row=4, column=0, pady=(0, 6))

        # ── Pulsanti ───────────────────────────────────────────────────────────
        btn_row = ctk.CTkFrame(self, fg_color="transparent")
        btn_row.grid(row=4, column=0, pady=(4, 14))

        self._btn_start = ctk.CTkButton(
            btn_row, text="[>] Avvia Download",
            fg_color="#28a745", hover_color="#218838",
            width=170, height=40, font=("Segoe UI", 13, "bold"),
            command=self._start_download, state="disabled")
        self._btn_start.pack(side="left", padx=8)

        self._btn_pause = ctk.CTkButton(
            btn_row, text="|| Pausa",
            width=130, height=40,
            command=self._toggle_pause, state="disabled")
        self._btn_pause.pack(side="left", padx=8)

        self._btn_cancel = ctk.CTkButton(
            btn_row, text="[X] Annulla",
            fg_color="#dc3545", hover_color="#c82333",
            width=120, height=40,
            command=self._cancel_download, state="disabled")
        self._btn_cancel.pack(side="left", padx=8)

        self._btn_open = ctk.CTkButton(
            btn_row, text="Apri Cartella",
            width=140, height=40,
            command=self._open_output_dir, state="disabled")
        self._btn_open.pack(side="left", padx=8)

    @staticmethod
    def _configure_tree_style():
        s = Style()
        s.theme_use("clam")
        s.configure("Treeview",
                    background="#1A1A2E", foreground="#CCCCEE",
                    fieldbackground="#1A1A2E", rowheight=25,
                    font=("Segoe UI", 11))
        s.configure("Treeview.Heading",
                    background="#0F3460", foreground="#AAAACC",
                    relief="flat", font=("Segoe UI", 10, "bold"))
        s.map("Treeview.Heading", background=[("active", "#1e4080")])
        s.map("Treeview",
              background=[("selected", "#7C5CBF")],
              foreground=[("selected", "white")])
        s.configure("Vertical.TScrollbar",
                    background="#16213E", troughcolor="#1A1A2E", arrowcolor="#888899")

    # ──────────────────────────────────────────────────────────────────────────
    #  DIRECTORY
    # ──────────────────────────────────────────────────────────────────────────

    def _choose_dir(self):
        d = filedialog.askdirectory(initialdir=self._outdir_var.get(),
                                     title="Seleziona cartella di destinazione")
        if d:
            self._outdir_var.set(d)

    def _get_output_dir(self) -> str:
        base = self._outdir_var.get()
        if self._subfolder_var.get() and self._playlist_info.get("title"):
            folder_name = _safe_filename(self._playlist_info["title"])
            return os.path.join(base, folder_name)
        return base

    def _open_output_dir(self):
        _open_folder(self._get_output_dir())

    # ──────────────────────────────────────────────────────────────────────────
    #  FETCH PLAYLIST INFO
    # ──────────────────────────────────────────────────────────────────────────

    def _fetch_thread(self):
        try:
            opts = {
                "quiet":          True,
                "extract_flat":   "in_playlist",   # FIX: not just True
                "skip_download":  True,
                "socket_timeout": 30,
                "ignoreerrors":   True,
                "noplaylist":     False,            # FIX: must be False for playlists
            }
            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(self._url, download=False)

            if not info:
                raise ValueError("Nessuna informazione ottenuta dall'URL.")

            self._playlist_info = info
            raw_entries = info.get("entries") or []
            entries = []
            for e in raw_entries:
                if not e:
                    continue
                if not e.get("id"):
                    url_field = e.get("url", "")
                    if "watch?v=" in url_field:
                        e["id"] = url_field.split("watch?v=")[-1].split("&")[0]
                    elif url_field and len(url_field) == 11:
                        e["id"] = url_field
                if e.get("id"):
                    entries.append(e)
            self._entries = entries

            # Popola albero nel thread UI
            self.after(0, self._populate_tree, entries, info)

        except Exception as exc:
            _log(f"Fetch playlist error: {exc}")
            self.after(0, self._on_fetch_error, str(exc))

    def _populate_tree(self, entries: list, info: dict):
        self._tree.delete(*self._tree.get_children())
        for i, e in enumerate(entries, 1):
            dur = _fmt_duration(e.get("duration")) if e.get("duration") else "?"
            self._tree.insert("", "end", iid=str(i - 1),
                              values=(i, e.get("title", "Sconosciuto"), dur, "Attesa"),
                              tags=("pending",))

        title = info.get("title", "Playlist")
        total = len(entries)
        self._status_var.set(f"{title}  —  {total} brani")
        self._btn_start.configure(state="normal")
        _log(f"Playlist caricata: '{title}' — {total} brani")

    def _on_fetch_error(self, msg: str):
        self._status_var.set(f"Errore caricamento: {msg}")
        messagebox.showerror("Errore Playlist",
                             f"Impossibile caricare la playlist:\n\n{msg}", parent=self)

    # ──────────────────────────────────────────────────────────────────────────
    #  DOWNLOAD
    # ──────────────────────────────────────────────────────────────────────────

    def _start_download(self):
        if not self._entries:
            return
        self._is_running   = True
        self._is_paused    = False
        self._is_cancelled = False
        self._done_count   = 0
        self._fail_count   = 0

        out_dir = self._get_output_dir()
        os.makedirs(out_dir, exist_ok=True)

        self._btn_start.configure(state="disabled")
        self._btn_pause.configure(state="normal")
        self._btn_cancel.configure(state="normal")
        self._btn_open.configure(state="disabled")

        threading.Thread(
            target=self._download_worker,
            args=(out_dir, self._fmt_var.get()),
            daemon=True
        ).start()

    def _download_worker(self, out_dir: str, fmt: str):
        total = len(self._entries)
        settings = _load_settings()
        speed_limit = settings.get("speed_limit", "0")
        write_id3   = self._id3_var.get() if MUTAGEN_AVAILABLE else False

        for idx, entry in enumerate(self._entries):

            if self._is_cancelled:
                break

            # ── Attesa pausa ─────────────────────────────────────────────
            while self._is_paused and not self._is_cancelled:
                time.sleep(0.3)
            if self._is_cancelled:
                break

            title     = entry.get("title", f"Traccia {idx + 1}")
            video_url = f"https://www.youtube.com/watch?v={entry['id']}"

            # Aggiorna UI: stato "scaricando"
            self.after(0, self._set_row, str(idx), "downloading", "Scaricando...")
            self.after(0, self._status_var.set,
                       f"[{idx + 1}/{total}]  {title[:65]}")
            self.after(0, self._prog_single.set, 0)

            success = False
            try:
                downloaded_file = []  # mutabile per uso nel hook

                def hook(d, _file=downloaded_file):
                    if d["status"] == "downloading":
                        total_b = d.get("total_bytes_estimate") or d.get("total_bytes")
                        if total_b and total_b > 0:
                            pct = d.get("downloaded_bytes", 0) / total_b
                            self.after(0, self._prog_single.set, pct)
                    elif d["status"] == "finished":
                        _file.append(d.get("filename", ""))
                        self.after(0, self._prog_single.set, 1.0)

                outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")
                postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": fmt}]
                if fmt == "mp3":
                    postprocessors[0]["preferredquality"] = settings.get("audio_quality", "320")

                ydl_opts = {
                    "outtmpl": outtmpl,
                    "format": "bestaudio/best",
                    "quiet": True,
                    "noplaylist": True,
                    "postprocessors": postprocessors,
                    "progress_hooks": [hook],
                    "socket_timeout": 30,
                    "extractor_retries": 3,
                }
                if speed_limit and speed_limit != "0":
                    ydl_opts["ratelimit"] = speed_limit

                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(video_url, download=True)
                    if info:
                        base_path = ydl.prepare_filename(info).rsplit(".", 1)[0]
                        final_file = f"{base_path}.{fmt}"
                    else:
                        final_file = None

                # ── ID3 Tag ──────────────────────────────────────────────
                if write_id3 and final_file and os.path.exists(final_file) and fmt == "mp3":
                    try:
                        yt_dur = entry.get("duration")
                        yt_upl = entry.get("uploader", "")
                        match  = self._tagger.best_match(title, yt_upl, yt_dur)
                        if match:
                            cover = self._tagger.download_cover(match.get("cover_url", ""))
                            meta  = {k: match.get(k, "")
                                     for k in ("title", "artist", "album", "year", "genre")}
                            meta["track_number"] = str(match.get("track_number", ""))
                            self._tagger.apply_tags(final_file, meta, cover)
                    except Exception as e_id3:
                        _log(f"ID3 fallito per '{title}': {e_id3}")

                success = True
                self._done_count += 1
                self.after(0, self._set_row, str(idx), "done", "Completato")

            except Exception as exc:
                _log(f"Download fallito '{title}': {exc}")
                self._fail_count += 1
                self.after(0, self._set_row, str(idx), "failed", "Errore")

            # Aggiorna progresso totale
            done_so_far = self._done_count + self._fail_count
            self.after(0, self._prog_total.set, done_so_far / total)
            self.after(0, self._update_counter, done_so_far, total)

        # ── Fine ciclo ───────────────────────────────────────────────────────
        self._is_running = False

        if self._is_cancelled:
            final_msg = f"Download annullato  —  [OK] {self._done_count}  [ERR] {self._fail_count}"
        else:
            final_msg = (f"Completato!  [OK] {self._done_count} scaricati"
                         + (f"  [ERR] {self._fail_count} falliti" if self._fail_count else ""))
            if settings.get("notify_on_complete", True):
                _notify_desktop("Music Wavver",
                                f"Playlist completata! {self._done_count} brani scaricati.")

        self.after(0, self._status_var.set, final_msg)
        self.after(0, self._prog_total.set, 1.0)
        self.after(0, lambda: self._btn_pause.configure(state="disabled"))
        self.after(0, lambda: self._btn_cancel.configure(state="disabled"))
        self.after(0, lambda: self._btn_open.configure(state="normal"))
        self.after(0, lambda: self._btn_start.configure(state="normal", text="[>>]  Riscaricare?"))

    # ──────────────────────────────────────────────────────────────────────────
    #  UI HELPERS (chiamati via .after() dal worker thread)
    # ──────────────────────────────────────────────────────────────────────────

    def _set_row(self, iid: str, tag: str, status_text: str):
        try:
            vals = list(self._tree.item(iid, "values"))
            vals[3] = status_text
            self._tree.item(iid, values=vals, tags=(tag,))
            self._tree.see(iid)
        except Exception:
            pass

    def _update_counter(self, done: int, total: int):
        self._count_lbl.configure(
            text=f"{done} / {total}  |  [OK] {self._done_count}  [ERR] {self._fail_count}")

    # ──────────────────────────────────────────────────────────────────────────
    #  CONTROLLI
    # ──────────────────────────────────────────────────────────────────────────

    def _toggle_pause(self):
        if not self._is_paused:
            self._is_paused = True
            self._btn_pause.configure(text="[>] Riprendi")
            self._status_var.set("In pausa - premi [>] Riprendi per continuare")
        else:
            self._is_paused = False
            self._btn_pause.configure(text="|| Pausa")

    def _cancel_download(self):
        if messagebox.askyesno("Annulla Download",
                               "Sei sicuro di voler annullare il download della playlist?\n"
                               "I brani già scaricati verranno mantenuti.",
                               parent=self):
            self._is_cancelled = True
            self._is_paused    = False  # sblocca il loop di pausa


# ==============================================================================
#  STANDALONE — eseguito direttamente: python playlists.py <url>
# ==============================================================================

def _standalone_main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Music Wavver — Playlist Downloader autonomo"
    )
    parser.add_argument("url", nargs="?", help="URL della playlist YouTube")
    args = parser.parse_args()

    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")

    if args.url:
        url = args.url
    else:
        # Chiedi URL tramite GUI minima
        root = ctk.CTk()
        root.withdraw()
        import tkinter.simpledialog as sd
        url = sd.askstring("Music Wavver Playlist",
                           "Inserisci l'URL della playlist YouTube:",
                           parent=root)
        root.destroy()
        if not url:
            print("Nessun URL fornito. Uscita.")
            sys.exit(0)

    # Finestra principale (root) necessaria per CTkToplevel
    root = ctk.CTk()
    root.withdraw()  # nascosta — è solo il parent del Toplevel

    win = PlaylistDownloaderWindow(root, url)
    win.protocol("WM_DELETE_WINDOW", lambda: (root.quit(), root.destroy()))

    root.mainloop()


if __name__ == "__main__":
    _standalone_main()
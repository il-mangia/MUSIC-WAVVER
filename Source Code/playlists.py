#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PLAYLIST DOWNLOADER PER MUSIC WAVVER 4.5
- Integrazione perfetta con app.py
- Tag ID3 automatico (se Deezer disponibile)
- Ritentativi configurabili
- Salto file già scaricati
- Progresso dettagliato (per video e totale)
- Possibilità di riprovare i video falliti
- Piena gestione errori e logging
- CORRETTO: bug nell'ordine di creazione della treeview
"""

from tkinter import ttk
import os
import sys
import json
import threading
import queue
import logging
import platform
import time
import re
import traceback
from urllib.parse import urlparse, parse_qs
from typing import List, Dict, Optional, Tuple, Any, Set

import customtkinter as ctk
from tkinter import messagebox, filedialog, PhotoImage
from tkinter.ttk import Treeview, Style
from yt_dlp import YoutubeDL, DownloadError

# ---------------------- IMPORT DA APP PRINCIPALE (CON FALLBACK) ----------------------
try:
    # Tentativo di importazione dall'app principale
    from app import log, SETTINGS, save_settings, T, FFMPEG_PATH
    from app import DeezerID3Tagger
    DEEZER_AVAILABLE = True
    log("✅ Playlists: import riuscito da app.py")
except ImportError as e:
    # Fallback per esecuzione standalone o test
    import logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
    def log(msg): logging.info(msg)

    SETTINGS = {
        "download_dir": os.path.expanduser("~/Downloads"),
        "speed_limit": "0",
        "audio_quality": "320",
        "language": "it",
        "theme": "dark",
        "write_id3": False,
        "max_retries": 3,
        "retry_delay": 2,
    }
    DEEZER_AVAILABLE = False
    FFMPEG_PATH = None

    # Traduzioni minime di fallback (identiche a quelle di app.py)
    TRANSLATIONS = {
        "it": {
            "playlist_title": "Playlist Downloader",
            "playlist_select_dir": "Cartella download",
            "change_folder": "Cambia",
            "format_label": "Formato:",
            "playlist_download_btn": "▶️ Scarica playlist",
            "playlist_stop_btn": "⏹️ Ferma",
            "playlist_retry_failed": "🔄 Riprova falliti",
            "playlist_status_fetching": "Recupero playlist...",
            "playlist_error_no_videos": "Nessun video trovato.",
            "select_download_folder": "Seleziona cartella",
            "playlist_completed": "✅ Completata",
            "playlist_stopped": "Fermato",
            "playlist_current_video": "Video corrente:",
            "playlist_overall_progress": "Progresso:",
            "playlist_videos_found": "Trovati {} video",
            "playlist_error": "Errore",
            "playlist_download_completed": "{}/{} completati ({} falliti)",
            "playlist_download_stopped": "{}/{} completati (fermato)",
            "playlist_column_number": "#",
            "playlist_column_title": "Titolo",
            "playlist_column_duration": "Durata",
            "playlist_column_uploader": "Uploader",
            "playlist_column_status": "Stato",
            "playlist_column_progress": "Progresso",
            "playlist_confirm_close": "Download in corso. Chiudere?",
            "playlist_confirm_title": "Conferma",
            "playlist_error_invalid_url": "URL non valido",
            "playlist_error_private": "Video privato",
            "playlist_error_unavailable": "Video non disponibile",
            "playlist_retry_confirm": "Riprova i {} video falliti?",
            "playlist_retry_title": "Riprova falliti",
            "playlist_skip_existing": "Salta esistenti",
            "playlist_id3_applied": "ID3 applicato",
            "playlist_id3_failed": "ID3 fallito",
        },
        "en": {
            "playlist_title": "Playlist Downloader",
            "playlist_select_dir": "Download folder",
            "change_folder": "Change",
            "format_label": "Format:",
            "playlist_download_btn": "▶️ Download playlist",
            "playlist_stop_btn": "⏹️ Stop",
            "playlist_retry_failed": "🔄 Retry failed",
            "playlist_status_fetching": "Fetching playlist...",
            "playlist_error_no_videos": "No videos found.",
            "select_download_folder": "Select folder",
            "playlist_completed": "✅ Completed",
            "playlist_stopped": "Stopped",
            "playlist_current_video": "Current video:",
            "playlist_overall_progress": "Progress:",
            "playlist_videos_found": "Found {} videos",
            "playlist_error": "Error",
            "playlist_download_completed": "{}/{} completed ({} failed)",
            "playlist_download_stopped": "{}/{} completed (stopped)",
            "playlist_column_number": "#",
            "playlist_column_title": "Title",
            "playlist_column_duration": "Duration",
            "playlist_column_uploader": "Uploader",
            "playlist_column_status": "Status",
            "playlist_column_progress": "Progress",
            "playlist_confirm_close": "Download in progress. Close?",
            "playlist_confirm_title": "Confirm",
            "playlist_error_invalid_url": "Invalid URL",
            "playlist_error_private": "Private video",
            "playlist_error_unavailable": "Unavailable video",
            "playlist_retry_confirm": "Retry {} failed videos?",
            "playlist_retry_title": "Retry failed",
            "playlist_skip_existing": "Skip existing",
            "playlist_id3_applied": "ID3 applied",
            "playlist_id3_failed": "ID3 failed",
        }
    }
    def T(key, **kwargs):
        lang = SETTINGS.get("language", "it")
        text = TRANSLATIONS.get(lang, TRANSLATIONS["it"]).get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except:
                pass
        return text

# ---------------------- COSTANTI ----------------------
PLAYLIST_LOG_FILE = "playlist_urls.log"
MAX_RETRIES = SETTINGS.get("max_retries", 3)
RETRY_DELAY = SETTINGS.get("retry_delay", 2)
SKIP_EXISTING = True  # può essere reso opzionale in futuro

# Logger separato per URL delle playlist
playlist_logger = logging.getLogger("playlist_urls")
playlist_logger.setLevel(logging.INFO)
playlist_logger.propagate = False
if not playlist_logger.handlers:
    try:
        fh = logging.FileHandler(PLAYLIST_LOG_FILE, mode='a', encoding='utf-8')
        fh.setFormatter(logging.Formatter('%(message)s'))
        playlist_logger.addHandler(fh)
    except Exception as e:
        log(f"⚠️ Impossibile creare file log playlist: {e}")

def log_playlist_url(url: str) -> None:
    """Registra un URL della playlist nel file di log."""
    try:
        playlist_logger.info(url)
    except Exception:
        pass

# ---------------------- UTILITY ----------------------
def clean_playlist_url(url: str) -> Optional[str]:
    """Pulisce l'URL mantenendo solo il parametro 'list'."""
    try:
        parsed = urlparse(url)
        query = parse_qs(parsed.query)
        playlist_id = query.get("list", [None])[0]
        if playlist_id:
            return f"https://www.youtube.com/playlist?list={playlist_id}"
        if "playlist" in parsed.path:
            return url
        return None
    except Exception:
        return None

def is_playlist_url(url: str) -> bool:
    """Verifica se l'URL è una playlist."""
    return "list=" in url or "/playlist" in url

def safe_filename(title: str, max_len: int = 100) -> str:
    """Rimuove caratteri non validi per nomi file."""
    return re.sub(r'[\\/*?:"<>|]', "_", title)[:max_len]

def format_duration(seconds: Optional[int]) -> str:
    """Converte secondi in MM:SS o HH:MM:SS."""
    if not seconds:
        return "N/D"
    try:
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if h:
            return f"{h:02d}:{m:02d}:{s:02d}"
        return f"{m:02d}:{s:02d}"
    except:
        return "N/D"

# ---------------------- PLAYLIST DOWNLOADER (CLASSE PRINCIPALE) ----------------------
class PlaylistDownloader(ctk.CTkToplevel):
    """
    Finestra modale per il download di playlist YouTube.
    """

    def __init__(self, master, url: str):
        super().__init__(master)
        self.title(T("playlist_title"))
        self.geometry("980x750")
        self.minsize(900, 650)
        self.transient(master)

        self._set_icon()

        # Pulisci URL
        self.original_url = url
        self.playlist_url = clean_playlist_url(url)

        if not self.playlist_url:
            messagebox.showerror(
                T("playlist_error"),
                T("playlist_error_invalid_url", url=self.original_url),
                parent=self
            )
            self.destroy()
            return

        # Stato interno
        self.playlist_videos: List[Dict] = []
        self.downloading = False
        self.stop_requested = False
        self.current_index = 0
        self.completed = 0
        self.failed = 0
        self.failed_indices: List[int] = []          # indici originali dei video falliti
        self.video_progress: Dict[int, float] = {}
        self.lock = threading.Lock()

        # Coda per comunicazione thread → GUI
        self.queue = queue.Queue()

        # Variabili UI
        self.download_dir = ctk.StringVar(value=SETTINGS.get("download_dir", ""))
        self.format = ctk.StringVar(value="mp3")
        self.status_text = ctk.StringVar(value=T("playlist_status_fetching"))
        self.current_video = ctk.StringVar(value="")
        self.overall_progress_text = ctk.StringVar(value="0/0")
        self.overall_progress_var = ctk.DoubleVar(value=0.0)

        # Crea Deezer tagger se disponibile
        self.deezer_tagger = DeezerID3Tagger() if DEEZER_AVAILABLE else None

        # Costruisce UI
        self._build_ui()

        # Pulisce il file di log all'avvio
        try:
            open(PLAYLIST_LOG_FILE, "w").close()
        except Exception as e:
            log(f"⚠️ Impossibile pulire file log: {e}")

        # Avvia thread di recupero playlist
        self.search_thread = threading.Thread(
            target=self._fetch_playlist_thread,
            daemon=True,
            name="PlaylistFetch"
        )
        self.search_thread.start()

        # Avvia loop di processazione coda
        self.after(100, self._process_queue)

        # Gestione chiusura finestra
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _set_icon(self):
        """Imposta l'icona della finestra in base al sistema."""
        try:
            if platform.system() == "Windows" and os.path.exists("logo.ico"):
                self.iconbitmap("logo.ico")
            elif platform.system() == "Linux" and os.path.exists("logo.png"):
                img = PhotoImage(file="logo.png")
                self.iconphoto(False, img)
        except Exception as e:
            log(f"⚠️ Icona playlist: {e}")

    def _build_ui(self):
        """Costruisce l'interfaccia utente."""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)

        # --- Intestazione ---
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=15, pady=(15,5))
        ctk.CTkLabel(
            title_frame,
            text="📋 " + T("playlist_title"),
            font=("Segoe UI", 18, "bold")
        ).pack(side="left")

        # --- Info URL (con wrap) ---
        info_frame = ctk.CTkFrame(self)
        info_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=5)
        info_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(info_frame, text=T("playlist_url_label"), font=("Segoe UI", 11, "bold")).grid(
            row=0, column=0, sticky="w", padx=10, pady=(8,2)
        )
        url_display = self.playlist_url if len(self.playlist_url) <= 120 else self.playlist_url[:120] + "..."
        ctk.CTkLabel(
            info_frame,
            text=url_display,
            font=("Segoe UI", 10),
            text_color="gray",
            wraplength=850,
            justify="left"
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0,8))

        # --- Cartella download ---
        ctk.CTkLabel(self, text=T("playlist_select_dir"), font=("Segoe UI", 12)).grid(
            row=2, column=0, sticky="w", padx=15, pady=(10,2)
        )
        dir_frame = ctk.CTkFrame(self)
        dir_frame.grid(row=3, column=0, sticky="ew", padx=15, pady=(0,10))
        dir_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(dir_frame, textvariable=self.download_dir, wraplength=750).grid(
            row=0, column=0, sticky="w", padx=12, pady=8
        )
        ctk.CTkButton(dir_frame, text=T("change_folder"), command=self._change_dir, width=100).grid(
            row=0, column=1, padx=12, pady=8
        )

        # --- Tabella video con scroll ---
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=4, column=0, sticky="nsew", padx=15, pady=(0,10))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Definizione colonne
        columns = (
            T("playlist_column_number"),
            T("playlist_column_title"),
            T("playlist_column_duration"),
            T("playlist_column_uploader"),
            T("playlist_column_status"),
            T("playlist_column_progress"),
        )

        # Creazione Treeview
        self.tree = Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=15,
            selectmode="extended"
        )

        # Configura larghezza colonne
        self.tree.column("#1", width=50, anchor="center", minwidth=40)
        self.tree.column("#2", width=350, anchor="w", minwidth=200)
        self.tree.column("#3", width=80, anchor="center", minwidth=60)
        self.tree.column("#4", width=150, anchor="w", minwidth=100)
        self.tree.column("#5", width=120, anchor="center", minwidth=100)
        self.tree.column("#6", width=100, anchor="center", minwidth=80)

        for col in columns:
            self.tree.heading(col, text=col)

        # Scrollbar
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        # Configura stile e tag DOPO aver creato self.tree
        self._configure_treeview_style()

        # --- Pannello controlli ---
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=5, column=0, sticky="ew", padx=15, pady=(0,10))
        controls_frame.grid_columnconfigure(0, weight=1)

        # Formato e opzioni
        left_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        ctk.CTkLabel(left_frame, text=T("format_label"), font=("Segoe UI", 12)).pack(side="left", padx=(0,10))
        format_menu = ctk.CTkOptionMenu(
            left_frame,
            variable=self.format,
            values=["mp3", "wav", "flac"],
            width=100
        )
        format_menu.pack(side="left", padx=(0,20))

        self.skip_var = ctk.BooleanVar(value=SKIP_EXISTING)
        skip_check = ctk.CTkCheckBox(
            left_frame,
            text=T("playlist_skip_existing"),
            variable=self.skip_var,
            checkbox_width=18,
            checkbox_height=18
        )
        skip_check.pack(side="left", padx=5)

        # Pulsanti destra
        right_frame = ctk.CTkFrame(controls_frame, fg_color="transparent")
        right_frame.grid(row=0, column=1, sticky="e", padx=10, pady=5)

        self.btn_retry = ctk.CTkButton(
            right_frame,
            text=T("playlist_retry_failed"),
            command=self._retry_failed,
            state="disabled",
            fg_color="#ffc107",
            hover_color="#e0a800",
            text_color="black",
            width=120
        )
        self.btn_retry.pack(side="right", padx=5)

        self.btn_stop = ctk.CTkButton(
            right_frame,
            text=T("playlist_stop_btn"),
            command=self._stop_download,
            state="disabled",
            fg_color="#dc3545",
            hover_color="#c82333",
            width=100
        )
        self.btn_stop.pack(side="right", padx=5)

        self.btn_download = ctk.CTkButton(
            right_frame,
            text=T("playlist_download_btn"),
            command=self._start_download,
            state="disabled",
            width=140
        )
        self.btn_download.pack(side="right", padx=5)

        # --- Stato corrente ---
        current_frame = ctk.CTkFrame(self)
        current_frame.grid(row=6, column=0, sticky="ew", padx=15, pady=(0,5))
        current_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(current_frame, text=T("playlist_current_video"), font=("Segoe UI", 11)).grid(
            row=0, column=0, sticky="w", padx=10, pady=5
        )
        ctk.CTkLabel(current_frame, textvariable=self.current_video, font=("Segoe UI", 11, "bold")).grid(
            row=0, column=1, sticky="w", padx=10, pady=5
        )

        # --- Barra progresso totale ---
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=7, column=0, sticky="ew", padx=15, pady=(0,5))
        progress_frame.grid_columnconfigure(0, weight=1)

        self.overall_label = ctk.CTkLabel(
            progress_frame,
            textvariable=self.overall_progress_text,
            font=("Segoe UI", 12)
        )
        self.overall_label.grid(row=0, column=0, sticky="w", padx=10, pady=5)

        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            variable=self.overall_progress_var
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", padx=10, pady=(0,5))

        # --- Status bottom ---
        status_frame = ctk.CTkFrame(self)
        status_frame.grid(row=8, column=0, sticky="ew", padx=15, pady=(0,15))
        status_frame.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            status_frame,
            textvariable=self.status_text,
            font=("Segoe UI", 11),
            wraplength=850,
            justify="left"
        ).grid(row=0, column=0, sticky="w", padx=10, pady=10)

    def _configure_treeview_style(self):
        """Configura lo stile della treeview con colori."""
        style = Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            borderwidth=1,
            relief="solid",
            font=("Segoe UI", 10),
            rowheight=25
        )
        style.configure(
            "Treeview.Heading",
            background="#f0f0f0",
            foreground="black",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padding=(5,5)
        )
        style.map("Treeview.Heading", background=[("active", "#e0e0e0")])
        style.map(
            "Treeview",
            background=[("selected", "#0078d7")],
            foreground=[("selected", "white")]
        )

        # Tag per stati (self.tree esiste già)
        self.tree.tag_configure("downloading", background="#cce5ff", foreground="#004085")
        self.tree.tag_configure("completed", background="#d4edda", foreground="#155724")
        self.tree.tag_configure("failed", background="#f8d7da", foreground="#721c24")
        self.tree.tag_configure("skipped", background="#fff3cd", foreground="#856404")
        self.tree.tag_configure("id3_applied", background="#d1ecf1", foreground="#0c5460")

    def _change_dir(self):
        """Cambia la directory di download."""
        directory = filedialog.askdirectory(
            initialdir=self.download_dir.get(),
            title=T("select_download_folder")
        )
        if directory:
            self.download_dir.set(directory)
            log(f"📁 Cartella playlist cambiata in: {directory}")

    def _fetch_playlist_thread(self):
        """Thread per recuperare i video della playlist."""
        try:
            log(f"🔍 Recupero playlist: {self.playlist_url}")
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "extract_flat": True,
                "skip_download": True,
                "ignoreerrors": True,
                "socket_timeout": 30,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.playlist_url, download=False)

            if not info:
                self.queue.put(("error", "Impossibile ottenere informazioni playlist"))
                return

            entries = info.get("entries", [])
            if not entries:
                self.queue.put(("error", T("playlist_error_no_videos")))
                return

            videos = []
            for idx, entry in enumerate(entries):
                if entry and entry.get("id"):
                    video = {
                        "id": entry["id"],
                        "title": entry.get("title", f"Video {idx+1}")[:100],
                        "duration": entry.get("duration"),
                        "uploader": entry.get("uploader", entry.get("channel", "Sconosciuto"))[:50],
                        "url": f"https://www.youtube.com/watch?v={entry['id']}",
                    }
                    videos.append(video)
                    log_playlist_url(video["url"])

            if videos:
                self.queue.put(("videos_loaded", videos))
            else:
                self.queue.put(("error", T("playlist_error_no_videos")))

        except Exception as e:
            log(f"❌ Errore recupero playlist: {e}\n{traceback.format_exc()}")
            self.queue.put(("error", str(e)))

    def _start_download(self):
        """Avvia il download della playlist."""
        if self.downloading:
            return
        if not self.playlist_videos:
            messagebox.showerror(T("playlist_error"), T("playlist_error_no_videos_found"), parent=self)
            return

        # Verifica directory
        if not os.path.exists(self.download_dir.get()):
            try:
                os.makedirs(self.download_dir.get(), exist_ok=True)
            except Exception as e:
                messagebox.showerror(T("playlist_error"), f"Impossibile creare directory:\n{e}", parent=self)
                return

        self.downloading = True
        self.stop_requested = False
        self.completed = 0
        self.failed = 0
        self.failed_indices.clear()
        self.current_index = 0
        self.video_progress.clear()

        # Reset UI
        self.btn_download.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self.btn_retry.configure(state="disabled")
        self.progress_bar.configure(mode="determinate")
        self.overall_progress_var.set(0)

        # Reset righe
        for i in range(len(self.playlist_videos)):
            self.tree.set(str(i), T("playlist_column_status"), "⏳ In attesa")
            self.tree.set(str(i), T("playlist_column_progress"), "0%")
            self.tree.item(str(i), tags=())

        total = len(self.playlist_videos)
        self.overall_progress_text.set(f"0/{total} - 0%")
        self.status_text.set(T("playlist_status_downloading", current=1, total=total))

        log(f"▶️ Avvio download playlist: {total} video")

        # Thread principale di download
        self.download_thread = threading.Thread(
            target=self._download_playlist_thread,
            daemon=True,
            name="PlaylistDownload"
        )
        self.download_thread.start()

    def _stop_download(self):
        """Richiede l'arresto del download."""
        if self.downloading and not self.stop_requested:
            self.stop_requested = True
            self.status_text.set("⏹️ Arresto in corso...")
            log("⏹️ Richiesto arresto download playlist")

    def _retry_failed(self):
        """Riprova i video falliti."""
        if not self.failed_indices:
            return
        if self.downloading:
            return

        # Conferma
        if not messagebox.askyesno(
            T("playlist_retry_title"),
            T("playlist_retry_confirm", count=len(self.failed_indices)),
            parent=self
        ):
            return

        # Filtra la lista dei video mantenendo solo quelli falliti (basati sugli indici originali)
        # Nota: self.playlist_videos contiene ancora tutti i video originali
        failed_videos = [self.playlist_videos[i] for i in self.failed_indices]
        self.playlist_videos = failed_videos

        # Ricrea la tabella con i soli video falliti
        self._refresh_table_from_failed()

        # Pulisci la lista degli indici falliti (ora sono tutti da processare)
        self.failed_indices.clear()

        # Riavvia il download
        self._start_download()

    def _refresh_table_from_failed(self):
        """Aggiorna la tabella mostrando solo i video falliti."""
        self.tree.delete(*self.tree.get_children())
        for new_idx, video in enumerate(self.playlist_videos):
            self.tree.insert(
                "",
                "end",
                iid=str(new_idx),
                values=(
                    new_idx + 1,
                    video["title"],
                    format_duration(video.get("duration")),
                    video["uploader"],
                    "In attesa",
                    "0%"
                )
            )
        self.overall_progress_text.set(f"0/{len(self.playlist_videos)} - 0%")

    def _download_playlist_thread(self):
        """Thread principale che esegue i download uno dopo l'altro."""
        total = len(self.playlist_videos)
        for idx, video in enumerate(self.playlist_videos):
            if self.stop_requested:
                break

            self.current_index = idx
            self.queue.put(("video_start", (idx, video["title"])))

            # Controllo esistenza file (se skip attivo)
            if self.skip_var.get():
                expected_filename = self._get_expected_filename(video, idx)
                if expected_filename and os.path.exists(expected_filename):
                    log(f"⏭️ File già esistente, salto: {expected_filename}")
                    with self.lock:
                        self.completed += 1
                    self.queue.put(("video_skipped", idx))
                    self.queue.put(("overall_progress", (self.completed, self.failed, total)))
                    continue

            # Download con retry
            success = False
            for attempt in range(1, MAX_RETRIES + 1):
                if self.stop_requested:
                    break
                try:
                    log(f"📥 Download [{idx+1}/{total}] tentativo {attempt}: {video['title']}")
                    self._download_single_video(video, idx, attempt)
                    success = True
                    break
                except Exception as e:
                    log(f"❌ Tentativo {attempt} fallito: {e}")
                    if attempt < MAX_RETRIES:
                        time.sleep(RETRY_DELAY)
                    else:
                        log(f"❌ Video fallito dopo {MAX_RETRIES} tentativi: {video['title']}")

            if success:
                with self.lock:
                    self.completed += 1
                self.queue.put(("video_done", idx))
                # Applica ID3 se necessario (in un thread separato per non bloccare)
                if self.format.get() == "mp3" and SETTINGS.get("write_id3") and self.deezer_tagger:
                    self._apply_id3_in_background(video, idx)
            else:
                with self.lock:
                    self.failed += 1
                    self.failed_indices.append(idx)  # idx è l'indice corrente nella lista ristretta
                self.queue.put(("video_failed", idx))

            # Aggiorna progresso generale
            self.queue.put(("overall_progress", (self.completed, self.failed, total)))

            # Piccola pausa tra i video
            time.sleep(0.5)

        # Completato o fermato
        if self.stop_requested:
            self.queue.put(("download_stopped", (self.completed, self.failed)))
        else:
            self.queue.put(("download_completed", (self.completed, self.failed)))

    def _get_expected_filename(self, video: Dict, idx: int) -> Optional[str]:
        """Restituisce il percorso completo atteso per il video."""
        try:
            base = safe_filename(f"{idx+1:03d}. {video['title']}")
            ext = self.format.get()
            return os.path.join(self.download_dir.get(), f"{base}.{ext}")
        except:
            return None

    def _download_single_video(self, video: Dict, idx: int, attempt: int):
        """Esegue il download effettivo di un singolo video."""
        output_template = os.path.join(
            self.download_dir.get(),
            f"%(title)s.%(ext)s"
        )

        # Prepara opzioni yt-dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "progress_hooks": [self._create_progress_hook(idx)],
            "ignoreerrors": True,
            "socket_timeout": 30,
            "extractor_retries": 3,
            "noplaylist": True,
        }

        # Post-processor per audio
        if self.format.get() == "mp3":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": SETTINGS.get("audio_quality", "320"),
            }]
        elif self.format.get() == "wav":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "wav",
            }]
        elif self.format.get() == "flac":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "flac",
            }]

        # Limite velocità
        speed = SETTINGS.get("speed_limit", "0")
        if speed != "0":
            ydl_opts["ratelimit"] = int(speed) * 1024

        # FFmpeg path (solo Windows)
        if platform.system() == "Windows" and FFMPEG_PATH:
            ydl_opts["ffmpeg_location"] = os.path.dirname(FFMPEG_PATH)

        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([video["url"]])

    def _create_progress_hook(self, idx: int):
        """Crea un hook per il progresso del download."""
        def hook(d):
            if self.stop_requested:
                raise Exception("Download fermato dall'utente")
            if d.get("status") == "downloading":
                percent = 0.0
                if d.get("total_bytes"):
                    percent = d["downloaded_bytes"] / d["total_bytes"] * 100
                elif d.get("total_bytes_estimate"):
                    percent = d["downloaded_bytes"] / d["total_bytes_estimate"] * 100
                elif d.get("_percent_str"):
                    try:
                        percent = float(d["_percent_str"].strip().replace("%", ""))
                    except:
                        pass
                self.queue.put(("video_progress", (idx, percent)))
            elif d.get("status") == "finished":
                self.queue.put(("video_progress", (idx, 100.0)))
        return hook

    def _apply_id3_in_background(self, video: Dict, idx: int):
        """Applica i tag ID3 in un thread separato per non bloccare."""
        def apply():
            # Piccola attesa per sicurezza (assicura che il file sia stato scritto)
            time.sleep(1)
            try:
                # Costruisce il percorso del file dopo conversione
                base = safe_filename(video["title"])
                filepath = os.path.join(self.download_dir.get(), f"{base}.mp3")
                if not os.path.exists(filepath):
                    # Prova con prefisso numerico
                    base2 = safe_filename(f"{idx+1:03d}. {video['title']}")
                    filepath = os.path.join(self.download_dir.get(), f"{base2}.mp3")

                if os.path.exists(filepath):
                    # Cerca match Deezer
                    match = self.deezer_tagger.find_best_match(
                        video["title"],
                        video["uploader"],
                        video.get("duration")
                    )
                    if match:
                        cover = self.deezer_tagger.download_cover(match.get("cover_url", ""))
                        metadata = {
                            "title": match.get("title", ""),
                            "artist": match.get("artist", ""),
                            "album": match.get("album", ""),
                            "year": match.get("year", ""),
                            "genre": match.get("genre", ""),
                        }
                        if self.deezer_tagger.apply_id3_tags(filepath, metadata, cover):
                            self.queue.put(("id3_applied", idx))
                            return
                self.queue.put(("id3_failed", idx))
            except Exception as e:
                log(f"⚠️ ID3 error: {e}")
                self.queue.put(("id3_failed", idx))

        thread = threading.Thread(target=apply, daemon=True)
        thread.start()

    def _process_queue(self):
        """Elabora i messaggi dalla coda (chiamato periodicamente)."""
        try:
            while True:
                msg = self.queue.get_nowait()
                self._handle_message(msg)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

    def _handle_message(self, msg):
        """Gestisce un singolo messaggio dalla coda."""
        msg_type = msg[0]
        try:
            if msg_type == "videos_loaded":
                videos = msg[1]
                self.playlist_videos = videos
                total = len(videos)
                self.tree.delete(*self.tree.get_children())
                for i, v in enumerate(videos):
                    self.tree.insert(
                        "",
                        "end",
                        iid=str(i),
                        values=(
                            i+1,
                            v["title"],
                            format_duration(v.get("duration")),
                            v["uploader"],
                            "⏳ In attesa",
                            "0%"
                        )
                    )
                self.status_text.set(T("playlist_videos_found", total=total))
                self.overall_progress_text.set(f"0/{total} - 0%")
                self.btn_download.configure(state="normal")
                log(f"✅ Caricati {total} video")

            elif msg_type == "error":
                error = msg[1]
                self.status_text.set(T("playlist_error", error=error))
                self.btn_download.configure(state="disabled")
                messagebox.showerror(T("playlist_error"), error, parent=self)

            elif msg_type == "video_start":
                idx, title = msg[1]
                self.current_video.set(f"{idx+1}. {title}")
                self.tree.set(str(idx), T("playlist_column_status"), "📥 Download")
                self.tree.item(str(idx), tags=("downloading",))
                self.tree.see(str(idx))

            elif msg_type == "video_progress":
                idx, percent = msg[1]
                self.video_progress[idx] = percent
                self.tree.set(str(idx), T("playlist_column_progress"), f"{percent:.1f}%")

            elif msg_type == "video_done":
                idx = msg[1]
                self.tree.set(str(idx), T("playlist_column_status"), "✅ Completato")
                self.tree.set(str(idx), T("playlist_column_progress"), "100%")
                self.tree.item(str(idx), tags=("completed",))

            elif msg_type == "video_failed":
                idx = msg[1]
                self.tree.set(str(idx), T("playlist_column_status"), "❌ Fallito")
                self.tree.set(str(idx), T("playlist_column_progress"), "ERR")
                self.tree.item(str(idx), tags=("failed",))

            elif msg_type == "video_skipped":
                idx = msg[1]
                self.tree.set(str(idx), T("playlist_column_status"), "⏭️ Saltato")
                self.tree.set(str(idx), T("playlist_column_progress"), "Esistente")
                self.tree.item(str(idx), tags=("skipped",))

            elif msg_type == "id3_applied":
                idx = msg[1]
                current = self.tree.set(str(idx), T("playlist_column_status"))
                self.tree.set(str(idx), T("playlist_column_status"), current + " 🏷️")
                self.tree.item(str(idx), tags=("id3_applied",))

            elif msg_type == "id3_failed":
                idx = msg[1]
                current = self.tree.set(str(idx), T("playlist_column_status"))
                self.tree.set(str(idx), T("playlist_column_status"), current + " ⚠️")

            elif msg_type == "overall_progress":
                completed, failed, total = msg[1]
                percent = ((completed + failed) / total) * 100 if total else 0
                self.overall_progress_text.set(f"{completed}/{total} completati ({failed} falliti) - {percent:.1f}%")
                self.overall_progress_var.set(percent / 100)

            elif msg_type == "download_completed":
                completed, failed = msg[1]
                total = len(self.playlist_videos)
                self.downloading = False
                self.stop_requested = False
                self.btn_download.configure(state="normal")
                self.btn_stop.configure(state="disabled")
                if self.failed_indices:
                    self.btn_retry.configure(state="normal")
                self.status_text.set(T("playlist_completed"))
                self.current_video.set("")
                log(f"✅ Playlist completata: {completed}/{total} ok, {failed} falliti")
                messagebox.showinfo(
                    T("playlist_completed"),
                    T("playlist_download_completed", completed=completed, total=total, failed=failed),
                    parent=self
                )

            elif msg_type == "download_stopped":
                completed, failed = msg[1]
                total = len(self.playlist_videos)
                self.downloading = False
                self.stop_requested = False
                self.btn_download.configure(state="normal")
                self.btn_stop.configure(state="disabled")
                if self.failed_indices:
                    self.btn_retry.configure(state="normal")
                self.status_text.set(T("playlist_stopped"))
                self.current_video.set("")
                log(f"⏹️ Playlist fermata: {completed}/{total} ok, {failed} falliti")
                messagebox.showinfo(
                    T("playlist_stopped"),
                    T("playlist_download_stopped", completed=completed, total=total),
                    parent=self
                )

        except Exception as e:
            log(f"❌ Errore gestione messaggio {msg_type}: {e}")

    def _on_closing(self):
        """Gestisce la chiusura della finestra."""
        if self.downloading:
            if messagebox.askyesno(T("playlist_confirm_title"), T("playlist_confirm_close"), parent=self):
                self.stop_requested = True
                self.after(500, self.destroy)
        else:
            self.destroy()


# ---------------------- FUNZIONE DI APERTURA PER APP.PY ----------------------
def open_playlist_downloader(master, url: str = None):
    """
    Funzione chiamata da app.py per aprire il downloader playlist.
    Restituisce la finestra creata.
    """
    if hasattr(master, "playlist_window"):
        try:
            if master.playlist_window.winfo_exists():
                master.playlist_window.lift()
                master.playlist_window.focus_set()
                return master.playlist_window
        except:
            pass

    # Se url non fornito, prova a prenderlo dall'entry principale
    if not url and hasattr(master, "query"):
        url = master.query.get().strip()

    if not url:
        messagebox.showerror("Errore", "Inserisci un URL di playlist YouTube.", parent=master)
        return None

    # Controlla se è una playlist, altrimenti chiedi conferma
    if not is_playlist_url(url):
        if not messagebox.askyesno(
            T("playlist_prompt_title"),
            T("playlist_prompt_text"),
            parent=master
        ):
            return None

    try:
        master.playlist_window = PlaylistDownloader(master, url)
        return master.playlist_window
    except Exception as e:
        log(f"❌ Errore apertura playlist: {e}\n{traceback.format_exc()}")
        messagebox.showerror(T("playlist_error"), f"Impossibile aprire il downloader:\n{e}", parent=master)
        return None


# ---------------------- TEST STANDALONE ----------------------
if __name__ == "__main__":
    print("🎵 Playlist Downloader - Test Standalone")
    print("=" * 50)

    # Test utility
    test_urls = [
        "https://www.youtube.com/playlist?list=PLABC123",
        "https://www.youtube.com/watch?v=123&list=PLABC123",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    ]
    for url in test_urls:
        print(f"\nURL: {url}")
        print(f"  È playlist? {is_playlist_url(url)}")
        cleaned = clean_playlist_url(url)
        print(f"  Pulito: {cleaned}")

    # Test GUI
    try:
        ctk.set_appearance_mode(SETTINGS.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        class TestApp:
            def __init__(self):
                self.root = ctk.CTk()
                self.root.title("Test Playlist Downloader")
                self.root.geometry("400x200")
                self.query = ctk.StringVar()
                self.playlist_window = None

                frame = ctk.CTkFrame(self.root)
                frame.pack(pady=20, padx=20, fill="both", expand=True)

                ctk.CTkLabel(frame, text="Incolla URL playlist:", font=("Segoe UI", 14)).pack(pady=10)
                entry = ctk.CTkEntry(frame, textvariable=self.query, width=350)
                entry.pack(pady=10)
                ctk.CTkButton(
                    frame,
                    text="Apri Downloader",
                    command=self.open,
                    height=35
                ).pack(pady=20)

            def open(self):
                open_playlist_downloader(self, self.query.get())

            def run(self):
                self.root.mainloop()

        app = TestApp()
        app.run()
    except Exception as e:
        print(f"❌ Test GUI fallito: {e}")
        traceback.print_exc()
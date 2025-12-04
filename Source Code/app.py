#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA - 04/12/2025
MUSIC WAVVER 2.9.0
MADE IN ITALY 🇮🇹
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
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import subprocess
import io
from base64 import b64encode
import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
from tkinter.ttk import Treeview, Style
from yt_dlp import YoutubeDL
from PIL import Image, ImageTk
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TYER, TCON, APIC, error

# ---------------------- CONFIGURAZIONE CTK ----------------------
ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

# ---------------------- LOGGING ----------------------
LOG_FILE = "ytdownloader.log"
SETTINGS_FILE = "settings.json"
LANGUAGES_FILE = "languages.json"

try:
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.truncate(0)
except Exception:
    pass

PLAYLIST_LOG_FILE = "playlist_urls.log" 
playlist_logger = logging.getLogger('playlist_urls')
playlist_logger.setLevel(logging.INFO)
pl_handler = logging.FileHandler(PLAYLIST_LOG_FILE, mode='w', encoding='utf-8')
pl_handler.setFormatter(logging.Formatter("%(message)s"))
playlist_logger.addHandler(pl_handler)

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

def log(msg):
    print(msg)
    try:
        logging.info(msg)
    except Exception:
        pass
        
def log_playlist_url(url):
    playlist_logger.info(url)
    log(f"Tracciamento URL Playlist: {url}")

# ---------------------- CARICAMENTO LINGUE ----------------------
def load_languages():
    if not os.path.exists(LANGUAGES_FILE):
        error_msg = f"❌ ERRORE CRITICO: File delle lingue '{LANGUAGES_FILE}' non trovato!"
        log(error_msg)
        messagebox.showerror("Errore File Lingue", error_msg)
        sys.exit(1)
    
    try:
        with open(LANGUAGES_FILE, "r", encoding="utf-8") as f:
            languages = json.load(f)
        log("✅ File lingue caricato correttamente.")
        return languages
    except Exception as e:
        error_msg = f"❌ ERRORE nel caricamento del file delle lingue: {e}"
        log(error_msg)
        messagebox.showerror("Errore File Lingue", error_msg)
        sys.exit(1)

LANGUAGES = load_languages()

# ---------------------- DEFAULT SETTINGS ----------------------
DEFAULT_SETTINGS = {
    "download_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
    "theme": "system",
    "speed_limit": "0",
    "search_timeout": 30,
    "agreement_accepted": False,
    "language": "it",
    "last_update_check": "1970-01-01T00:00:00",
    "max_retries": 3,
    "retry_delay": 5,
    "write_id3": False  # Nuova impostazione per ID3 tag
}

# ---------------------- SETTINGS ----------------------
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                valid_settings = {k: v for k, v in s.items() if k in DEFAULT_SETTINGS}
                DEFAULT_SETTINGS.update(valid_settings)
        except Exception as e:
            log(f"⚠️ Errore leggendo settings.json: {e}")
    return DEFAULT_SETTINGS

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, indent=4)

SETTINGS = load_settings()

def T(key):
    lang = SETTINGS.get("language", "it")
    return LANGUAGES.get(lang, {}).get(key, LANGUAGES.get("it", {}).get(key, key))

# ---------------------- FUNZIONI ID3 DEEZER ----------------------
class DeezerID3Tagger:
    def __init__(self):
        self.api_base = "https://api.deezer.com"
        
    def clean_search_query(self, query):
        """Pulisce la query di ricerca rimuovendo parole comuni e parentesi"""
        # Rimuovi estensione file
        query = os.path.splitext(query)[0]
        
        # Pattern per rimuovere testo tra parentesi (incluse parentesi tonde e quadre)
        query = re.sub(r'[\[\(].*?[\]\)]', '', query)
        
        # Rimuovi parole comuni da YouTube
        common_terms = [
            'official', 'video', 'audio', 'lyric', 'lyrics', 'lyrical', 
            'hq', 'hd', '4k', '1080p', '720p', 'full', 'song', 'version',
            'oficial', 'vídeo', 'audio', 'letra', 'letras', 'kualitas',
            'official video', 'official audio', 'music video', 'mv', 'clip',
            'visualizer', 'visual', 'live', 'performance', 'remix', 'mix',
            'cover', 'original', 'extended', 'radio edit'
        ]
        
        # Crea pattern case-insensitive
        pattern = r'\b(' + '|'.join(re.escape(term) for term in common_terms) + r')\b'
        query = re.sub(pattern, '', query, flags=re.IGNORECASE)
        
        # Rimuovi spazi multipli e trim
        query = re.sub(r'\s+', ' ', query).strip()
        
        # Rimuovi caratteri speciali ma mantieni spazi e trattini
        query = re.sub(r'[^\w\s\-]', '', query)
        
        # Se la query è troppo corta dopo la pulizia, usa l'originale
        if len(query) < 3:
            query = os.path.splitext(query)[0]
            query = re.sub(r'[^\w\s\-]', ' ', query)
            query = re.sub(r'\s+', ' ', query).strip()
        
        log(f"🔍 Query pulita: '{query}'")
        return query
    
    def search_track(self, query, limit=5):
        """Cerca una traccia su Deezer"""
        try:
            # Pulisci la query prima della ricerca
            clean_query = self.clean_search_query(query)
            
            url = f"{self.api_base}/search"
            params = {"q": clean_query, "limit": limit}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            tracks = []
            for track in data.get("data", []):
                tracks.append({
                    "title": track.get("title", ""),
                    "artist": track.get("artist", {}).get("name", ""),
                    "album": track.get("album", {}).get("title", ""),
                    "year": track.get("release_date", "").split("-")[0] if track.get("release_date") else "",
                    "genre": track.get("genre", {}).get("name", "") if track.get("genre") else "",
                    "cover_url": track.get("album", {}).get("cover_medium", ""),
                    "track_number": track.get("track_position", ""),
                    "duration": track.get("duration", 0)
                })
            
            log(f"✅ Trovati {len(tracks)} risultati su Deezer per query: '{clean_query}'")
            return tracks
        except Exception as e:
            log(f"❌ Errore ricerca Deezer: {e}")
            return []
    
    def download_cover(self, url):
        """Scarica la copertina dall'URL"""
        try:
            if not url:
                return None
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.content
        except Exception as e:
            log(f"⚠️ Errore download copertina: {e}")
            return None
    
    def apply_id3_tags(self, filepath, metadata, cover_data=None):
        """Applica i tag ID3 al file MP3"""
        try:
            audio = MP3(filepath, ID3=ID3)
            
            # Crea tag ID3 se non esistono
            try:
                audio.add_tags()
            except error:
                pass
            
            # Titolo
            if metadata.get("title"):
                audio.tags.add(TIT2(encoding=3, text=metadata["title"]))
            
            # Artista
            if metadata.get("artist"):
                audio.tags.add(TPE1(encoding=3, text=metadata["artist"]))
            
            # Album
            if metadata.get("album"):
                audio.tags.add(TALB(encoding=3, text=metadata["album"]))
            
            # Anno
            if metadata.get("year"):
                audio.tags.add(TYER(encoding=3, text=metadata["year"]))
            
            # Genere
            if metadata.get("genre"):
                audio.tags.add(TCON(encoding=3, text=metadata["genre"]))
            
            # Copertina
            if cover_data:
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # 3 = front cover
                    desc='Cover',
                    data=cover_data
                ))
            
            audio.save()
            log(f"✅ Tag ID3 applicati a: {filepath}")
            return True
        except Exception as e:
            log(f"❌ Errore applicazione tag ID3: {e}")
            return False

# ---------------------- FINESTRA METADATI DEEZER ----------------------
class DeezerMetadataWindow(ctk.CTkToplevel):
    def __init__(self, parent, filename, filepath, deezer_tagger):
        super().__init__(parent)
        self.title(T("id3_window_title"))
        self.geometry("700x650")
        self.transient(parent)
        
        # NON impostare grab_set qui - causerebbe errore su Linux
        self.withdraw()  # Nascondi temporaneamente come fanno le altre finestre
        
        self.filename = filename
        self.filepath = filepath
        self.deezer_tagger = deezer_tagger
        self.selected_metadata = None
        self.cover_image = None
        self.cover_data = None
        
        # Centra la finestra
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.winfo_screenheight() // 2) - (650 // 2)
        self.geometry(f"700x650+{x}+{y}")
        
        # Icona
        try:
            if os.path.exists("logo.ico"):
                self.after(250, lambda: self.iconbitmap("logo.ico"))
        except Exception:
            pass
        
        self._build_ui()
        self._search_metadata()
        
        # Mostra la finestra e imposta il grab DOPO che è pronta
        self.after(100, self._show_window)
    
    def _show_window(self):
        """Mostra la finestra e imposta il grab dopo che è pronta"""
        self.deiconify()  # Rendi visibile
        try:
            self.grab_set()  # Ora può impostare il grab
        except Exception as e:
            log(f"⚠️ Grab fallito su DeezerMetadataWindow: {e}")
            # Su Linux a volte grab_set fallisce, ma possiamo continuare comunque
    
    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Titolo
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        title_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(title_frame, text=T("id3_question").format(file=self.filename), 
                    font=("Segoe UI", 16, "bold"), wraplength=600).grid(row=0, column=0, sticky="w")
        
        # Frame principale
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Lista risultati (sinistra)
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(10, 5), pady=10)
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(left_frame, text=T("id3_search_results"), font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))
        
        # Treeview per risultati
        tree_frame = ctk.CTkFrame(left_frame)
        tree_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)
        
        style = Style()
        style.configure("Results.Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            borderwidth=0,
            highlightthickness=0,
            rowheight=25
        )
        style.configure("Results.Treeview.Heading",
            background="#f0f0f0",
            foreground="black",
            relief="flat"
        )
        
        self.tree = Treeview(tree_frame, columns=("Title", "Artist", "Album"), 
                           show="headings", style="Results.Treeview", height=8)
        self.tree.column("Title", width=150, anchor="w")
        self.tree.column("Artist", width=100, anchor="w")
        self.tree.column("Album", width=100, anchor="w")
        
        self.tree.heading("Title", text=T("id3_title"))
        self.tree.heading("Artist", text=T("id3_artist"))
        self.tree.heading("Album", text=T("id3_album"))
        
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.tree.bind("<<TreeviewSelect>>", self._on_select_result)
        
        # Scrollbar per treeview
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        # Dettagli (destra)
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 10), pady=10)
        right_frame.grid_columnconfigure(1, weight=1)
        
        # Titolo dettagli
        ctk.CTkLabel(right_frame, text=T("id3_selected_details"), 
                    font=("Segoe UI", 14, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=(10, 15))
        
        # Copertina
        self.cover_label = ctk.CTkLabel(right_frame, text=T("id3_no_cover"), 
                                       width=150, height=150, corner_radius=8)
        self.cover_label.grid(row=1, column=0, rowspan=4, padx=(10, 20), pady=(0, 20), sticky="n")
        
        # Campi metadati
        row = 1
        labels = [
            (T("id3_title"), "title"),
            (T("id3_artist"), "artist"),
            (T("id3_album"), "album"),
            (T("id3_year"), "year"),
            (T("id3_genre"), "genre"),
            (T("id3_track_num"), "track_number"),
            (T("id3_duration"), "duration_formatted")
        ]
        
        self.entry_vars = {}
        for label_text, key in labels:
            ctk.CTkLabel(right_frame, text=label_text + ":", 
                        font=("Segoe UI", 11)).grid(row=row, column=1, sticky="w", padx=(0, 10), pady=2)
            
            var = ctk.StringVar()
            entry = ctk.CTkEntry(right_frame, textvariable=var, width=250)
            entry.grid(row=row, column=2, sticky="w", pady=2)
            
            self.entry_vars[key] = var
            row += 1
        
        # Pulsanti
        button_frame = ctk.CTkFrame(self, fg_color="transparent")
        button_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 20))
        button_frame.grid_columnconfigure(0, weight=1)
        button_frame.grid_columnconfigure(1, weight=1)
        button_frame.grid_columnconfigure(2, weight=1)
        
        self.btn_apply = ctk.CTkButton(button_frame, text=T("id3_apply"), 
                                      command=self._apply_tags, state="disabled",
                                      fg_color="#28a745", hover_color="#218838")
        self.btn_apply.grid(row=0, column=0, padx=10)
        
        self.btn_cancel = ctk.CTkButton(button_frame, text=T("id3_cancel"), 
                                       command=self.destroy)
        self.btn_cancel.grid(row=0, column=1, padx=10)
        
        self.btn_manual = ctk.CTkButton(button_frame, text=T("id3_manual_edit"), 
                                       command=self._enable_editing)
        self.btn_manual.grid(row=0, column=2, padx=10)
        
        # Stato
        self.status_label = ctk.CTkLabel(self, text=T("id3_searching"), 
                                        font=("Segoe UI", 11, "italic"))
        self.status_label.grid(row=3, column=0, sticky="w", padx=20, pady=(0, 10))
    
    def _search_metadata(self):
        """Avvia ricerca metadati in thread separato"""
        def search_thread():
            # Usa il nome del file per la ricerca
            search_query = self.filename
            
            results = self.deezer_tagger.search_track(search_query)
            
            self.after(0, lambda: self._update_results(results))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def _update_results(self, results):
        """Aggiorna la lista dei risultati"""
        self.tree.delete(*self.tree.get_children())
        
        if not results:
            self.status_label.configure(text=T("id3_no_results"))
            return
        
        self.results = results
        for i, track in enumerate(results):
            duration_sec = track.get("duration", 0)
            duration_str = f"{duration_sec//60}:{duration_sec%60:02d}" if duration_sec else ""
            
            self.tree.insert("", "end", iid=i, values=(
                track.get("title", "")[:50],
                track.get("artist", "")[:30],
                track.get("album", "")[:30]
            ))
        
        self.status_label.configure(text=T("id3_select_track"))
    
    def _on_select_result(self, event):
        """Quando viene selezionato un risultato"""
        selection = self.tree.selection()
        if not selection:
            return
        
        idx = int(selection[0])
        track = self.results[idx]
        self.selected_metadata = track
        
        # Aggiorna campi
        self.entry_vars["title"].set(track.get("title", ""))
        self.entry_vars["artist"].set(track.get("artist", ""))
        self.entry_vars["album"].set(track.get("album", ""))
        self.entry_vars["year"].set(track.get("year", ""))
        self.entry_vars["genre"].set(track.get("genre", ""))
        self.entry_vars["track_number"].set(str(track.get("track_number", "")))
        
        # Formatta durata
        duration = track.get("duration", 0)
        if duration:
            minutes = duration // 60
            seconds = duration % 60
            self.entry_vars["duration_formatted"].set(f"{minutes}:{seconds:02d}")
        else:
            self.entry_vars["duration_formatted"].set("")
        
        # Scarica e mostra copertina
        self._load_cover(track.get("cover_url", ""))
        
        # Abilita pulsante applica
        self.btn_apply.configure(state="normal")
    
    def _load_cover(self, url):
        """Carica la copertina dall'URL"""
        def load_thread():
            cover_data = self.deezer_tagger.download_cover(url)
            self.cover_data = cover_data
            
            if cover_data:
                try:
                    image = Image.open(io.BytesIO(cover_data))
                    image.thumbnail((150, 150))
                    
                    if ctk.get_appearance_mode() == "Dark":
                        bg_color = "#2b2b2b"
                    else:
                        bg_color = "#f0f0f0"
                    
                    # Crea immagine con sfondo
                    bg = Image.new("RGB", (150, 150), bg_color)
                    x = (150 - image.width) // 2
                    y = (150 - image.height) // 2
                    bg.paste(image, (x, y))
                    
                    self.cover_image = ImageTk.PhotoImage(bg)
                    self.after(0, lambda: self.cover_label.configure(
                        image=self.cover_image, text=""
                    ))
                except Exception as e:
                    log(f"⚠️ Errore caricamento immagine: {e}")
                    self.after(0, lambda: self.cover_label.configure(
                        text=T("id3_cover_error")
                    ))
        
        threading.Thread(target=load_thread, daemon=True).start()
    
    def _enable_editing(self):
        """Abilita la modifica manuale di tutti i campi"""
        for entry_var in self.entry_vars.values():
            # I CTkEntry sono già editabili di default
            pass
        
        if not self.selected_metadata:
            # Crea metadata vuoto se nessuno selezionato
            self.selected_metadata = {
                "title": "",
                "artist": "",
                "album": "",
                "year": "",
                "genre": "",
                "track_number": "",
                "duration": 0
            }
        
        self.btn_apply.configure(state="normal")
        self.status_label.configure(text=T("id3_manual_mode"))
    
    def _apply_tags(self):
        """Applica i tag ID3 al file"""
        # Raccogli dati dai campi
        metadata = {
            "title": self.entry_vars["title"].get().strip(),
            "artist": self.entry_vars["artist"].get().strip(),
            "album": self.entry_vars["album"].get().strip(),
            "year": self.entry_vars["year"].get().strip(),
            "genre": self.entry_vars["genre"].get().strip(),
            "track_number": self.entry_vars["track_number"].get().strip()
        }
        
        # Verifica che almeno titolo o artista siano presenti
        if not metadata["title"] and not metadata["artist"]:
            messagebox.showwarning(T("id3_warning_title"), 
                                 T("id3_warning_empty"), parent=self)
            return
        
        # Applica tag
        success = self.deezer_tagger.apply_id3_tags(
            self.filepath, metadata, self.cover_data
        )
        
        if success:
            messagebox.showinfo(T("id3_success_title"), 
                              T("id3_success_msg"), parent=self)
            self.destroy()
        else:
            messagebox.showerror(T("id3_error_title"), 
                               T("id3_error_msg"), parent=self)

# ---------------------- CONTROLLO FFMPEG ----------------------
def show_ffmpeg_missing_error():
    """Mostra finestra di errore per FFmpeg mancante"""
    root = ctk.CTk()
    root.title(T("ffmpeg_missing_title"))
    root.geometry("600x400")
    root.resizable(False, False)
    
    # Centra la finestra
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (600 // 2)
    y = (root.winfo_screenheight() // 2) - (400 // 2)
    root.geometry(f"600x400+{x}+{y}")
    
    # Imposta icona
    try:
        if os.path.exists("logo.ico"):
            root.iconbitmap("logo.ico")
    except Exception:
        pass
    
    # Contenuto
    frame = ctk.CTkFrame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Icona errore
    ctk.CTkLabel(frame, text="❌", font=("Segoe UI", 48)).pack(pady=(20, 10))
    
    # Titolo
    ctk.CTkLabel(frame, text=T("ffmpeg_missing_title"), font=("Segoe UI", 20, "bold")).pack(pady=(0, 20))
    
    # Istruzioni
    if platform.system().lower() == "windows":
        instructions = T("ffmpeg_missing_windows")
    else:
        instructions = T("ffmpeg_missing_linux")
    
    text_widget = ctk.CTkTextbox(frame, wrap="word", height=200, font=("Consolas", 12))
    text_widget.pack(fill="both", expand=True, padx=10, pady=10)
    text_widget.insert("1.0", instructions)
    text_widget.configure(state="disabled")
    
    # Pulsante chiudi
    ctk.CTkButton(frame, text=T("ffmpeg_close_app"), command=sys.exit, 
                 fg_color="#dc3545", hover_color="#c82333", height=40).pack(pady=20)
    
    root.mainloop()

def detect_ffmpeg():
    """Controlla se FFmpeg è disponibile, altrimenti mostra finestra di errore"""
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    sys_os = platform.system().lower()
    
    # Cerca FFmpeg localmente
    candidate = os.path.join(base, "ffmpeg", "win", "ffmpeg.exe") if "win" in sys_os else os.path.join(base, "ffmpeg", "linux", "ffmpeg")

    if not os.path.exists(candidate):
        log("⚠️ ffmpeg locale non trovato, controllo presenza globale...")
        found = shutil.which("ffmpeg")
        if found:
            log(f"✅ ffmpeg globale trovato: {found}")
            return found
        else:
            # FFMPEG NON TROVATO - MOSTRA FINESTRA DI ERRORE
            show_ffmpeg_missing_error()
            sys.exit(1)
    
    os.environ["PATH"] = os.path.dirname(candidate) + os.pathsep + os.environ.get("PATH", "")
    log(f"FFmpeg path rilevato (locale): {candidate}")
    return candidate

FFMPEG_PATH = detect_ffmpeg()

# ---------------------- ACCORDO LEGALE ----------------------
def show_agreement():
    root = ctk.CTk()
    root.withdraw()
    accept = messagebox.askyesno(T("agreement_title"), T("agreement_text"))
    root.destroy()
    if accept:
        SETTINGS["agreement_accepted"] = True
        save_settings()
        return True
    else:
        messagebox.showinfo(T("agreement_title"), T("agreement_close"))
        return False

# ---------------------- UTILITY ----------------------
def is_playlist(url):
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    if "playlist" in parsed.path:
        return True
    if "list" in query_params:
        return True
    return False

def extract_video_id(url):
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    if "v" in query_params:
        return query_params["v"][0]
    match = re.search(r'(youtu\.be\/|v=)([a-zA-Z0-9_-]{11})', url)
    if match:
        return match.group(2)
    return None

# ---------------------- RICERCA ----------------------
def _yt_search_worker(query, max_results, result_queue):
    log(f"🔎 Avvio ricerca - Query: '{query}', Max risultati: {max_results}")
    max_retries = SETTINGS.get("max_retries", 3)
    retry_delay = SETTINGS.get("retry_delay", 5)
    
    for attempt in range(max_retries):
        try:
            is_url = query.startswith("http")
            
            opts = {
                "quiet": True, 
                "extract_flat": True, 
                "skip_download": True, 
                "default_search": "ytsearch",
                "socket_timeout": 30,
                "extractor_retries": 3
            }
            if is_url:
                opts["default_search"] = "auto"
            
            search_query = f"ytsearch{max_results}:{query}" if not is_url else query

            with YoutubeDL(opts) as ydl:
                info = ydl.extract_info(search_query, download=False)
                
                if not is_url:
                    results = []
                    for e in info.get("entries", []):
                        if e.get('id'):
                            results.append({
                                "title": e.get("title", "Sconosciuto"),
                                "url": f"https://www.youtube.com/watch?v={e['id']}",
                                "duration": e.get("duration", "N/D"),
                                "uploader": e.get("uploader", "Sconosciuto")
                            })
                    log(f"✅ Ricerca completata. Trovati {len(results)} risultati.")
                    result_queue.put(("ok", results))
                    return
                elif info.get("id"):
                    results = [{
                        "title": info.get("title", "Sconosciuto"),
                        "url": info.get("webpage_url", query),
                        "duration": info.get("duration", "N/D"),
                        "uploader": info.get("uploader", "Sconosciuto")
                    }]
                    log("✅ Info URL singolo estratta.")
                    result_queue.put(("ok", results))
                    return
                else:
                    log("⚠️ Nessun risultato trovato per l'URL.")
                    result_queue.put(("ok", []))
                    return

        except Exception as ex:
            log(f"❌ Tentativo {attempt + 1}/{max_retries} fallito: {ex}")
            if attempt < max_retries - 1:
                log(f"🔄 Ritento tra {retry_delay} secondi...")
                time.sleep(retry_delay)
            else:
                log(f"❌ Errore durante la ricerca/estrazione info: {ex}")
                result_queue.put(("err", str(ex)))

def search_youtube(query, max_results=10, timeout_seconds=30):
    rq = queue.Queue()
    video_id = extract_video_id(query)
    
    if video_id and query.startswith("http"):
        query_to_search = f"https://www.youtube.com/watch?v={video_id}"
    else:
        query_to_search = query
    
    t = threading.Thread(target=_yt_search_worker, args=(query_to_search, max_results, rq), daemon=True)
    t.start()
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            typ, payload = rq.get_nowait()
            return payload if typ == "ok" else (_ for _ in ()).throw(RuntimeError(payload))
        except queue.Empty:
            time.sleep(0.05)
    log(f"❌ Ricerca scaduta dopo {timeout_seconds} secondi.")
    raise TimeoutError("Ricerca scaduta")

# ---------------------- DOWNLOAD SINGOLO ----------------------
LAST_FILE = None
def download_with_yt_dlp(url, fmt, out_dir, speed_limit, progress_cb=None):
    global LAST_FILE
    
    max_retries = SETTINGS.get("max_retries", 3)
    retry_delay = SETTINGS.get("retry_delay", 5)
    
    outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")
    
    log(f"⬇️ Avvio download singolo - URL: {url}, Formato: {fmt}, Cartella: {out_dir}")

    def hook(d):
        if d["status"] == "downloading":
            if d.get("total_bytes_estimate") or d.get("total_bytes"):
                total = d.get("total_bytes_estimate") or d.get("total_bytes")
                downloaded = d.get("downloaded_bytes", 0)
                perc = downloaded / total * 100
                if progress_cb:
                    progress_cb(perc)
        elif d["status"] == "finished":
            if progress_cb:
                progress_cb(100)

    for attempt in range(max_retries):
        try:
            postprocessors = [
                {"key":"FFmpegExtractAudio","preferredcodec": fmt,"preferredquality": "320"}
            ]
            
            ydl_opts = {
                "outtmpl": outtmpl,
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
                "ffmpeg_location": os.path.dirname(FFMPEG_PATH),
                "postprocessors": postprocessors,
                "progress_hooks": [hook],
                "socket_timeout": 30,
                "extractor_retries": 3
            }
            if speed_limit != "0":
                ydl_opts["ratelimit"] = speed_limit
                
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                LAST_FILE = ydl.prepare_filename(info).rsplit(".",1)[0] + f".{fmt}"
            
            log(f"✅ Download singolo completato. File salvato in: {LAST_FILE}")
            return True
            
        except Exception as e:
            log(f"❌ Tentativo {attempt + 1}/{max_retries} fallito: {e}")
            if attempt < max_retries - 1:
                log(f"🔄 Ritento download tra {retry_delay} secondi...")
                time.sleep(retry_delay)
            else:
                log(f"❌ Errore critico durante il download singolo: {e}")
                raise e

# ---------------------- PLAYLIST DOWNLOADER ----------------------
class PlaylistDownloader(ctk.CTkToplevel):
    def __init__(self, master, url):
        super().__init__(master)
        self.withdraw()  # Nascondi temporaneamente la finestra
        
        self.title(T("playlist_title"))
        self.geometry("800x600")
        self.transient(master)
        
        self._set_icon()

        self.playlist_url = url
        self.playlist_videos = []
        self.downloading = False
        self.current_video_index = 0
        self.completed_count = 0
        
        self.download_dir = ctk.StringVar(value=SETTINGS["download_dir"])
        self.format = ctk.StringVar(value="mp3")  # MP3 come predefinito
        self.status = ctk.StringVar(value=T("playlist_status_fetching"))
        self.overall_progress_text = ctk.StringVar(value="")
        self.overall_progress_value = ctk.DoubleVar(value=0)

        log(f"🆕 Avvio PlaylistDownloader per URL: {url}")

        self._build_ui()
        open(PLAYLIST_LOG_FILE, 'w').close()
        
        # Mostra la finestra e imposta il grab dopo che è pronta
        self.after(100, self._show_window)
        
        threading.Thread(target=self._search_playlist_thread, daemon=True).start()
        self.after(100, self._loop)

    def _show_window(self):
        """Mostra la finestra e imposta il grab"""
        self.deiconify()  # Rendi visibile
        try:
            self.grab_set()   # Ora puoi impostare il grab
        except Exception as e:
            log(f"⚠️ Grab fallito: {e}")

    def _set_icon(self):
        try:
            if os.path.exists("logo.ico"):
                self.after(250, lambda: self.iconbitmap("logo.ico"))
        except Exception:
            pass

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(self, text=T("playlist_select_dir"), font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w", pady=(10, 5), padx=12)
        
        dir_frame = ctk.CTkFrame(self)
        dir_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        dir_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(dir_frame, textvariable=self.download_dir, wraplength=550).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        ctk.CTkButton(dir_frame, text=T("change_folder"), command=self.change_dir, width=80).grid(row=0, column=1, padx=10, pady=8)

        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self._configure_treeview_style()
        
        cols = ("#", "Titolo", "Durata", "Uploader")
        self.tree = Treeview(tree_frame, columns=cols, show="headings", height=15)
        self.tree.column("#", width=40, anchor="center")
        self.tree.column("Titolo", width=350, anchor="w")
        self.tree.column("Durata", width=80, anchor="center")
        self.tree.column("Uploader", width=150, anchor="w")
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)

        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))
        
        ctk.CTkLabel(controls_frame, text=T("format_label")).pack(side="left", padx=(10, 5))
        ctk.CTkOptionMenu(controls_frame, variable=self.format, values=["wav", "mp3", "flac"]).pack(side="left", padx=5)
        
        self.btn_download = ctk.CTkButton(controls_frame, text=T("playlist_download_btn"), 
                                         command=self._start_download, state="disabled")
        self.btn_download.pack(side="right", padx=10)

        ctk.CTkLabel(self, textvariable=self.overall_progress_text, font=("Segoe UI", 12)).grid(row=4, column=0, sticky="w", padx=12)
        self.progress_bar = ctk.CTkProgressBar(self, variable=self.overall_progress_value)
        self.progress_bar.grid(row=5, column=0, sticky="ew", padx=12, pady=(5, 5))
        ctk.CTkLabel(self, textvariable=self.status).grid(row=6, column=0, sticky="w", padx=12, pady=(0, 10))

    def change_dir(self):
        d = filedialog.askdirectory(initialdir=self.download_dir.get(), title=T("select_download_folder"))
        if d:
            self.download_dir.set(d)
            log(f"📁 Cartella download playlist aggiornata a: {d}")

    def _configure_treeview_style(self):
        style = Style()
        style.configure("Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            borderwidth=0,
            highlightthickness=0
        )
        style.configure("Treeview.Heading",
            background="#f0f0f0",
            foreground="black",
            relief="flat"
        )
        style.map("Treeview.Heading",
            background=[('active', '#e0e0e0')]
        )

    def _search_playlist_thread(self):
        try:
            log(f"🔎 Avvio ricerca video in playlist: {self.playlist_url}")
            ydl_opts = {
                "quiet": True,
                "extract_flat": True,
                "skip_download": True,
                "socket_timeout": 30
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.playlist_url, download=False)
            
            videos = []
            for entry in info.get("entries", []):
                if entry and entry.get("id"):
                    url = f"https://www.youtube.com/watch?v={entry['id']}"
                    log_playlist_url(url)
                    videos.append({
                        "title": entry.get("title", "Titolo Sconosciuto"),
                        "url": url,
                        "duration": entry.get("duration_string", "N/D"),
                        "uploader": entry.get("channel", "Sconosciuto")
                    })

            self.playlist_videos = videos
            self.master.queue.put(("playlist_videos_loaded", len(videos)))
            
            if not self.playlist_videos:
                self.master.queue.put(("playlist_error", T("playlist_error_no_videos")))
                return

        except Exception as e:
            error_msg = str(e)
            # Ignora l'errore specifico ['maximum'] non supportato
            if "'maximum'" in error_msg and "are not supported arguments" in error_msg:
                log(f"⚠️ Errore yt-dlp ignorato: {error_msg}")
                # Continua comunque, cerca di recuperare almeno alcuni video
                self.master.queue.put(("playlist_videos_loaded", 0))
                return
            
            log(f"❌ Errore critico nel recupero playlist: {e}")
            self.master.queue.put(("playlist_error", str(e)))

    def _start_download(self):
        if self.downloading:
            return

        if not self.playlist_videos:
            messagebox.showerror("Errore", "Nessun video trovato nella playlist", parent=self)
            return

        self.downloading = True
        self.current_video_index = 0
        self.completed_count = 0
        self.btn_download.configure(state="disabled")
        
        log(f"⬇️ Avvio download playlist. {len(self.playlist_videos)} video da scaricare.")
        threading.Thread(target=self._download_playlist_thread, daemon=True).start()

    def _download_single_video_worker(self, video_index):
        video = self.playlist_videos[video_index]
        video_number = video_index + 1
        url = video["url"]
        title = video["title"]
        download_directory = self.download_dir.get()

        log(f"--- Avvio download {video_number}/{len(self.playlist_videos)}: '{title}' ---")
        
        self.master.queue.put(("playlist_progress_update", (video_index, "start")))

        outtmpl = os.path.join(download_directory, f"{video_number}. %(title)s.%(ext)s")
        
        postprocessors = [
            {"key":"FFmpegExtractAudio","preferredcodec": self.format.get(),"preferredquality": "320"}
        ]

        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "ffmpeg_location": os.path.dirname(FFMPEG_PATH),
            "socket_timeout": 30,
            "extractor_retries": 3
        }

        ydl_opts["postprocessors"] = postprocessors
        
        speed_limit = SETTINGS["speed_limit"]
        if speed_limit != "0":
            ydl_opts["ratelimit"] = speed_limit

        max_retries = SETTINGS.get("max_retries", 3)
        retry_delay = SETTINGS.get("retry_delay", 5)
        
        for attempt in range(max_retries):
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    ydl.extract_info(url, download=True)
                log(f"--- ✅ Download {video_number} completato: {title} ---")
                return True

            except Exception as e:
                log(f"--- ❌ Tentativo {attempt + 1}/{max_retries} fallito per {title}: {e} ---")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    return False

    def _download_playlist_thread(self):
        total_videos = len(self.playlist_videos)
        self.completed_count = 0
        
        log(f"Inizio download playlist verso: {self.download_dir.get()}")

        for i in range(total_videos):
            try:
                video_success = self._download_single_video_worker(i)
                
                if video_success:
                    self.completed_count += 1
                    self.master.queue.put(("playlist_progress_update", (i, "done")))
                else:
                    self.master.queue.put(("playlist_progress_update", (i, "failed")))
                    log(f"⚠️ Saltato video {i+1} a causa di errori")

            except Exception as e:
                log(f"❌ Errore imprevisto nel video {i+1}: {e}")
                self.master.queue.put(("playlist_progress_update", (i, "failed")))

            self.master.queue.put(("playlist_overall_progress", (i + 1, total_videos, self.completed_count)))
            time.sleep(0.5)

        log(f"✅ Download playlist completato. {self.completed_count}/{total_videos} video scaricati con successo.")
        self.master.queue.put(("playlist_done", self.completed_count))

    def _loop(self):
        try:
            while True:
                typ, payload = self.master.queue.get_nowait()
                
                if typ == "playlist_videos_loaded":
                    video_count = payload
                    self.tree.delete(*self.tree.get_children())
                    
                    if video_count > 0:
                        for i, video in enumerate(self.playlist_videos):
                            self.tree.insert("", "end", iid=i, values=(i+1, video["title"], video["duration"], video["uploader"]))
                        
                        self.status.set(f"Trovati {video_count} video. Pronto per il download.")
                        self.overall_progress_text.set(f"0/{video_count} video scaricati.")
                        self.btn_download.configure(state="normal")
                        self.progress_bar.configure(maximum=video_count)
                        log(f"✅ Trovati {video_count} video nella playlist.")
                    else:
                        self.status.set("Playlist recuperata ma nessun video trovato o formato non supportato.")
                        self.btn_download.configure(state="disabled")
                
                elif typ == "playlist_progress_update":
                    video_index, status = payload
                    try:
                        iid = str(video_index)
                        tags_to_remove = ('downloading_tag', 'done_tag', 'failed_tag')
                        current_tags = list(self.tree.item(iid, 'tags'))
                        new_tags = [t for t in current_tags if t not in tags_to_remove]
                        
                        if status == "start":
                            new_tags.append('downloading_tag')
                        elif status == "done":
                            new_tags.append('done_tag')
                        elif status == "failed":
                            new_tags.append('failed_tag')
                            
                        self.tree.item(iid, tags=new_tags)
                    except Exception as e:
                        log(f"Errore aggiornamento tag treeview: {e}")

                elif typ == "playlist_overall_progress":
                    current_idx_processed, total, completed_count = payload
                    self.overall_progress_value.set(current_idx_processed)
                    self.overall_progress_text.set(f"{completed_count}/{total} video scaricati (processato: {current_idx_processed}/{total})")
                    
                    if self.downloading and current_idx_processed <= total:
                         self.status.set(T("playlist_status_downloading").format(
                             current=current_idx_processed, 
                             total=total
                         ))

                elif typ == "playlist_done":
                    log("✅ Download playlist completato.")
                    self.status.set(T("playlist_status_complete"))
                    self.overall_progress_text.set(f"{payload}/{len(self.playlist_videos)} video scaricati con successo.")
                    self.btn_download.configure(state="normal")
                    self.downloading = False
                    
                    messagebox.showinfo(T("playlist_status_complete"), T("playlist_status_complete"), parent=self)
                    self.destroy()
                
                elif typ == "playlist_error":
                    error_msg = payload
                    log(f"❌ Errore playlist: {error_msg}")
                    self.btn_download.configure(state="disabled")
                    
                    # Se è l'errore ['maximum'], mostra un messaggio più soft
                    if "'maximum'" in error_msg and "are not supported arguments" in error_msg:
                        self.status.set("Playlist trovata ma con formato non completamente supportato.")
                        messagebox.showwarning("Attenzione", 
                            "La playlist è stata trovata ma potrebbe non essere completamente compatibile.\n"
                            "Alcune informazioni potrebbero mancare. Puoi comunque provare a scaricare i video.",
                            parent=self)
                    else:
                        self.status.set("Errore nel recupero della playlist")
                        messagebox.showerror("Errore Playlist", error_msg, parent=self)
                
                else:
                    self.master.queue.put_nowait((typ, payload))
        except queue.Empty:
            pass
        
        self.after(100, self._loop)

# ---------------------- GUI PRINCIPALE ----------------------
class YTDownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Il Mangia's MUSIC WAVVER - V.2.9.0") 
        self.geometry("960x620")
        
        self._set_icon()
        self._set_logo()

        self.queue = queue.Queue()
        self.results = []
        self.downloading = False
        self.query = ctk.StringVar()
        self.format = ctk.StringVar(value="mp3")  # MP3 come predefinito
        self.status = ctk.StringVar(value=T("ready"))
        self.search_max = ctk.IntVar(value=10)
        self.deezer_tagger = DeezerID3Tagger()
        
        log(f"🚀 GUI avviata. Versione: MUSIC WAVVER 2.9.0")

        self._build_ui()
        self.after(150, self._loop)
        log("🟢 Ciclo eventi avviato")
        
        self.after(500, self.check_for_updates)

    def _set_icon(self):
        try:
            if os.path.exists("logo.ico"):
                self.after(250, lambda: self.iconbitmap("logo.ico"))
        except Exception:
            pass

    def _set_logo(self):
        self.logo_image = None
        try:
            if os.path.exists("logo.png"):
                self.logo_image = ctk.CTkImage(
                    light_image=Image.open("logo.png"),
                    dark_image=Image.open("logo.png"),
                    size=(32, 32)
                )
        except Exception:
            pass

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        top_frame = ctk.CTkFrame(self)
        top_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=12)
        top_frame.grid_columnconfigure(0, weight=1)
        
        title_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="w", padx=10, pady=10)
        
        if self.logo_image:
            ctk.CTkLabel(title_frame, image=self.logo_image, text="").pack(side="left", padx=(0, 10))
        
        ctk.CTkLabel(title_frame, text=T("welcome"), font=("Segoe UI", 20, "bold")).pack(side="left")
        
        button_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        button_frame.grid(row=0, column=1, sticky="e", padx=10, pady=10)
        
        ctk.CTkButton(button_frame, text=T("open_playlist_log"), command=self.open_playlist_log, width=120).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text=T("open_log"), command=self.open_log, width=80).pack(side="right", padx=(5, 0))
        ctk.CTkButton(button_frame, text=T("settings"), command=self.open_settings, width=80).pack(side="right", padx=(5, 0))

        search_frame = ctk.CTkFrame(self)
        search_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 10))
        search_frame.grid_columnconfigure(0, weight=1)
        
        self.entry = ctk.CTkEntry(search_frame, textvariable=self.query, placeholder_text="Inserisci URL YouTube o termine di ricerca...")
        self.entry.grid(row=0, column=0, sticky="ew", padx=(10, 5), pady=10)
        self.entry.bind("<Return>", lambda e: self.on_search())
        
        self.btn_search = ctk.CTkButton(search_frame, text=T("search_btn"), command=self.on_search, width=120)
        self.btn_search.grid(row=0, column=1, padx=(5, 10), pady=10)

        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self._configure_treeview_style()
        
        cols = ("Titolo", "Uploader", "Durata")
        self.tree = Treeview(tree_frame, columns=cols, show="headings", height=14)
        
        self.tree.tag_configure('downloading_tag', background='#3B8ED0', foreground='white')
        
        self.tree.column("Titolo", width=400, anchor="w")
        self.tree.column("Uploader", width=150, anchor="w")
        self.tree.column("Durata", width=80, anchor="center")

        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.tree.bind("<Double-1>", lambda e: self.on_download())

        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=3, column=0, sticky="ew", padx=12, pady=(0, 10))
        
        ctk.CTkLabel(controls_frame, text=T("format_label")).pack(side="left", padx=(10, 5))
        ctk.CTkOptionMenu(controls_frame, variable=self.format, values=["wav", "mp3", "flac"]).pack(side="left", padx=5)
        
        self.btn_download = ctk.CTkButton(controls_frame, text=T("download_btn"), command=self.on_download, 
                                         fg_color="#28a745", hover_color="#218838")
        self.btn_download.pack(side="left", padx=20)
        
        self.btn_play = ctk.CTkButton(controls_frame, text=T("play_btn"), command=self.play_file, state="disabled")
        self.btn_play.pack(side="left", padx=5)

        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 12))
        progress_frame.grid_columnconfigure(0, weight=1)
        
        self.progress = ctk.CTkProgressBar(progress_frame)
        self.progress.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        ctk.CTkLabel(progress_frame, textvariable=self.status).grid(row=0, column=1, padx=(10, 10), pady=10)

    def _configure_treeview_style(self):
        style = Style()
        style.configure("Treeview",
            background="white",
            foreground="black",
            fieldbackground="white",
            borderwidth=0,
            highlightthickness=0,
            rowheight=25
        )
        style.configure("Treeview.Heading",
            background="#f0f0f0",
            foreground="black",
            relief="flat",
            font=('Segoe UI', 10, 'bold')
        )
        style.map("Treeview.Heading",
            background=[('active', '#e0e0e0')]
        )
        style.map("Treeview",
            background=[('selected', '#0078d7')],
            foreground=[('selected', 'white')]
        )

    def lock_ui(self, state: bool):
        s = "disabled" if state else "normal"
        for b in [self.btn_search, self.btn_download, self.entry]:
            b.configure(state=s)

    def on_search(self):
        q = self.query.get().strip()
        if not q:
            return

        if q.startswith("http") and is_playlist(q):
            self.handle_playlist_prompt(q)
            return

        self.lock_ui(True)
        self.btn_play.configure(state="disabled")
        self.status.set(T("searching"))
        threading.Thread(target=self._search_thread, args=(q, int(self.search_max.get())), daemon=True).start()

    def handle_playlist_prompt(self, url):
        video_id = extract_video_id(url)
        
        if not video_id:
            PlaylistDownloader(self, url)
            return

        win = ctk.CTkToplevel(self)
        win.withdraw()  # Nascondi temporaneamente
        win.title(T("playlist_prompt_title"))
        win.geometry("400x150")
        win.transient(self)
        
        try:
            if os.path.exists("logo.ico"):
                win.after(250, lambda: win.iconbitmap("logo.ico"))
        except Exception:
            pass

        ctk.CTkLabel(win, text=T("playlist_prompt_text"), font=("Segoe UI", 12)).pack(pady=10)

        def download_single():
            win.destroy()
            self.query.set(f"https://www.youtube.com/watch?v={video_id}")
            self.on_search()

        def download_full():
            win.destroy()
            PlaylistDownloader(self, url)

        button_frame = ctk.CTkFrame(win, fg_color="transparent")
        button_frame.pack(pady=10)
        
        ctk.CTkButton(button_frame, text=T("playlist_prompt_single"), command=download_single, width=150).pack(side="left", padx=10)
        ctk.CTkButton(button_frame, text=T("playlist_prompt_full"), command=download_full, width=150, 
                     fg_color="#28a745", hover_color="#218838").pack(side="left", padx=10)
        
        # Mostra la finestra e imposta il grab dopo che è pronta
        win.after(100, lambda: (win.deiconify(), win.grab_set()))

    def _search_thread(self, q, maxr):
        try:
            results = search_youtube(q, max_results=maxr, timeout_seconds=SETTINGS["search_timeout"])
            self.results = results
            self.tree.delete(*self.tree.get_children())
            for r in results:
                duration_sec = r.get("duration")
                if isinstance(duration_sec, int):
                    minutes, seconds = divmod(duration_sec, 60)
                    hours, minutes = divmod(minutes, 60)
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = str(duration_sec)
                    
                self.tree.insert("", "end", values=(r["title"], r["uploader"], duration_str))
            self.status.set(f"{len(results)} risultati trovati.")
        except Exception as e:
            self.status.set("Errore ricerca")
            messagebox.showerror("Errore", str(e))
        self.lock_ui(False)

    def on_download(self):
        if self.downloading:
            return
        sel = self.tree.focus()
        if not sel:
            return
        
        index = self.tree.index(sel)
        item = self.tree.item(sel)["values"]
        title = item[0]
        url = self.results[index]["url"]
        
        self.downloading = True
        self.lock_ui(True)
        self.status.set(f"Scaricamento di {title}...")

        try:
            self.tree.item(sel, tags=('downloading_tag',))
        except Exception:
            pass
            
        threading.Thread(target=self._download_thread, args=(url, self.format.get(), sel), daemon=True).start()

    def _download_thread(self, url, fmt, tree_item_id):
        try:
            def update_progress(p):
                self.queue.put(("progress", p))
            
            download_with_yt_dlp(url, fmt, SETTINGS["download_dir"], SETTINGS["speed_limit"], progress_cb=update_progress)
            
            # Dopo il download, verifica se dobbiamo gestire ID3 tag
            global LAST_FILE
            if fmt == "mp3" and SETTINGS.get("write_id3", False) and LAST_FILE and os.path.exists(LAST_FILE):
                self.queue.put(("id3_prompt", (LAST_FILE, tree_item_id)))
            else:
                self.queue.put(("done", tree_item_id))
                
        except Exception as e:
            self.queue.put(("error", str(e)))

    def play_file(self):
        global LAST_FILE
        if LAST_FILE and os.path.exists(LAST_FILE):
            try:
                if platform.system() == "Windows":
                    os.startfile(LAST_FILE)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", LAST_FILE])
                else:
                    subprocess.call(["xdg-open", LAST_FILE])
            except Exception as e:
                messagebox.showerror("Errore", f"Impossibile aprire il file: {e}")
        else:
            messagebox.showinfo("Errore", "Nessun file da riprodurre trovato.")

    def open_log(self):
        self._open_log_file(LOG_FILE, "Log del Programma")
        
    def open_playlist_log(self):
        self._open_log_file(PLAYLIST_LOG_FILE, "Traccia URL Playlist")
        
    def _open_log_file(self, filename, title):
        if not os.path.exists(filename):
            messagebox.showinfo("Log", f"Nessun file di {title} trovato.")
            return
        win = ctk.CTkToplevel(self)
        win.title(title)
        win.geometry("800x600")
        
        try:
            if os.path.exists("logo.ico"):
                win.after(250, lambda: win.iconbitmap("logo.ico"))
        except Exception:
            pass
        
        text_frame = ctk.CTkFrame(win)
        text_frame.pack(fill="both", expand=True, padx=12, pady=12)
        
        txt = ctk.CTkTextbox(text_frame, wrap="word", font=("Consolas", 12))
        txt.pack(fill="both", expand=True, padx=5, pady=5)
        
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        content = ""
        for encoding in encodings:
            try:
                with open(filename, "r", encoding=encoding) as f:
                    content = f.read()
                break
            except UnicodeDecodeError:
                continue
            except Exception as e:
                content = f"Errore lettura log: {e}"
                break
        else:
            try:
                with open(filename, "r", encoding='latin-1', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                content = f"Errore critico lettura log: {e}"
        
        txt.insert("1.0", content)
        txt.configure(state="disabled")

    def open_settings(self):
        win = ctk.CTkToplevel(self)
        win.withdraw()  # Nascondi temporaneamente
        win.title(T("settings_title"))
        win.geometry("540x650")  # Aumentata altezza per nuova opzione
        win.transient(self)
        
        try:
            if os.path.exists("logo.ico"):
                win.after(250, lambda: win.iconbitmap("logo.ico"))
        except Exception:
            pass

        win.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(win, text=T("download_folder_label"), font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w", pady=(20, 5), padx=20)
        
        dir_frame = ctk.CTkFrame(win)
        dir_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        dir_frame.grid_columnconfigure(0, weight=1)
        
        self.dir_label = ctk.CTkLabel(dir_frame, text=SETTINGS["download_dir"], wraplength=480)
        self.dir_label.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        ctk.CTkButton(dir_frame, text=T("change_folder"), command=lambda: self.change_dir(win), width=80).grid(row=0, column=1, padx=10, pady=8)

        ctk.CTkLabel(win, text=T("language_label"), font=("Segoe UI", 14, "bold")).grid(row=4, column=0, sticky="w", pady=(20, 5), padx=20)
        self.lang_var = ctk.StringVar(value=SETTINGS.get("language", "it"))
        lang_combo = ctk.CTkComboBox(win, variable=self.lang_var, values=["it", "en", "es", "de"], state="readonly")
        lang_combo.grid(row=5, column=0, sticky="ew", padx=20, pady=5)

        ctk.CTkLabel(win, text=T("theme_label"), font=("Segoe UI", 14, "bold")).grid(row=6, column=0, sticky="w", pady=(20, 5), padx=20)
        self.theme_var = ctk.StringVar(value=SETTINGS.get("theme", "system"))
        theme_combo = ctk.CTkComboBox(win, variable=self.theme_var, values=["system", "dark", "light"], state="readonly")
        theme_combo.grid(row=7, column=0, sticky="ew", padx=20, pady=5)

        # Nuova opzione ID3 Tag
        ctk.CTkLabel(win, text="ID3 Tag", font=("Segoe UI", 14, "bold")).grid(row=8, column=0, sticky="w", pady=(20, 5), padx=20)
        self.id3_var = ctk.BooleanVar(value=SETTINGS.get("write_id3", False))
        id3_check = ctk.CTkCheckBox(win, text=T("id3_enable_label"), variable=self.id3_var, 
                                   checkbox_width=20, checkbox_height=20)
        id3_check.grid(row=9, column=0, sticky="w", padx=20, pady=5)

        ctk.CTkLabel(win, text=T("speed_limit_label"), font=("Segoe UI", 14, "bold")).grid(row=10, column=0, sticky="w", pady=(20, 5), padx=20)
        self.speed_var = ctk.StringVar(value=SETTINGS.get("speed_limit", "0"))
        speed_entry = ctk.CTkEntry(win, textvariable=self.speed_var)
        speed_entry.grid(row=11, column=0, sticky="ew", padx=20, pady=5)

        ctk.CTkLabel(win, text=T("search_timeout_label"), font=("Segoe UI", 14, "bold")).grid(row=12, column=0, sticky="w", pady=(20, 5), padx=20)
        self.timeout_var = ctk.StringVar(value=str(SETTINGS.get("search_timeout", 30)))
        timeout_entry = ctk.CTkEntry(win, textvariable=self.timeout_var)
        timeout_entry.grid(row=13, column=0, sticky="ew", padx=20, pady=5)

        ctk.CTkButton(win, text=T("save_settings"), command=lambda: self.save_settings(win), 
                     fg_color="#28a745", hover_color="#218838", height=40).grid(row=14, column=0, sticky="ew", padx=20, pady=20)

        # Mostra la finestra e imposta il grab dopo che è pronta
        win.after(100, lambda: (win.deiconify(), win.grab_set()))

    def change_dir(self, parent_win):
        d = filedialog.askdirectory(initialdir=SETTINGS["download_dir"], title=T("select_download_folder"))
        if d:
            SETTINGS["download_dir"] = d
            self.dir_label.configure(text=d)
            save_settings()

    def save_settings(self, win):
        SETTINGS["language"] = self.lang_var.get()
        SETTINGS["theme"] = self.theme_var.get()
        SETTINGS["write_id3"] = self.id3_var.get()  # Salva nuova impostazione
        SETTINGS["speed_limit"] = self.speed_var.get().strip() or "0"
        
        try:
            SETTINGS["search_timeout"] = int(self.timeout_var.get())
        except ValueError:
            SETTINGS["search_timeout"] = 30
            
        save_settings()
        ctk.set_appearance_mode(SETTINGS["theme"])
        messagebox.showinfo("Impostazioni", "Impostazioni salvate con successo!", parent=win)
        win.destroy()

    def check_for_updates(self):
        try:
            last_check_str = SETTINGS.get("last_update_check", "1970-01-01T00:00:00")
            last_check = datetime.fromisoformat(last_check_str)
            days_passed = (datetime.now() - last_check).days

            if days_passed >= 3:
                if messagebox.askyesno(T("updater_prompt_title"), T("updater_prompt_text")):
                    self.run_updater()
                else:
                    SETTINGS["last_update_check"] = datetime.now().isoformat()
                    save_settings()
        except Exception:
            pass

    def run_updater(self):
        self.updater_win = ctk.CTkToplevel(self)
        self.updater_win.title(T("updater_title"))
        self.updater_win.geometry("700x400")
        self.updater_win.transient(self)
        self.updater_win.grab_set()
        
        try:
            if os.path.exists("logo.ico"):
                self.updater_win.after(250, lambda: self.updater_win.iconbitmap("logo.ico"))
        except Exception:
            pass

        self.updater_win.grid_columnconfigure(0, weight=1)
        self.updater_win.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.updater_win, text=T("updater_running"), font=("Segoe UI", 16, "bold")).grid(row=0, column=0, pady=20)
        
        text_frame = ctk.CTkFrame(self.updater_win)
        text_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 20))
        text_frame.grid_columnconfigure(0, weight=1)
        text_frame.grid_rowconfigure(0, weight=1)
        
        self.updater_log_text = ctk.CTkTextbox(text_frame, wrap="word", font=("Consolas", 12))
        self.updater_log_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.updater_log_text.configure(state="disabled")

        threading.Thread(target=self._updater_thread, daemon=True).start()
        self._check_updater_queue()

    def _updater_thread(self):
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                       text=True, encoding='utf-8', bufsize=1, universal_newlines=True,
                                       creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)

            for line in process.stdout:
                self.queue.put(("updater_log", line))
            
            process.wait()

            if process.returncode == 0:
                SETTINGS["last_update_check"] = datetime.now().isoformat()
                save_settings()
                self.queue.put(("updater_done", True))
            else:
                self.queue.put(("updater_done", False))
                
        except Exception:
            self.queue.put(("updater_done", False))

    def _check_updater_queue(self):
        try:
            while True:
                typ, payload = self.queue.get_nowait()
                
                if typ == "updater_log":
                    line = payload
                    self.updater_log_text.configure(state="normal")
                    self.updater_log_text.insert("end", line)
                    self.updater_log_text.see("end")
                    self.updater_log_text.configure(state="disabled")
                
                elif typ == "updater_done":
                    success = payload
                    if success:
                        messagebox.showinfo(T("updater_title"), T("updater_success"), parent=self.updater_win)
                    else:
                        messagebox.showerror(T("updater_title"), T("updater_fail"), parent=self.updater_win)
                    self.updater_win.destroy()
                    return
                
                else:
                    self.queue.put_nowait((typ, payload))

        except queue.Empty:
            pass
        
        self.updater_win.after(100, self._check_updater_queue)

    def _loop(self):
        try:
            while True:
                typ, payload = self.queue.get_nowait()
                
                if typ == "done":
                    item_id = payload
                    self.downloading = False
                    self.lock_ui(False)
                    self.btn_play.configure(state="normal")
                    self.progress.set(1.0)
                    self.status.set(T("complete"))
                    
                    if item_id:
                        try:
                            self.tree.item(item_id, tags=()) 
                        except Exception:
                            pass
                            
                    messagebox.showinfo("Completato", T("complete_msg"))
                    self.after(5000, self.reset_ui)
                
                elif typ == "id3_prompt":
                    filepath, tree_item_id = payload
                    filename = os.path.basename(filepath)
                    
                    # Prima completa lo stato UI
                    self.downloading = False
                    self.lock_ui(False)
                    self.btn_play.configure(state="normal")
                    self.progress.set(1.0)
                    self.status.set(T("complete"))
                    
                    if tree_item_id:
                        try:
                            self.tree.item(tree_item_id, tags=()) 
                        except Exception:
                            pass
                    
                    # POI mostra la finestra ID3
                    self.after(100, lambda: DeezerMetadataWindow(self, filename, filepath, self.deezer_tagger))
                    
                    # Non mostrare messaggio "Completato" qui - lo farà la finestra ID3
                    self.after(3000, self.reset_ui)
                
                elif typ == "error":
                    self.downloading = False
                    self.lock_ui(False)
                    messagebox.showerror("Errore", payload)
                
                elif typ == "progress":
                    self.progress.set(payload / 100)
        
        except queue.Empty:
            pass
        
        self.after(150, self._loop)

    def reset_ui(self):
        global LAST_FILE
        self.query.set("")
        self.results = []
        self.tree.delete(*self.tree.get_children())
        self.status.set(T("ready"))
        self.btn_play.configure(state="disabled")
        self.progress.set(0)
        self.lock_ui(False)
        LAST_FILE = None
        log("🟢 UI resettata e pronta per un nuovo download.")
        print("Ui Bloccata con successo. Pronto per un nuovo download.")

# ---------------------- MAIN ----------------------
def main():
    log("🚀 Avvio di MUSIC WAVVER (main)...")
    
    # CONTROLLA FFMPEG PRIMA DI TUTTO
    log("🔍 Controllo presenza FFmpeg...")
    detect_ffmpeg()  # Se FFmpeg non c'è, questa funzione chiude l'app
    
    # POI CONTROLLA ACCORDO LEGALE
    if not SETTINGS.get("agreement_accepted", False):
        if not show_agreement():
            log("🛑 Programma chiuso a causa del mancato consenso all'accordo legale.")
            sys.exit(0)
    
    # INFINE AVVIA L'APP
    app = YTDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()

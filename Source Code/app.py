#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA - 07/01/2025
MUSIC WAVVER 4.0
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
from tkinter import messagebox, filedialog, ttk, PhotoImage
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

# ---------------------- DETECT OS ----------------------
def get_linux_distro():
    """Rileva la distribuzione Linux"""
    try:
        with open("/etc/os-release", "r") as f:
            for line in f:
                if line.startswith("ID="):
                    return line.split("=")[1].strip().strip('"').lower()
    except:
        return "unknown"
    return "unknown"

# ---------------------- DEFAULT SETTINGS ----------------------
if platform.system() == "Windows":
    DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Music", "Scaricati")
else:
    DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Music", "Scaricati")

DEFAULT_SETTINGS = {
    "download_dir": DEFAULT_DOWNLOAD_DIR,
    "theme": "system",
    "speed_limit": "0",
    "search_timeout": 30,
    "agreement_accepted": False,
    "language": "it",
    "last_update_check": "1970-01-01T00:00:00",
    "max_retries": 3,
    "retry_delay": 5,
    "write_id3": False,
    "audio_quality": "320"
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

# ---------------------- CONTROLLO FFMPEG (CROSS-PLATFORM) ----------------------
def show_ffmpeg_missing_error_linux():
    """Mostra finestra di errore per FFmpeg mancante su Linux"""
    root = ctk.CTk()
    root.title("FFmpeg Mancante")
    root.geometry("600x450")
    root.resizable(False, False)
    
    # Centra la finestra
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (600 // 2)
    y = (root.winfo_screenheight() // 2) - (450 // 2)
    root.geometry(f"600x450+{x}+{y}")
    
    # Contenuto
    frame = ctk.CTkFrame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    ctk.CTkLabel(frame, text="❌", font=("Segoe UI", 48)).pack(pady=(20, 10))
    ctk.CTkLabel(frame, text="FFmpeg Non Trovato", font=("Segoe UI", 20, "bold")).pack(pady=(0, 20))
    
    # Istruzioni specifiche per Linux
    instructions = "FFmpeg è necessario per il funzionamento di questo programma.\n\n"
    instructions += "Per installare FFmpeg su Linux:\n\n"
    
    # Rileva la distribuzione
    distro = get_linux_distro()
    if distro in ["ubuntu", "debian", "linuxmint", "mint"]:
        instructions += "Ubuntu/Debian/Mint:\n"
        instructions += "  sudo apt update && sudo apt install ffmpeg -y\n\n"
    elif distro in ["fedora", "rhel", "centos"]:
        instructions += "Fedora/RHEL/CentOS:\n"
        instructions += "  sudo dnf install ffmpeg -y\n\n"
    elif distro in ["arch", "manjaro", "endeavouros"]:
        instructions += "Arch/Manjaro:\n"
        instructions += "  sudo pacman -S ffmpeg\n\n"
    elif distro in ["opensuse", "tumbleweed"]:
        instructions += "openSUSE:\n"
        instructions += "  sudo zypper install ffmpeg\n\n"
    else:
        instructions += "Usa il gestore pacchetti della tua distribuzione:\n"
        instructions += "  sudo [apt/dnf/pacman/zypper] install ffmpeg\n\n"
    
    instructions += "Dopo l'installazione, riavvia il programma."
    
    text_widget = ctk.CTkTextbox(frame, wrap="word", height=200, font=("Consolas", 12))
    text_widget.pack(fill="both", expand=True, padx=10, pady=10)
    text_widget.insert("1.0", instructions)
    text_widget.configure(state="disabled")
    
    ctk.CTkButton(frame, text="Chiudi Applicazione", command=sys.exit, 
                 fg_color="#dc3545", hover_color="#c82333", height=40).pack(pady=20)
    
    root.mainloop()

def show_ffmpeg_missing_error_windows():
    """Mostra finestra di errore per FFmpeg mancante su Windows"""
    root = ctk.CTk()
    root.title("FFmpeg Mancante")
    root.geometry("600x400")
    root.resizable(False, False)
    
    # Centra la finestra
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (600 // 2)
    y = (root.winfo_screenheight() // 2) - (400 // 2)
    root.geometry(f"600x400+{x}+{y}")
    
    # Contenuto
    frame = ctk.CTkFrame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Icona errore
    ctk.CTkLabel(frame, text="❌", font=("Segoe UI", 48)).pack(pady=(20, 10))
    
    # Titolo
    ctk.CTkLabel(frame, text="FFmpeg Non Trovato", font=("Segoe UI", 20, "bold")).pack(pady=(0, 20))
    
    # Istruzioni
    instructions = "FFmpeg è necessario per il funzionamento di questo programma.\n\n"
    instructions += "Per installare FFmpeg su Windows:\n\n"
    instructions += "1. Apri PowerShell come Amministratore\n"
    instructions += "2. Esegui questo comando:\n"
    instructions += "   winget install Gyan.FFmpeg\n\n"
    instructions += "Oppure scarica manualmente da:\n"
    instructions += "https://www.gyan.dev/ffmpeg/builds/"
    
    text_widget = ctk.CTkTextbox(frame, wrap="word", height=200, font=("Consolas", 12))
    text_widget.pack(fill="both", expand=True, padx=10, pady=10)
    text_widget.insert("1.0", instructions)
    text_widget.configure(state="disabled")
    
    # Pulsante chiudi
    ctk.CTkButton(frame, text="Chiudi Applicazione", command=sys.exit, 
                 fg_color="#dc3545", hover_color="#c82333", height=40).pack(pady=20)
    
    root.mainloop()

def detect_ffmpeg():
    """Controlla se FFmpeg è disponibile, altrimenti mostra finestra di errore"""
    log("🔍 Controllo presenza FFmpeg...")
    
    # Prima cerca nel PATH di sistema
    found = shutil.which("ffmpeg")
    if found:
        log(f"✅ ffmpeg trovato: {found}")
        return found
    
    # Se non trovato, mostra errore specifico per OS
    log("❌ FFmpeg non trovato nel sistema")
    
    current_os = platform.system().lower()
    if current_os == "linux":
        show_ffmpeg_missing_error_linux()
    elif current_os == "windows":
        show_ffmpeg_missing_error_windows()
    else:  # macOS o altri
        messagebox.showerror("FFmpeg Mancante", 
                           "FFmpeg è necessario per il funzionamento di questo programma.\n\n"
                           "Per installare FFmpeg su macOS:\n"
                           "  brew install ffmpeg\n\n"
                           "Per Linux:\n"
                           "  sudo apt install ffmpeg  # Debian/Ubuntu\n"
                           "  sudo dnf install ffmpeg  # Fedora\n"
                           "  sudo pacman -S ffmpeg    # Arch")
    
    sys.exit(1)

FFMPEG_PATH = detect_ffmpeg()

# ---------------------- FUNZIONI ID3 DEEZER ----------------------
class DeezerID3Tagger:
    def __init__(self):
        self.api_base = "https://api.deezer.com"
        
    def clean_search_query(self, query):
        """Pulisci la query di ricerca rimuovendo parole comuni e parentesi"""
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
        """Cerca una traccia su Deezer - restituisce più risultati per matching"""
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
    
    def calculate_matching_score(self, youtube_title, youtube_uploader, deezer_track, youtube_duration=None, search_position=0):
        """Calcola uno score di matching tra YouTube e Deezer (NUOVA LOGICA)"""
        score = 0
        max_score = 100
        
        # Prepara i testi per il confronto (lowercase)
        yt_title_lower = youtube_title.lower()
        yt_uploader_lower = youtube_uploader.lower()
        dz_title_lower = deezer_track["title"].lower()
        dz_artist_lower = deezer_track["artist"].lower()
        
        # 1. Uploader = o simile all'Artista (20pt)
        # Controlla se l'uploader contiene il nome dell'artista o viceversa
        if dz_artist_lower in yt_uploader_lower or yt_uploader_lower in dz_artist_lower:
            score += 20
        else:
            # Confronto parole per parole con similarità parziale
            artist_words = set(dz_artist_lower.split())
            uploader_words = set(yt_uploader_lower.split())
            common_words = artist_words.intersection(uploader_words)
            
            if common_words:
                similarity = len(common_words) / max(len(artist_words), len(uploader_words))
                if similarity > 0.5:  # Almeno 50% di similarità
                    score += int(similarity * 20)
        
        # 2. Nome traccia = o simile al nome della canzone (20pt)
        # Pulisci il titolo YouTube per rimuovere informazioni extra
        yt_title_clean = re.sub(r'[\[\(].*?[\]\)]', '', yt_title_lower)
        yt_title_clean = re.sub(r'\b(official|video|audio|lyric|lyrics|hd|hq|4k|1080p|720p|mv|clip|music|song|remix|cover|original|extended|radio edit)\b', '', yt_title_clean, flags=re.IGNORECASE)
        yt_title_clean = re.sub(r'\s+', ' ', yt_title_clean).strip()
        
        dz_title_clean = re.sub(r'[^\w\s]', '', dz_title_lower)
        
        # Confronto esatto
        if yt_title_clean == dz_title_lower or dz_title_lower in yt_title_clean or yt_title_clean in dz_title_lower:
            score += 20
        else:
            # Confronto parole per parole
            yt_words = set(yt_title_clean.split())
            dz_words = set(dz_title_clean.split())
            common_words = yt_words.intersection(dz_words)
            
            if common_words:
                similarity = len(common_words) / max(len(yt_words), len(dz_words))
                score += int(similarity * 20)
        
        # 3. Punteggio per tipo di contenuto (MODIFICATO: più punti ad Audio che a Video)
        # MODIFICA QUI: assegna punti diversi in base al tipo di contenuto
        if 'official audio' in yt_title_lower:
            # Official Audio: massimo punteggio (30pt)
            score += 30
            log(f"📀 Official Audio: +30 punti")
        elif 'official music video' in yt_title_lower:
            # Video musicale ufficiale
            score += 25
            log(f"🎬 Official Music Video: +25 punti")
        elif 'official video' in yt_title_lower:
            # Video ufficiale
            score += 20
            log(f"🎥 Official Video: +20 punti")
        elif 'audio' in yt_title_lower:
            # Solo audio (non ufficiale)
            score += 18
            log(f"🔊 Audio: +18 punti")
        elif 'live' in yt_title_lower and 'performance' in yt_title_lower:
            # Performance live
            score += 15
            log(f"🎤 Live Performance: +15 punti")
        elif 'lyric' in yt_title_lower or 'lyrics' in yt_title_lower:
            # Video lyrics
            score += 5
            log(f"📝 Lyrics: +5 punti")
        elif 'cover' in yt_title_lower:
            # Cover
            score += 8
            log(f"🎵 Cover: +8 punti")
        elif 'remix' in yt_title_lower:
            # Remix
            score += 8
            log(f"🌀 Remix: +8 punti")
        else:
            # Altri tipi
            score += 10
            log(f"📹 Altro: +10 punti")
        
        # 4. Tempo che corrisponde al tempo della traccia (20pt)
        if youtube_duration and deezer_track.get("duration"):
            youtube_duration = int(youtube_duration)
            deezer_duration = int(deezer_track["duration"])
            diff = abs(youtube_duration - deezer_duration)
            
            if diff <= 5:  # Differenza di 5 secondi o meno
                score += 20
                log(f"⏱️ Durata perfetta (±5s): +20 punti")
            elif diff <= 15:  # Differenza di 15 secondi o meno
                score += 15
                log(f"⏱️ Durata buona (±15s): +15 punti")
            elif diff <= 30:  # Differenza di 30 secondi o meno
                score += 10
                log(f"⏱️ Durata accettabile (±30s): +10 punti")
            elif diff <= 60:  # Differenza di 1 minuto o meno
                score += 5
                log(f"⏱️ Durata discreta (±60s): +5 punti")
        
        # 5. Rilevanza della ricerca (posizione) - 10pt
        # Primo risultato: 10pt, secondo: 8pt, terzo: 6pt, quarto: 4pt, quinto: 2pt
        if search_position < 5:
            position_scores = [10, 8, 6, 4, 2]
            position_score = position_scores[search_position]
            score += position_score
            log(f"🏆 Posizione {search_position+1}: +{position_score} punti")
        
        # Log del punteggio totale
        log(f"📊 Punteggio totale: {min(score, max_score)}/100")
        
        # Normalizza a max 100
        return min(score, max_score)
    
    def find_best_match(self, youtube_title, youtube_uploader, youtube_duration=None, search_position=0, limit=5):
        """Trova il miglior match su Deezer per un video YouTube"""
        tracks = self.search_track(youtube_title, limit=limit)
        
        if not tracks:
            return None
        
        # Calcola score per ogni traccia
        scored_tracks = []
        for i, track in enumerate(tracks):
            score = self.calculate_matching_score(
                youtube_title, 
                youtube_uploader,
                track, 
                youtube_duration,
                search_position
            )
            scored_tracks.append({
                **track,
                "score": score
            })
        
        # Ordina per score decrescente
        scored_tracks.sort(key=lambda x: x["score"], reverse=True)
        
        # Restituisci il migliore se ha score > 40
        best_match = scored_tracks[0] if scored_tracks else None
        
        if best_match and best_match["score"] >= 40:
            log(f"✅ Miglior match trovato: '{best_match['title']}' - Score: {best_match['score']}/100")
            return best_match
        
        log(f"⚠️ Nessun buon match trovato (miglior score: {best_match['score'] if best_match else 0}/100)")
        return None
    
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

# ---------------------- FINESTRA METADATI DEEZER AUTOMATICA ----------------------
def apply_deezer_id3_automatically(parent, filename, filepath, deezer_tagger):
    """Applica automaticamente i metadati Deezer (primo risultato)"""
    log(f"🔍 Ricerca automatica metadati per: {filename}")
    
    # Usa il nome del file per la ricerca
    search_query = filename
    
    # Cerca metadatti (solo primo risultato)
    results = deezer_tagger.search_track(search_query, limit=1)
    
    if not results:
        log(f"⚠️ Nessun risultato Deezer trovato per: {filename}")
        return False
    
    # Prendi il primo risultato
    track = results[0]
    
    # Scarica copertina
    cover_data = deezer_tagger.download_cover(track.get("cover_url", ""))
    
    # Applica tag ID3
    metadata = {
        "title": track.get("title", ""),
        "artist": track.get("artist", ""),
        "album": track.get("album", ""),
        "year": track.get("year", ""),
        "genre": track.get("genre", ""),
        "track_number": str(track.get("track_number", ""))
    }
    
    success = deezer_tagger.apply_id3_tags(filepath, metadata, cover_data)
    
    if success:
        log(f"✅ Tag ID3 applicati automaticamente a: {filepath}")
        messagebox.showinfo("Metadati Applicati", 
                          f"Tag ID3 applicati con successo a:\n{filename}",
                          parent=parent)
    else:
        log(f"❌ Fallita applicazione automatica tag ID3 per: {filepath}")
        messagebox.showwarning("Attenzione", 
                             f"Impossibile applicare tag ID3 a:\n{filename}",
                             parent=parent)
    
    return success

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

# ---------------------- RICERCA INTEGRATA YOUTUBE + DEEZER ----------------------
def _yt_search_worker(query, max_results, result_queue, deezer_tagger):
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
                    entries = info.get("entries", [])
                    
                    # Per ogni risultato YouTube, cerca il match migliore su Deezer
                    for position, e in enumerate(entries):
                        if e.get('id'):
                            youtube_title = e.get("title", "Sconosciuto")
                            youtube_uploader = e.get("uploader", "Sconosciuto")
                            youtube_duration = e.get("duration", None)
                            
                            # Cerca il miglior match su Deezer
                            best_deezer_match = None
                            if deezer_tagger:
                                best_deezer_match = deezer_tagger.find_best_match(
                                    youtube_title, 
                                    youtube_uploader,
                                    youtube_duration,
                                    position,  # Aggiungi la posizione nella ricerca
                                    limit=3
                                )
                            
                            results.append({
                                "title": youtube_title,
                                "url": f"https://www.youtube.com/watch?v={e['id']}",
                                "duration": youtube_duration,
                                "uploader": youtube_uploader,
                                "deezer_match": best_deezer_match,  # Aggiungi il match Deezer
                                "youtube_original": youtube_title,  # Mantieni il titolo originale
                                "search_position": position  # Memorizza la posizione nella ricerca
                            })
                    
                    log(f"✅ Ricerca completata. Trovati {len(results)} risultati.")
                    result_queue.put(("ok", results))
                    return
                elif info.get("id"):
                    youtube_title = info.get("title", "Sconosciuto")
                    youtube_uploader = info.get("uploader", "Sconosciuto")
                    youtube_duration = info.get("duration", None)
                    
                    # Cerca il miglior match su Deezer (posizione 0 per URL singolo)
                    best_deezer_match = None
                    if deezer_tagger:
                        best_deezer_match = deezer_tagger.find_best_match(
                            youtube_title, 
                            youtube_uploader,
                            youtube_duration,
                            0,  # Posizione 0 per URL singolo
                            limit=3
                        )
                    
                    results = [{
                        "title": youtube_title,
                        "url": info.get("webpage_url", query),
                        "duration": youtube_duration,
                        "uploader": youtube_uploader,
                        "deezer_match": best_deezer_match,
                        "youtube_original": youtube_title,
                        "search_position": 0
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

def search_youtube(query, max_results=10, timeout_seconds=30, deezer_tagger=None):
    rq = queue.Queue()
    video_id = extract_video_id(query)
    
    if video_id and query.startswith("http"):
        query_to_search = f"https://www.youtube.com/watch?v={video_id}"
    else:
        query_to_search = query
    
    # Avvia il thread di ricerca
    t = threading.Thread(target=_yt_search_worker, args=(query_to_search, max_results, rq, deezer_tagger), daemon=True)
    t.start()
    
    # Attendi direttamente senza timer
    try:
        typ, payload = rq.get(timeout=timeout_seconds)
        return payload if typ == "ok" else (_ for _ in ()).throw(RuntimeError(payload))
    except queue.Empty:
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
            # Configurazione postprocessor cross-platform
            postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": fmt}]
            
            # Aggiungi qualità se specificata (solo per MP3)
            if fmt == "mp3" and SETTINGS.get("audio_quality"):
                postprocessors[0]["preferredquality"] = SETTINGS["audio_quality"]
            
            # Configurazione yt-dlp cross-platform
            ydl_opts = {
                "outtmpl": outtmpl,
                "format": "bestaudio/best",
                "quiet": True,
                "noplaylist": True,
                "ffmpeg_location": os.path.dirname(FFMPEG_PATH) if platform.system() == "Windows" else None,
                "postprocessors": postprocessors,
                "progress_hooks": [hook],
                "socket_timeout": 30,
                "extractor_retries": 3
            }
            
            # Su Linux/Unix, se ffmpeg è nel PATH, non specificare ffmpeg_location
            if platform.system() != "Windows":
                # Rimuovi ffmpeg_location se non necessario
                ydl_opts.pop("ffmpeg_location", None)
            
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
        self.title(T("playlist_title"))
        self.geometry("850x650")
        self.transient(master)
        
        self._set_icon()

        self.playlist_url = url
        self.playlist_videos = []
        self.downloading = False
        self.stop_requested = False
        self.current_video_index = 0
        self.completed_count = 0
        self.video_progress = {}  # Dizionario per tracciare progresso di ogni video
        
        self.download_dir = ctk.StringVar(value=SETTINGS["download_dir"])
        self.format = ctk.StringVar(value="mp3")  # MP3 come predefinito
        self.status = ctk.StringVar(value=T("playlist_status_fetching"))
        self.current_video_status = ctk.StringVar(value="")
        self.overall_progress_text = ctk.StringVar(value="")
        self.overall_progress_value = ctk.DoubleVar(value=0)

        log(f"🆕 Avvio PlaylistDownloader per URL: {url}")

        self._build_ui()
        open(PLAYLIST_LOG_FILE, 'w').close()
        
        threading.Thread(target=self._search_playlist_thread, daemon=True).start()
        self.after(100, self._loop)

    def _set_icon(self):
        try:
            current_os = platform.system()
            if current_os == "Windows" and os.path.exists("logo.ico"):
                self.iconbitmap("logo.ico")
            elif current_os == "Linux" and os.path.exists("logo.png"):
                # Su Linux usa PNG
                img = PhotoImage(file="logo.png")
                self.iconphoto(False, img)
            elif os.path.exists("logo.ico"):
                # Fallback per Windows
                self.iconbitmap("logo.ico")
        except Exception as e:
            log(f"⚠️ Impossibile impostare icona: {e}")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Titolo
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 5))
        ctk.CTkLabel(title_frame, text="📥 Download Playlist", font=("Segoe UI", 16, "bold")).pack(side="left")
        
        # Directory
        ctk.CTkLabel(self, text=T("playlist_select_dir"), font=("Segoe UI", 12)).grid(row=1, column=0, sticky="w", pady=(5, 5), padx=12)
        
        dir_frame = ctk.CTkFrame(self)
        dir_frame.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 10))
        dir_frame.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(dir_frame, textvariable=self.download_dir, wraplength=600).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        ctk.CTkButton(dir_frame, text=T("change_folder"), command=self.change_dir, width=80).grid(row=0, column=1, padx=10, pady=8)

        # Tabella video
        tree_frame = ctk.CTkFrame(self)
        tree_frame.grid(row=3, column=0, sticky="nsew", padx=12, pady=(0, 10))
        tree_frame.grid_columnconfigure(0, weight=1)
        tree_frame.grid_rowconfigure(0, weight=1)

        self._configure_treeview_style()
        
        cols = ("#", "Titolo", "Durata", "Uploader", "Stato", "Progresso")
        self.tree = Treeview(tree_frame, columns=cols, show="headings", height=12)
        self.tree.column("#", width=40, anchor="center")
        self.tree.column("Titolo", width=280, anchor="w")
        self.tree.column("Durata", width=60, anchor="center")
        self.tree.column("Uploader", width=120, anchor="w")
        self.tree.column("Stato", width=100, anchor="center")
        self.tree.column("Progresso", width=80, anchor="center")
        
        for c in cols:
            self.tree.heading(c, text=c)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.grid(row=0, column=0, sticky="nsew", padx=(5, 0), pady=5)
        scrollbar.grid(row=0, column=1, sticky="ns", pady=5)

        # Controlli
        controls_frame = ctk.CTkFrame(self)
        controls_frame.grid(row=4, column=0, sticky="ew", padx=12, pady=(0, 10))
        
        ctk.CTkLabel(controls_frame, text=T("format_label")).pack(side="left", padx=(10, 5))
        ctk.CTkOptionMenu(controls_frame, variable=self.format, values=["wav", "mp3", "flac"]).pack(side="left", padx=5)
        
        self.btn_download = ctk.CTkButton(controls_frame, text=T("playlist_download_btn"), 
                                         command=self._start_download, state="disabled")
        self.btn_download.pack(side="right", padx=(5, 10))
        
        self.btn_stop = ctk.CTkButton(controls_frame, text="⏹️ Ferma", 
                                     command=self._stop_download, state="disabled",
                                     fg_color="#dc3545", hover_color="#c82333")
        self.btn_stop.pack(side="right", padx=5)

        # Progresso corrente
        progress_frame = ctk.CTkFrame(self)
        progress_frame.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 5))
        
        ctk.CTkLabel(progress_frame, text="Video corrente:", font=("Segoe UI", 11)).pack(side="left", padx=(10, 5))
        ctk.CTkLabel(progress_frame, textvariable=self.current_video_status, font=("Segoe UI", 11, "bold")).pack(side="left", padx=5)
        
        # Progresso generale
        ctk.CTkLabel(self, textvariable=self.overall_progress_text, font=("Segoe UI", 12)).grid(row=6, column=0, sticky="w", padx=12)
        self.progress_bar = ctk.CTkProgressBar(self, variable=self.overall_progress_value)
        self.progress_bar.grid(row=7, column=0, sticky="ew", padx=12, pady=(5, 5))
        
        # Status
        ctk.CTkLabel(self, textvariable=self.status, font=("Segoe UI", 11)).grid(row=8, column=0, sticky="w", padx=12, pady=(0, 10))

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
            highlightthickness=0,
            font=('Segoe UI', 10)
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
        self.stop_requested = False
        self.current_video_index = 0
        self.completed_count = 0
        self.video_progress = {}
        
        # Disabilita pulsante download, abilita stop
        self.btn_download.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        
        # Resetta lo stato di tutti i video
        for i in range(len(self.playlist_videos)):
            self.tree.set(str(i), "Stato", "In attesa")
            self.tree.set(str(i), "Progresso", "0%")
        
        log(f"⬇️ Avvio download playlist. {len(self.playlist_videos)} video da scaricare.")
        
        # Avvia il thread di download
        threading.Thread(target=self._download_playlist_thread, daemon=True).start()

    def _stop_download(self):
        if self.downloading:
            self.stop_requested = True
            self.status.set("Fermatura in corso...")
            log("🛑 Fermatura download playlist richiesta dall'utente")

    def _download_single_video_with_subprocess(self, video_index, url, title, output_dir):
        """Scarica un singolo video usando subprocess per non bloccare la GUI"""
        video_number = video_index + 1
        
        # Crea il template per il nome file
        safe_title = re.sub(r'[\\/*?:"<>|]', "_", title)
        output_template = os.path.join(output_dir, f"{video_number}. {safe_title}.%(ext)s")
        
        # Costruisci il comando yt-dlp
        cmd = [
            "yt-dlp",
            "-o", output_template,
            "-f", "bestaudio/best",
            "--no-playlist",
            "--socket-timeout", "30",
            "--extractor-retries", "3",
            "--newline"  # Importante: output in tempo reale
        ]
        
        # Aggiungi postprocessor per l'estrazione audio
        cmd.extend(["--postprocessor-args", f"-c:a {self.format.get()}"])
        
        if self.format.get() == "mp3" and SETTINGS.get("audio_quality"):
            cmd.extend(["--postprocessor-args", f"-b:a {SETTINGS['audio_quality']}k"])
        
        # Aggiungi limitazione velocità se impostata
        speed_limit = SETTINGS["speed_limit"]
        if speed_limit != "0":
            cmd.extend(["--limit-rate", speed_limit])
        
        # Aggiungi l'URL
        cmd.append(url)
        
        log(f"Comando per video {video_number}: {' '.join(cmd)}")
        
        try:
            # Esegui yt-dlp come subprocess per non bloccare la GUI
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1,
                encoding='utf-8',
                errors='ignore'
            )
            
            # Leggi l'output in tempo reale
            while True:
                if self.stop_requested:
                    process.terminate()
                    log(f"❌ Download video {video_number} fermato dall'utente")
                    return False
                
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                
                if line:
                    # Analizza l'output per estrarre il progresso
                    progress = self._parse_yt_dlp_progress(line)
                    if progress is not None:
                        # Invia aggiornamento progresso alla GUI
                        self.master.queue.put(("playlist_video_progress", (video_index, progress)))
            
            # Controlla il codice di uscita
            return_code = process.wait()
            return return_code == 0
            
        except Exception as e:
            log(f"❌ Errore nel download del video {video_number}: {e}")
            return False

    def _parse_yt_dlp_progress(self, line):
        """Analizza l'output di yt-dlp per estrarre il progresso percentuale"""
        try:
            # Pattern per estrarre la percentuale (es: "[download]  45.7% of ...")
            if "[download]" in line:
                match = re.search(r'(\d+\.?\d*)%', line)
                if match:
                    return float(match.group(1))
            
            # Pattern per quando il download è completo
            if "100%" in line or "[ExtractAudio]" in line or "Deleting original file" in line:
                return 100.0
                
        except Exception:
            pass
        return None

    def _download_playlist_thread(self):
        """Thread principale per scaricare l'intera playlist"""
        total_videos = len(self.playlist_videos)
        self.completed_count = 0
        output_dir = self.download_dir.get()
        
        log(f"Inizio download playlist verso: {output_dir}")
        
        for i in range(total_videos):
            if self.stop_requested:
                log("⏹️ Download playlist fermato dall'utente")
                self.master.queue.put(("playlist_stopped", self.completed_count))
                break
            
            video = self.playlist_videos[i]
            video_number = i + 1
            
            # Aggiorna lo stato nella GUI
            self.master.queue.put(("playlist_progress_update", (i, "start")))
            self.master.queue.put(("playlist_current_video", (i, f"{video_number}. {video['title']}")))
            
            log(f"--- Avvio download {video_number}/{total_videos}: '{video['title']}' ---")
            
            # Scarica il video
            success = self._download_single_video_with_subprocess(i, video["url"], video["title"], output_dir)
            
            if success:
                self.completed_count += 1
                self.master.queue.put(("playlist_progress_update", (i, "done")))
                self.master.queue.put(("playlist_video_progress", (i, 100)))
                log(f"--- ✅ Download {video_number} completato: {video['title']} ---")
            else:
                self.master.queue.put(("playlist_progress_update", (i, "failed")))
                log(f"--- ❌ Download {video_number} fallito: {video['title']} ---")
            
            # Aggiorna il progresso generale
            self.master.queue.put(("playlist_overall_progress", (i + 1, total_videos, self.completed_count)))
            
            # Piccola pausa tra i video
            time.sleep(0.5)
        
        if not self.stop_requested:
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
                            self.tree.insert("", "end", iid=str(i), 
                                           values=(i+1, video["title"], video["duration"], 
                                                  video["uploader"], "In attesa", "0%"))
                        
                        self.status.set(f"✅ Trovati {video_count} video. Pronto per il download.")
                        self.overall_progress_text.set(f"0/{video_count} video scaricati")
                        self.btn_download.configure(state="normal")
                        self.progress_bar.configure(maximum=video_count)
                        log(f"✅ Trovati {video_count} video nella playlist.")
                    else:
                        self.status.set("⚠️ Playlist recuperata ma nessun video trovato o formato non supportato.")
                        self.btn_download.configure(state="disabled")
                
                elif typ == "playlist_current_video":
                    video_idx, title = payload
                    self.current_video_status.set(title[:80] + "..." if len(title) > 80 else title)
                
                elif typ == "playlist_progress_update":
                    video_index, status = payload
                    try:
                        iid = str(video_index)
                        if status == "start":
                            self.tree.set(iid, "Stato", "📥 Scaricando")
                            self.tree.set(iid, "Progresso", "0%")
                        elif status == "done":
                            self.tree.set(iid, "Stato", "✅ Completato")
                            self.tree.set(iid, "Progresso", "100%")
                        elif status == "failed":
                            self.tree.set(iid, "Stato", "❌ Fallito")
                            self.tree.set(iid, "Progresso", "ERR")
                        
                        # Forza l'aggiornamento visivo
                        self.tree.update_idletasks()
                    except Exception as e:
                        log(f"Errore aggiornamento stato video: {e}")
                
                elif typ == "playlist_video_progress":
                    video_index, progress = payload
                    try:
                        iid = str(video_index)
                        if 0 <= progress <= 100:
                            self.tree.set(iid, "Progresso", f"{progress:.1f}%")
                            # Forza l'aggiornamento visivo
                            self.tree.update_idletasks()
                    except Exception as e:
                        log(f"Errore aggiornamento progresso video: {e}")
                
                elif typ == "playlist_overall_progress":
                    current_idx_processed, total, completed_count = payload
                    self.overall_progress_value.set(current_idx_processed)
                    self.overall_progress_text.set(f"{completed_count}/{total} video scaricati (in elaborazione: {current_idx_processed}/{total})")
                    
                    if self.downloading:
                        progress_percent = (current_idx_processed / total) * 100
                        self.status.set(f"📊 Progresso generale: {progress_percent:.1f}%")
                
                elif typ == "playlist_done":
                    completed = payload
                    total = len(self.playlist_videos)
                    log("✅ Download playlist completato.")
                    
                    self.status.set("✅ Download completato!")
                    self.current_video_status.set("")
                    self.overall_progress_text.set(f"{completed}/{total} video scaricati con successo")
                    self.btn_download.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self.downloading = False
                    
                    messagebox.showinfo("Download Completato", 
                                      f"Download playlist completato!\n\n"
                                      f"{completed}/{total} video scaricati con successo.",
                                      parent=self)
                    self.destroy()
                
                elif typ == "playlist_stopped":
                    completed = payload
                    total = len(self.playlist_videos)
                    log("⏹️ Download playlist fermato dall'utente.")
                    
                    self.status.set("⏹️ Download fermato")
                    self.current_video_status.set("")
                    self.overall_progress_text.set(f"{completed}/{total} video scaricati prima dell'arresto")
                    self.btn_download.configure(state="normal")
                    self.btn_stop.configure(state="disabled")
                    self.downloading = False
                    
                    messagebox.showinfo("Download Fermato", 
                                      f"Download playlist fermato.\n\n"
                                      f"{completed}/{total} video scaricati.",
                                      parent=self)
                
                elif typ == "playlist_error":
                    error_msg = payload
                    log(f"❌ Errore playlist: {error_msg}")
                    self.btn_download.configure(state="disabled")
                    
                    # Se è l'errore ['maximum'], mostra un messaggio più soft
                    if "'maximum'" in error_msg and "are not supported arguments" in error_msg:
                        self.status.set("⚠️ Playlist trovata ma con formato non completamente supportato.")
                        messagebox.showwarning("Attenzione", 
                            "La playlist è stata trovata ma potrebbe non essere completamente compatibile.\n"
                            "Alcune informazioni potrebbero mancare. Puoi comunque provare a scaricare i video.",
                            parent=self)
                    else:
                        self.status.set("❌ Errore nel recupero della playlist")
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
        self.title("Il Mangia's MUSIC WAVVER - V.4.0") 
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
        
        log(f"🚀 GUI avviata. Versione: MUSIC WAVVER 4.0")

        self._build_ui()
        self.after(150, self._loop)
        log("🟢 Ciclo eventi avviato")

    def _set_icon(self):
        try:
            current_os = platform.system()
            if current_os == "Windows" and os.path.exists("logo.ico"):
                self.iconbitmap("logo.ico")
            elif current_os == "Linux" and os.path.exists("logo.png"):
                # Su Linux usa PNG
                img = PhotoImage(file="logo.png")
                self.iconphoto(True, img)
            elif os.path.exists("logo.ico"):
                # Fallback per Windows o altri OS con supporto .ico
                self.iconbitmap("logo.ico")
        except Exception as e:
            log(f"⚠️ Impossibile impostare icona: {e}")
            # Workaround per Windows AppUserModelID
            if platform.system() == "Windows":
                try:
                    import ctypes
                    myappid = 'ilmangia.musicwavver.4.0'
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                except:
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
        
        # Aggiunta colonna "Score" per visualizzare il matching score
        cols = ("Titolo", "Uploader", "Durata", "Score", "Status")
        self.tree = Treeview(tree_frame, columns=cols, show="headings", height=14)
        
        # Configurazione tag per diversi stati
        self.tree.tag_configure('best_match', background='#d4edda', foreground='#155724')  # Verde chiaro
        self.tree.tag_configure('good_match', background='#fff3cd', foreground='#856404')  # Giallo chiaro
        self.tree.tag_configure('no_match', background='#f8f9fa', foreground='#6c757d')  # Grigio chiaro
        self.tree.tag_configure('downloading_tag', background='#3B8ED0', foreground='white')
        
        self.tree.column("Titolo", width=350, anchor="w")
        self.tree.column("Uploader", width=120, anchor="w")
        self.tree.column("Durata", width=80, anchor="center")
        self.tree.column("Score", width=60, anchor="center")
        self.tree.column("Status", width=80, anchor="center")

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
        win.title(T("playlist_prompt_title"))
        win.geometry("400x150")
        win.transient(self)
        
        try:
            current_os = platform.system()
            if current_os == "Windows" and os.path.exists("logo.ico"):
                win.iconbitmap("logo.ico")
            elif current_os == "Linux" and os.path.exists("logo.png"):
                img = PhotoImage(file="logo.png")
                win.iconphoto(True, img)
            elif os.path.exists("logo.ico"):
                win.iconbitmap("logo.ico")
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

    def _search_thread(self, q, maxr):
        try:
            # Cerca su YouTube e Deezer simultaneamente
            results = search_youtube(q, max_results=maxr, timeout_seconds=SETTINGS["search_timeout"], deezer_tagger=self.deezer_tagger)
            self.results = results
            
            # Trova il miglior match tra tutti i risultati
            best_match_index = -1
            best_match_score = -1
            
            for i, r in enumerate(results):
                if r.get("deezer_match"):
                    score = r["deezer_match"].get("score", 0)
                    if score > best_match_score:
                        best_match_score = score
                        best_match_index = i
            
            # Aggiorna l'albero dei risultati
            self.tree.delete(*self.tree.get_children())
            
            for i, r in enumerate(results):
                duration_sec = r.get("duration")
                if isinstance(duration_sec, int):
                    minutes, seconds = divmod(duration_sec, 60)
                    hours, minutes = divmod(minutes, 60)
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}" if hours > 0 else f"{minutes:02d}:{seconds:02d}"
                else:
                    duration_str = str(duration_sec)
                
                # Determina il titolo da mostrare
                if r.get("deezer_match"):
                    deezer_match = r["deezer_match"]
                    score = deezer_match.get("score", 0)
                    # SEMPRE mostra il titolo originale YouTube (sporco)
                    display_title = r["title"]  # Sempre titolo YouTube originale
                    score_str = f"{score}/100"
                    has_good_duration = False
                    if r.get("duration") and r.get("deezer_match", {}).get("duration"):
                        youtube_dur = int(r["duration"])
                        deezer_dur = int(r["deezer_match"]["duration"])
                        if abs(youtube_dur - deezer_dur) <= 10:  # Differenza massima 10 secondi
                            has_good_duration = True
                        if score >= 40:
                            if has_good_duration:
                                status = "✅⏱️"  # Buon match + durata corretta
                            else:
                                status = "✅"     # Buon match ma durata non perfetta
                        else:
                            if has_good_duration:
                                status = "⚠️⏱️"  # Match mediocre ma durata corretta
                            else:
                                status = "⚠️"   # Match mediocre e durata non perfetta
                    else:
                        if has_good_duration:
                            status = "⚠️⏱️"  # Match mediocre ma durata corretta
                        else:
                            status = "⚠️"   
                else:
                    display_title = r["title"]  # Titolo originale YouTube
                    score_str = "N/A"
                    status = "❌"
                
                # Determina il tag da applicare
                if i == best_match_index and best_match_score >= 40:
                    tag = 'best_match'
                elif r.get("deezer_match") and r["deezer_match"].get("score", 0) >= 30:
                    tag = 'good_match'
                else:
                    tag = 'no_match'
                
                # Inserisci nel treeview
                item_id = self.tree.insert("", "end", 
                                          values=(display_title, r["uploader"], duration_str, score_str, status),
                                          tags=(tag,))
            
            self.status.set(f"{len(results)} risultati trovati. Miglior match: {best_match_score}/100" if best_match_score > 0 else f"{len(results)} risultati trovati.")
            
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
            
        threading.Thread(target=self._download_thread, args=(url, self.format.get(), sel, index), daemon=True).start()

    def _download_thread(self, url, fmt, tree_item_id, result_index):
        try:
            def update_progress(p):
                self.queue.put(("progress", p))
            
            download_with_yt_dlp(url, fmt, SETTINGS["download_dir"], SETTINGS["speed_limit"], progress_cb=update_progress)
            
            # Dopo il download, verifica se dobbiamo gestire ID3 tag
            global LAST_FILE
            if fmt == "mp3" and SETTINGS.get("write_id3", False) and LAST_FILE and os.path.exists(LAST_FILE):
                # Controlla se abbiamo un match Deezer per questo risultato
                result = self.results[result_index]
                if result.get("deezer_match"):
                    # Usa i metadati Deezer del match trovato
                    deezer_match = result["deezer_match"]
                    
                    # Scarica copertina
                    cover_data = self.deezer_tagger.download_cover(deezer_match.get("cover_url", ""))
                    
                    # Applica tag ID3
                    metadata = {
                        "title": deezer_match.get("title", ""),
                        "artist": deezer_match.get("artist", ""),
                        "album": deezer_match.get("album", ""),
                        "year": deezer_match.get("year", ""),
                        "genre": deezer_match.get("genre", ""),
                        "track_number": str(deezer_match.get("track_number", ""))
                    }
                    
                    success = self.deezer_tagger.apply_id3_tags(LAST_FILE, metadata, cover_data)
                    
                    if success:
                        self.queue.put(("id3_done", (tree_item_id, deezer_match.get("score", 0))))
                    else:
                        self.queue.put(("id3_failed", tree_item_id))
                else:
                    # Prova ricerca automatica come fallback
                    success = apply_deezer_id3_automatically(self, os.path.basename(LAST_FILE), LAST_FILE, self.deezer_tagger)
                    if success:
                        self.queue.put(("id3_done", (tree_item_id, 0)))
                    else:
                        self.queue.put(("id3_failed", tree_item_id))
            else:
                self.queue.put(("done", tree_item_id))
                
        except Exception as e:
            self.queue.put(("error", str(e)))

    def play_file(self):
        global LAST_FILE
        if LAST_FILE and os.path.exists(LAST_FILE):
            try:
                system = platform.system()
                if system == "Windows":
                    os.startfile(LAST_FILE)
                elif system == "Darwin":  # macOS
                    subprocess.call(["open", LAST_FILE])
                else:  # Linux
                    # Prova diversi metodi per Linux
                    try:
                        subprocess.call(["xdg-open", LAST_FILE])
                    except:
                        # Fallback: usa altre applicazioni
                        try:
                            subprocess.call(["gio", "open", LAST_FILE])
                        except:
                            try:
                                subprocess.call(["exo-open", LAST_FILE])
                            except:
                                # Ultimo tentativo
                                subprocess.call(["xdg-open", LAST_FILE], shell=True)
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
            current_os = platform.system()
            if current_os == "Windows" and os.path.exists("logo.ico"):
                win.iconbitmap("logo.ico")
            elif current_os == "Linux" and os.path.exists("logo.png"):
                img = PhotoImage(file="logo.png")
                win.iconphoto(True, img)
            elif os.path.exists("logo.ico"):
                win.iconbitmap("logo.ico")
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
        win.title(T("settings_title"))
        win.geometry("540x500")  # Ridotta altezza, ora scrollabile
        win.transient(self)
        
        try:
            current_os = platform.system()
            if current_os == "Windows" and os.path.exists("logo.ico"):
                win.iconbitmap("logo.ico")
            elif current_os == "Linux" and os.path.exists("logo.png"):
                img = PhotoImage(file="logo.png")
                win.iconphoto(True, img)
            elif os.path.exists("logo.ico"):
                win.iconbitmap("logo.ico")
        except Exception:
            pass

        # Frame principale scrollabile
        main_frame = ctk.CTkFrame(win)
        main_frame.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Canvas per lo scroll
        canvas = ctk.CTkCanvas(main_frame)
        scrollbar = ctk.CTkScrollbar(main_frame, orientation="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Grid per organizzare il layout
        canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        main_frame.grid_rowconfigure(0, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Contenuto scrollabile
        scrollable_frame.grid_columnconfigure(0, weight=1)
        
        row_counter = 0
        
        # Directory download
        ctk.CTkLabel(scrollable_frame, text=T("download_folder_label"), font=("Segoe UI", 14, "bold")).grid(
            row=row_counter, column=0, sticky="w", pady=(20, 5), padx=20
        )
        row_counter += 1
        
        dir_frame = ctk.CTkFrame(scrollable_frame)
        dir_frame.grid(row=row_counter, column=0, sticky="ew", padx=20, pady=(0, 10))
        dir_frame.grid_columnconfigure(0, weight=1)
        row_counter += 1
        
        self.dir_label = ctk.CTkLabel(dir_frame, text=SETTINGS["download_dir"], wraplength=480)
        self.dir_label.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        ctk.CTkButton(dir_frame, text=T("change_folder"), command=lambda: self.change_dir(win), width=80).grid(row=0, column=1, padx=10, pady=8)
        
        # Qualità audio MP3
        ctk.CTkLabel(scrollable_frame, text="Qualità Audio MP3", font=("Segoe UI", 14, "bold")).grid(
            row=row_counter, column=0, sticky="w", pady=(20, 5), padx=20
        )
        row_counter += 1
        
        self.quality_var = ctk.StringVar(value=SETTINGS.get("audio_quality", "320"))
        quality_combo = ctk.CTkComboBox(scrollable_frame, variable=self.quality_var, 
                                      values=["128", "192", "256", "320"], state="readonly")
        quality_combo.grid(row=row_counter, column=0, sticky="ew", padx=20, pady=5)
        row_counter += 1
        
        # Lingua
        ctk.CTkLabel(scrollable_frame, text=T("language_label"), font=("Segoe UI", 14, "bold")).grid(
            row=row_counter, column=0, sticky="w", pady=(20, 5), padx=20
        )
        row_counter += 1
        
        self.lang_var = ctk.StringVar(value=SETTINGS.get("language", "it"))
        lang_combo = ctk.CTkComboBox(scrollable_frame, variable=self.lang_var, values=["it", "en", "es", "de"], state="readonly")
        lang_combo.grid(row=row_counter, column=0, sticky="ew", padx=20, pady=5)
        row_counter += 1
        
        # Tema
        ctk.CTkLabel(scrollable_frame, text=T("theme_label"), font=("Segoe UI", 14, "bold")).grid(
            row=row_counter, column=0, sticky="w", pady=(20, 5), padx=20
        )
        row_counter += 1
        
        self.theme_var = ctk.StringVar(value=SETTINGS.get("theme", "system"))
        theme_combo = ctk.CTkComboBox(scrollable_frame, variable=self.theme_var, values=["system", "dark", "light"], state="readonly")
        theme_combo.grid(row=row_counter, column=0, sticky="ew", padx=20, pady=5)
        row_counter += 1
        
        # ID3 Tag
        ctk.CTkLabel(scrollable_frame, text="ID3 Tag", font=("Segoe UI", 14, "bold")).grid(
            row=row_counter, column=0, sticky="w", pady=(20, 5), padx=20
        )
        row_counter += 1
        
        self.id3_var = ctk.BooleanVar(value=SETTINGS.get("write_id3", False))
        id3_check = ctk.CTkCheckBox(scrollable_frame, text=T("id3_enable_label"), variable=self.id3_var, 
                                   checkbox_width=20, checkbox_height=20)
        id3_check.grid(row=row_counter, column=0, sticky="w", padx=20, pady=5)
        row_counter += 1
        
        # Limitazione velocità
        ctk.CTkLabel(scrollable_frame, text=T("speed_limit_label"), font=("Segoe UI", 14, "bold")).grid(
            row=row_counter, column=0, sticky="w", pady=(20, 5), padx=20
        )
        row_counter += 1
        
        self.speed_var = ctk.StringVar(value=SETTINGS.get("speed_limit", "0"))
        speed_entry = ctk.CTkEntry(scrollable_frame, textvariable=self.speed_var)
        speed_entry.grid(row=row_counter, column=0, sticky="ew", padx=20, pady=5)
        row_counter += 1
        
        # Timeout ricerca
        ctk.CTkLabel(scrollable_frame, text=T("search_timeout_label"), font=("Segoe UI", 14, "bold")).grid(
            row=row_counter, column=0, sticky="w", pady=(20, 5), padx=20
        )
        row_counter += 1
        
        self.timeout_var = ctk.StringVar(value=str(SETTINGS.get("search_timeout", 30)))
        timeout_entry = ctk.CTkEntry(scrollable_frame, textvariable=self.timeout_var)
        timeout_entry.grid(row=row_counter, column=0, sticky="ew", padx=20, pady=5)
        row_counter += 1
        
        # Pulsante salva
        ctk.CTkButton(scrollable_frame, text=T("save_settings"), command=lambda: self.save_settings(win), 
                     fg_color="#28a745", hover_color="#218838", height=40).grid(
            row=row_counter, column=0, sticky="ew", padx=20, pady=20
        )
        row_counter += 1
        
        # Aggiungi spazio finale
        ctk.CTkLabel(scrollable_frame, text="").grid(row=row_counter, column=0, pady=10)
        
        # Imposta l'altezza del canvas
        win.update_idletasks()
        canvas_height = min(500, scrollable_frame.winfo_reqheight())
        canvas.configure(height=canvas_height)

    def change_dir(self, parent_win):
        d = filedialog.askdirectory(initialdir=SETTINGS["download_dir"], title=T("select_download_folder"))
        if d:
            SETTINGS["download_dir"] = d
            self.dir_label.configure(text=d)
            save_settings()

    def save_settings(self, win):
        SETTINGS["language"] = self.lang_var.get()
        SETTINGS["theme"] = self.theme_var.get()
        SETTINGS["write_id3"] = self.id3_var.get()
        SETTINGS["audio_quality"] = self.quality_var.get()
        SETTINGS["speed_limit"] = self.speed_var.get().strip() or "0"
        
        try:
            SETTINGS["search_timeout"] = int(self.timeout_var.get())
        except ValueError:
            SETTINGS["search_timeout"] = 30
            
        save_settings()
        ctk.set_appearance_mode(SETTINGS["theme"])
        messagebox.showinfo("Impostazioni", "Impostazioni salvate con successo!", parent=win)
        win.destroy()

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
                    # Avvia timer per reset UI dopo 5 secondi
                    self.after(5000, self.reset_ui)
                
                elif typ == "id3_done":
                    item_id, score = payload
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
                    
                    if score > 0:
                        messagebox.showinfo("Metadati Applicati", 
                                          f"Tag ID3 applicati con successo!\nScore matching: {score}/100")
                    
                    # Avvia timer per reset UI dopo 5 secondi
                    self.after(5000, self.reset_ui)
                
                elif typ == "id3_failed":
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
                    
                    # Avvia timer per reset UI dopo 5 secondi
                    self.after(5000, self.reset_ui)
                
                elif typ == "error":
                    self.downloading = False
                    self.lock_ui(False)
                    messagebox.showerror("Errore", payload)
                    self.after(5000, self.reset_ui)
                
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
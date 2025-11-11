#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA - 11/11/2025 (Aggiornato e Corretto)
MUSIC WAVVER 2.7 - YouTube Downloader avanzato con GUI ttkbootstrap
MADE IN ITALY 🇮🇹 -
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
import concurrent.futures #[NUOVO] Per download paralleli
from urllib.parse import urlparse, parse_qs
from datetime import datetime
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
# Importa in modo difensivo le classi
from ttkbootstrap.dialogs import Messagebox
# NON importare da ttkbootstrap.treeview. Il widget è ttk.Treeview stilizzato.
from tkinter.ttk import Treeview 
from yt_dlp import YoutubeDL

# ---------------------- LOGGING ----------------------
LOG_FILE = "ytdownloader.log"
SETTINGS_FILE = "settings.json"

try:
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.truncate(0)
except Exception:
    pass

# Imposta il formato del logging (già dettagliato)
logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

def log(msg):
    # Aggiunge la stampa su console per debug in tempo reale
    print(msg)
    try:
        logging.info(msg)
    except Exception:
        pass

# ---------------------- DEFAULT SETTINGS ----------------------
DEFAULT_SETTINGS = {
    "download_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
    "theme": "superhero",
    "speed_limit": "0",
    "search_timeout": 15,
    "agreement_accepted": False,
    "language": "it",
    "last_update_check": "1970-01-01T00:00:00", #[NUOVO] Per updater
    "concurrent_playlist_downloads": 4, #[NUOVO] Download paralleli
}

# ---------------------- LINGUE ----------------------
LANG = {
    "it": {
        "welcome": "Benvenuto in MUSIC WAVVER",
        "search_btn": "🔍 Cerca / Incolla link",
        "download_btn": "⬇️ Download selezionato",
        "play_btn": "🎵 Riproduci",
        "searching": "Ricerca in corso...",
        "ready": "Pronto",
        "complete": "✅ Download completato",
        "complete_msg": "Download terminato con successo!",
        "settings": "⚙️ Impostazioni",
        "open_log": "🧾 Apri log",
        "agreement_title": "Accordo legale",
        "agreement_text": (
            "⚠️ ACCORDO LEGALE ⚠️\n\n"
            "Utilizzando questo programma ('MUSIC WAVVER'), dichiari di essere l'unico responsabile "
            "dell'uso che ne fai. L'autore ('Il Mangia') non è responsabile per l'uso improprio, "
            "incluso la violazione dei diritti d'autore o dei Termini di Servizio di YouTube.\n\n"
            "Software solo per uso personale e didattico.\n\n"
            "Premi 'Accetto' per continuare."
        ),
        "agreement_close": "Non hai accettato l'accordo. Il programma verrà chiuso.",
        # Stringhe Playlist
        "playlist_title": "Playlist Downloader",
        "playlist_select_dir": "📁 Cartella download (Temporanea/Playlist)",
        "playlist_download_btn": "▶️ Scarica playlist",
        "playlist_status_fetching": "Recupero video della playlist...",
        "playlist_status_downloading": "Scaricando {current} video in parallelo... ({done}/{total} completati)", #[MODIFICATO]
        "playlist_status_complete": "✅ Playlist completata",
        "playlist_prompt_title": "Playlist Rilevata",
        "playlist_prompt_text": "Hai incollato un link contenente una playlist. Cosa vuoi scaricare?",
        "playlist_prompt_single": "Solo il video in riproduzione",
        "playlist_prompt_full": "Intera playlist",
        "playlist_prompt_error_no_v": "L'URL è solo una playlist. Avvio download playlist...",
        "playlist_error_no_videos": "Impossibile trovare video validi nella playlist.",
        # [NUOVO] Stringhe Updater
        "updater_title": "Aggiornamento yt-dlp",
        "updater_prompt_title": "Aggiornamento Consigliato",
        "updater_prompt_text": "Sono passati più di 3 giorni dall'ultimo controllo.\n\nVuoi aggiornare `yt-dlp` ora? (Consigliato per evitare errori di download)",
        "updater_running": "Aggiornamento `yt-dlp` in corso...",
        "updater_log_title": "Log Aggiornamento",
        "updater_success": "Aggiornamento completato con successo!",
        "updater_fail": "Aggiornamento fallito. Controlla il log.",
        "updater_skipped": "Aggiornamento saltato dall'utente.",
        "updater_not_needed": "yt-dlp è già aggiornato. Nessun controllo necessario.",
    },
    "en": {
        "welcome": "Welcome to MUSIC WAVVER",
        "search_btn": "🔍 Search / Paste link",
        "download_btn": "⬇️ Download selected",
        "play_btn": "🎵 Play",
        "searching": "Searching...",
        "ready": "Ready",
        "complete": "✅ Download complete",
        "complete_msg": "Download finished successfully!",
        "settings": "⚙️ Settings",
        "open_log": "🧾 Open log",
        "agreement_title": "Legal Agreement",
        "agreement_text": (
            "⚠️ LEGAL AGREEMENT ⚠️\n\n"
            "By using this software ('MUSIC WAVVER'), you acknowledge you are solely responsible for its use. "
            "The author ('Il Mangia') is not responsible for any misuse, including copyright violations.\n\n"
            "Personal and educational use only.\n\n"
            "Press 'Accept' to continue."
        ),
        "agreement_close": "You declined the agreement. The program will close.",
        # New strings for Playlist
        "playlist_title": "Playlist Downloader",
        "playlist_select_dir": "📁 Download Folder (Temporary/Playlist)",
        "playlist_download_btn": "▶️ Download Playlist",
        "playlist_status_fetching": "Fetching playlist videos...",
        "playlist_status_downloading": "Downloading {current} videos in parallel... ({done}/{total} complete)", #[MODIFIED]
        "playlist_status_complete": "✅ Playlist Complete",
        "playlist_prompt_title": "Playlist Detected",
        "playlist_prompt_text": "You pasted a link containing a playlist. What do you want to download?",
        "playlist_prompt_single": "Only the currently playing video",
        "playlist_prompt_full": "Entire playlist",
        "playlist_prompt_error_no_v": "The URL is only a playlist. Starting playlist download...",
        "playlist_error_no_videos": "Could not find valid videos in the playlist.",
        # [NEW] Updater strings
        "updater_title": "yt-dlp Updater",
        "updater_prompt_title": "Update Recommended",
        "updater_prompt_text": "It has been more than 3 days since the last check.\n\nDo you want to update `yt-dlp` now? (Recommended to prevent download errors)",
        "updater_running": "Updating `yt-dlp`...",
        "updater_log_title": "Update Log",
        "updater_success": "Update completed successfully!",
        "updater_fail": "Update failed. Check the log.",
        "updater_skipped": "Update skipped by user.",
        "updater_not_needed": "yt-dlp is up-to-date. No check needed.",
    },
    # Aggiungere traduzioni per 'es' e 'de' se necessario...
    "es": {
        "welcome": "Bienvenido a MUSIC WAVVER",
        "search_btn": "🔍 Buscar / Pegar enlace",
        "download_btn": "⬇️ Descargar seleccionado",
        "play_btn": "🎵 Reproducir",
        "searching": "Buscando...",
        "ready": "Listo",
        "complete": "✅ Descarga completada",
        "complete_msg": "¡Descarga finalizada correctamente!",
        "settings": "⚙️ Configuración",
        "open_log": "🧾 Abrir registro",
        "agreement_title": "Acuerdo Legal",
        "agreement_text": (
            "⚠️ ACUERDO LEGAL ⚠️\n\n"
            "Al usar este programa ('MUSIC WAVVER'), reconoces que eres el único responsable de su uso. "
            "El autor ('Il Mangia') no se hace responsible de un uso indebido ni de violaciones de derechos.\n\n"
            "Solo para uso personal y educativo.\n\n"
            "Presiona 'Aceptar' para continuar."
        ),
        "agreement_close": "No aceptaste el acuerdo. El programa se cerrará.",
        # Nuevas cadenas para Playlist
        "playlist_title": "Descargador de Listas de Reproducción",
        "playlist_select_dir": "📁 Carpeta de descarga (Temporal/Lista)",
        "playlist_download_btn": "▶️ Descargar lista",
        "playlist_status_fetching": "Obteniendo videos de la lista...",
        "playlist_status_downloading": "Descargando {current} videos en paralelo... ({done}/{total} completados)", #[MODIFICATO]
        "playlist_status_complete": "✅ Lista de Reproducción Completa",
        "playlist_prompt_title": "Lista de Reproducción Detectada",
        "playlist_prompt_text": "¿Qué quieres descargar?",
        "playlist_prompt_single": "Solo el video actual",
        "playlist_prompt_full": "Lista completa",
        "playlist_prompt_error_no_v": "El URL es solo una lista. Iniciando descarga...",
        "playlist_error_no_videos": "No se encontraron videos válidos en la lista.",
        # [NUEVO] Cadenas de actualización
        "updater_title": "Actualizador yt-dlp",
        "updater_prompt_title": "Actualización Recomendada",
        "updater_prompt_text": "Han pasado más de 3 días desde la última comprobación.\n\n¿Quieres actualizar `yt-dlp` ahora? (Recomendado para evitar errores de descarga)",
        "updater_running": "Actualizando `yt-dlp`...",
        "updater_log_title": "Registro de Actualización",
        "updater_success": "¡Actualización completada con éxito!",
        "updater_fail": "Actualización fallida. Revisa el registro.",
        "updater_skipped": "Actualización omitida por el usuario.",
        "updater_not_needed": "yt-dlp está actualizado. No se necesita comprobación.",
    },
    "de": {
        "welcome": "Willkommen bei MUSIC WAVVER",
        "search_btn": "🔍 Suchen / Link einfügen",
        "download_btn": "⬇️ Auswahl herunterladen",
        "play_btn": "🎵 Abspielen",
        "searching": "Suche läuft...",
        "ready": "Bereit",
        "complete": "✅ Download abgeschlossen",
        "complete_msg": "Download erfolgreich beendet!",
        "settings": "⚙️ Einstellungen",
        "open_log": "🧾 Log öffnen",
        "agreement_title": "Rechtliche Vereinbarung",
        "agreement_text": (
            "⚠️ RECHTLICHE VEREINBARUNG ⚠️\n\n"
            "Durch die Nutzung dieses Programms erklärst du dich allein verantwortlich für dessen Verwendung. "
            "Der Autor ('Il Mangia') haftet nicht für Missbrauch oder Urheberrechtsverletzungen.\n\n"
            "Nur für persönliche und schulische Nutzung.\n\n"
            "Klicke auf 'Akzeptieren', um fortzufahren."
        ),
        "agreement_close": "Du hast die Vereinbarung abgelehnt. Das Programm wird geschlossen.",
        # Neue Zeichenketten für Playlist
        "playlist_title": "Playlist Downloader",
        "playlist_select_dir": "📁 Download-Ordner (Temporär/Playlist)",
        "playlist_download_btn": "▶️ Playlist herunterladen",
        "playlist_status_fetching": "Playlist-Videos abrufen...",
        "playlist_status_downloading": "{current} Videos werden parallel heruntergeladen... ({done}/{total} abgeschlossen)", #[MODIFIZIERT]
        "playlist_status_complete": "✅ Playlist abgeschlossen",
        "playlist_prompt_title": "Playlist erkannt",
        "playlist_prompt_text": "Sie haben einen Link mit einer Playlist eingefügt. Was möchten Sie herunterladen?",
        "playlist_prompt_single": "Nur das aktuell spielende Video",
        "playlist_prompt_full": "Ganze Playlist",
        "playlist_prompt_error_no_v": "Die URL ist nur eine Playlist. Starte Playlist-Download...",
        "playlist_error_no_videos": "Es konnten keine gültigen Videos in der Playlist gefunden werden.",
        # [NEU] Updater-Strings
        "updater_title": "yt-dlp Updater",
        "updater_prompt_title": "Update empfohlen",
        "updater_prompt_text": "Seit der letzten Überprüfung sind mehr als 3 Tage vergangen.\n\nMöchten Sie `yt-dlp` jetzt aktualisieren? (Empfohlen, um Download-Fehler zu vermeiden)",
        "updater_running": "Update `yt-dlp`...",
        "updater_log_title": "Update-Protokoll",
        "updater_success": "Update erfolgreich abgeschlossen!",
        "updater_fail": "Update fehlgeschlagen. Überprüfen Sie das Protokoll.",
        "updater_skipped": "Update vom Benutzer übersprungen.",
        "updater_not_needed": "yt-dlp ist auf dem neuesten Stand. Keine Überprüfung erforderlich.",
    }
}


# ---------------------- SETTINGS ----------------------
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                # Mantengo solo le chiavi valide
                valid_settings = {k: v for k, v in s.items() if k in DEFAULT_SETTINGS}
                DEFAULT_SETTINGS.update(valid_settings)
        except Exception as e:
            log(f"⚠️ Errore leggendo settings.json: {e}")
    return DEFAULT_SETTINGS

def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, indent=4)

SETTINGS = load_settings()
T = LANG.get(SETTINGS.get("language", "it"), LANG["it"])

# ---------------------- ACCORDO LEGALE ----------------------
def show_agreement():
    root = tk.Tk()
    root.withdraw()
    text = T["agreement_text"]
    # Utilizzo Messagebox di Tkinter come fallback
    accept = messagebox.askyesno(T["agreement_title"], text)
    root.destroy()
    if accept:
        SETTINGS["agreement_accepted"] = True
        save_settings()
        return True
    else:
        messagebox.showinfo(T["agreement_title"], T["agreement_close"])
        return False

# ---------------------- FFMPEG ----------------------
def detect_ffmpeg():
    base = os.path.dirname(os.path.abspath(sys.argv[0]))
    sys_os = platform.system().lower()
    candidate = os.path.join(base, "ffmpeg", "win", "ffmpeg.exe") if "win" in sys_os else os.path.join(base, "ffmpeg", "linux", "ffmpeg")

    if not os.path.exists(candidate):
        log("⚠️ ffmpeg locale non trovato, controllo presenza globale...")
        found = shutil.which("ffmpeg")
        if found:
            log(f"✅ ffmpeg globale trovato: {found}")
            log(f"FFmpeg path rilevato: {found}")
            return found
        else:
            messagebox.showerror("ffmpeg", f"ffmpeg non trovato né localmente né nel PATH.\nPercorso cercato:\n{candidate}")
            sys.exit(1)
    os.environ["PATH"] = os.path.dirname(candidate) + os.pathsep + os.environ.get("PATH", "")
    log(f"FFmpeg path rilevato (locale): {candidate}")
    return candidate

FFMPEG_PATH = detect_ffmpeg()

# ---------------------- UTILITY ----------------------
def is_playlist(url):
    """Controlla se l'URL è un link di playlist o di riproduzione con lista."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    
    # Caso 1: È un link playlist diretto
    if "playlist" in parsed.path:
        log("🔍 Rilevato URL come link playlist diretto.")
        return True

    # Caso 2: È un link watch con parametro list=
    if "list" in query_params:
        log(f"🔍 Rilevato URL con parametro list={query_params['list'][0]}")
        return True
    
    return False

def extract_video_id(url):
    """Estrae l'ID del video se presente (utile per il download singolo)."""
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)
    if "v" in query_params:
        return query_params["v"][0]
    # Gestione formati brevi come youtu.be/id
    match = re.search(r'(youtu\.be\/|v=)([a-zA-Z0-9_-]{11})', url)
    if match:
        return match.group(2)
    return None

# ---------------------- RICERCA ----------------------
def _yt_search_worker(query, max_results, result_queue):
    log(f"🔎 Avvio ricerca - Query: '{query}', Max risultati: {max_results}")
    try:
        # Se è un URL, imposto default_search a 'auto' per consentire il parsing diretto
        is_url = query.startswith("http")
        search_term = query if not is_url else query
        
        opts = {"quiet": True, "extract_flat": True, "skip_download": True, "default_search": "ytsearch"}
        if is_url:
            # Per url, yt-dlp gestirà l'estrazione, non vogliamo la ricerca.
            opts["default_search"] = "auto"
        
        # Aggiungo limite di ricerca se non è un URL
        search_query = f"ytsearch{max_results}:{query}" if not is_url else query

        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search_query, download=False)
            
            # Se è una ricerca, gestiamo l'array di risultati.
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
            # Se è un URL singolo, ritorniamo un array di 1 elemento per coerenza
            elif info.get("id"):
                results = [{
                    "title": info.get("title", "Sconosciuto"),
                    "url": info.get("webpage_url", query),
                    "duration": info.get("duration", "N/D"),
                    "uploader": info.get("uploader", "Sconosciuto")
                }]
                log("✅ Info URL singolo estratta.")
                result_queue.put(("ok", results))
            else:
                log("⚠️ Nessun risultato trovato per l'URL.")
                result_queue.put(("ok", []))

    except Exception as ex:
        log(f"❌ Errore durante la ricerca/estrazione info: {ex}")
        result_queue.put(("err", str(ex)))

def search_youtube(query, max_results=10, timeout_seconds=15):
    rq = queue.Queue()
    # Uso solo l'ID del video se l'URL è di riproduzione, per evitare risultati multipli dalla ricerca
    video_id = extract_video_id(query)
    
    if video_id and query.startswith("http"):
        # Se è un URL con ID video, cerco solo le info di quell'ID
        query_to_search = f"https://www.youtube.com/watch?v={video_id}"
    else:
        # Altrimenti è una ricerca per parole chiave
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
    
    # Nomenclatura standard per download singolo: Titolo.ext
    outtmpl = os.path.join(out_dir, "%(title)s.%(ext)s")
    
    log(f"⬇️ Avvio download singolo - URL: {url}, Formato: {fmt}, Cartella: {out_dir}, Limite velocità: {speed_limit}")

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

    # #[MODIFICATO] Aggiunta gestione metadati
    postprocessors = [
        {"key":"FFmpegExtractAudio","preferredcodec": fmt,"preferredquality": "320"},
        {"key": "EmbedMetadata", "add_metadata": True}
    ]
    
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True, # Essenziale per forzare il download singolo
        "ffmpeg_location": os.path.dirname(FFMPEG_PATH),
        "postprocessors": postprocessors,
        # Setta solo Titolo e Album (mappa Uploader su Album)
        "postprocessor_args": {
            'metadata': 'title="%(title)s", album="%(uploader)s"'
        },
        "progress_hooks": [hook],
    }
    
    if speed_limit != "0":
        ydl_opts["ratelimit"] = speed_limit
        
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            LAST_FILE = ydl.prepare_filename(info).rsplit(".",1)[0] + f".{fmt}"
        
        log(f"✅ Download singolo completato. File salvato in: {LAST_FILE}")
        return True
    except Exception as e:
        log(f"❌ Errore critico durante il download singolo: {e}")
        raise e

# ---------------------- PLAYLIST DOWNLOADER UI ----------------------
# #[MODIFICATO] Classe quasi interamente riscritta per download concorrenti
class PlaylistDownloader(ttk.Toplevel):
    def __init__(self, master, url):
        super().__init__(master)
        self.title(T["playlist_title"])
        self.geometry("800x600")
        self.transient(master)
        self.grab_set()

        self.playlist_url = url
        self.playlist_videos = []
        self.downloading = False
        self.current_video_index = 0
        
        # [NUOVO] Variabili per download concorrente
        self.download_lock = threading.Lock()
        self.completed_count = 0
        self.workers = SETTINGS.get("concurrent_playlist_downloads", 4)

        self.download_dir = tk.StringVar(value=SETTINGS["download_dir"])
        self.format = tk.StringVar(value="wav")
        self.status = tk.StringVar(value=T["playlist_status_fetching"])
        self.overall_progress_text = tk.StringVar(value="")
        # [NUOVO] Progresso generale, non più per singolo video
        self.overall_progress_value = tk.DoubleVar(value=0)

        log(f"🆕 Avvio PlaylistDownloader per URL: {url} (Max {self.workers} workers)")

        self._build_ui()
        threading.Thread(target=self._search_playlist_thread, daemon=True).start()
        self._loop()

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # Cartella download
        ttk.Label(frm, text=T["playlist_select_dir"], font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(4, 2))
        dir_row = ttk.Frame(frm)
        dir_row.pack(fill=X)
        ttk.Label(dir_row, textvariable=self.download_dir, wraplength=550, bootstyle=PRIMARY).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(dir_row, text="📁 Cambia", bootstyle=SECONDARY, command=self.change_dir).pack(side=LEFT, padx=6)

        ttk.Separator(frm).pack(fill=X, pady=8)

        # Risultati (Treeview)
        cols = ("#", "Titolo", "Durata", "Uploader")
        self.tree = Treeview(frm, columns=cols, show="headings", height=15)
        self.tree.column("#", width=40, anchor=CENTER)
        self.tree.column("Titolo", width=350, anchor=W)
        self.tree.column("Durata", width=80, anchor=CENTER)
        self.tree.column("Uploader", width=150, anchor=W)
        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.pack(fill=BOTH, expand=True, pady=8)
        
        # Configurazione del tag: DEVE essere sull'oggetto Treeview
        # [MODIFICATO] Aggiunti tag per "fatto" e "fallito"
        self.tree.tag_configure('downloading_tag', background=self.master.style.colors.info)
        self.tree.tag_configure('done_tag', background=self.master.style.colors.success)
        self.tree.tag_configure('failed_tag', background=self.master.style.colors.danger)


        # Controlli Download
        controls_row = ttk.Frame(frm)
        controls_row.pack(fill=X, pady=6)
        
        ttk.Label(controls_row, text="Formato:").pack(side=LEFT)
        ttk.OptionMenu(controls_row, self.format, self.format.get(), "wav", "mp3", "flac").pack(side=LEFT, padx=6)
        
        self.btn_download = ttk.Button(controls_row, text=T["playlist_download_btn"], 
                                        bootstyle=SUCCESS, command=self._start_download, state=DISABLED)
        self.btn_download.pack(side=RIGHT)

        # Stato e Progresso
        ttk.Label(frm, textvariable=self.overall_progress_text, bootstyle=INFO).pack(anchor=W, pady=(8, 2))
        # [MODIFICATO] Progress bar usa overall_progress_value
        self.progress_bar = ttk.Progressbar(frm, variable=self.overall_progress_value, length=500, bootstyle=INFO)
        self.progress_bar.pack(fill=X)
        ttk.Label(frm, textvariable=self.status, width=80).pack(anchor=W, pady=(4, 0))


    def change_dir(self):
        d = filedialog.askdirectory(initialdir=self.download_dir.get(), title=T["playlist_select_dir"])
        if d:
            self.download_dir.set(d)
            log(f"📁 Cartella download playlist aggiornata a: {d}")

    def _search_playlist_thread(self):
        try:
            log(f"🔎 Avvio ricerca video in playlist: {self.playlist_url}")
            ydl_opts = {
                "quiet": True,
                "extract_flat": "in_playlist", # Estrae info superficiali di tutti gli elementi
                "skip_download": True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(self.playlist_url, download=False)
            
            videos = []
            for entry in info.get("entries", []):
                if entry and entry.get("id"):
                    videos.append({
                        "title": entry.get("title", "Titolo Sconosciuto"),
                        "url": f"https://www.youtube.com/watch?v={entry['id']}",
                        "duration": entry.get("duration_string", "N/D"),
                        "uploader": entry.get("channel", "Sconosciuto")
                    })

            self.playlist_videos = videos
            self.tree.delete(*self.tree.get_children())
            
            if not self.playlist_videos:
                self.status.set(T["playlist_error_no_videos"])
                log("❌ Nessun video trovato nella playlist.")
                messagebox.showerror("Errore", T["playlist_error_no_videos"])
                self.btn_download.config(state=DISABLED)
                return

            for i, video in enumerate(self.playlist_videos):
                self.tree.insert("", "end", iid=i, values=(i+1, video["title"], video["duration"], video["uploader"]))

            self.status.set(f"Trovati {len(self.playlist_videos)} video. Pronto per il download.")
            self.overall_progress_text.set(f"0/{len(self.playlist_videos)} video scaricati.")
            self.btn_download.config(state=NORMAL)
            # [NUOVO] Imposta il massimo della progress bar
            self.progress_bar.config(maximum=len(self.playlist_videos))
            log(f"✅ Trovati {len(self.playlist_videos)} video nella playlist. UI abilitata.")

        except Exception as e:
            self.status.set("Errore nel recupero della playlist")
            log(f"❌ Errore critico nel recupero playlist: {e}")
            messagebox.showerror("Errore Playlist", str(e))
            self.btn_download.config(state=DISABLED)

    def _start_download(self):
        if self.downloading:
            log("⚠️ Tentativo di avviare un download playlist in corso.")
            return

        self.downloading = True
        self.completed_count = 0
        self.btn_download.config(state=DISABLED)
        self.tree.config(selectmode="none") # Blocca la selezione
        
        log(f"⬇️ Avvio thread di download playlist. {len(self.playlist_videos)} video da scaricare con {self.workers} workers.")
        threading.Thread(target=self._download_playlist_thread, daemon=True).start()

    # [NUOVO] Worker per il download del singolo video
    def _download_single_video_worker(self, video_index):
        video = self.playlist_videos[video_index]
        video_number = video_index + 1
        url = video["url"]
        title = video["title"]
        download_directory = self.download_dir.get()

        log(f"--- Avvio worker per {video_number}: '{title}' ---")
        
        # Manda messaggio alla UI per colorare la riga
        self.master.queue.put(("playlist_progress_update", (video_index, "start")))

        outtmpl = os.path.join(download_directory, f"{video_number}. %(title)s.%(ext)s")
        
        # [MODIFICATO] Aggiunta metadati con numero traccia
        postprocessors = [
            {"key":"FFmpegExtractAudio","preferredcodec": self.format.get(),"preferredquality": "320"},
            {"key": "EmbedMetadata", "add_metadata": True}
        ]

        ydl_opts = {
            "outtmpl": outtmpl,
            "format": "bestaudio/best",
            "quiet": True,
            "noplaylist": True,
            "ffmpeg_location": os.path.dirname(FFMPEG_PATH),
            "postprocessors": postprocessors,
            # Setta Titolo, Album (da uploader) e Numero Traccia
            "postprocessor_args": {
                'metadata': f'title="%(title)s", album="%(uploader)s", track="{video_number}"'
            },
        }

        speed_limit = SETTINGS["speed_limit"]
        if speed_limit != "0":
            ydl_opts["ratelimit"] = speed_limit

        try:
            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(url, download=True)
            log(f"--- ✅ Download {video_number}/{len(self.playlist_videos)} completato: {title} ---")
            self.master.queue.put(("playlist_progress_update", (video_index, "done")))
            return True

        except Exception as e:
            log(f"--- ❌ Errore download {video_number} ({title}): {e} ---")
            self.master.queue.put(("playlist_progress_update", (video_index, "failed")))
            return False
        
        finally:
            # [NUOVO] Aggiorna il contatore generale in modo thread-safe
            with self.download_lock:
                self.completed_count += 1
                current_done = self.completed_count
                total = len(self.playlist_videos)
                # Manda aggiornamento per la barra di progresso generale
                self.master.queue.put(("playlist_overall_progress", (current_done, total)))


    # [MODIFICATO] Thread principale che gestisce l'executor
    def _download_playlist_thread(self):
        total_videos = len(self.playlist_videos)
        self.completed_count = 0
        
        log(f"📁 Download playlist verso: {self.download_dir.get()}")
        self.status.set(T["playlist_status_downloading"].format(current=self.workers, done=0, total=total_videos))

        # Usa ThreadPoolExecutor per i download concorrenti
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.workers) as executor:
            # Sottomette tutti i task
            # Passiamo solo l'indice per evitare problemi con oggetti (es. Toplevel)
            futures = [executor.submit(self._download_single_video_worker, i) for i in range(total_videos)]
            
            # Attende il completamento di tutti i task
            concurrent.futures.wait(futures)

        # Tutti i download (o tentativi) sono terminati
        log(f"✅ Esecuzione ThreadPool completata. {self.completed_count} tasks processati.")
        # Manda il messaggio finale
        self.master.queue.put(("playlist_done", self.completed_count))


    def _loop(self):
        """Gestisce il loop degli eventi per la finestra della playlist."""
        try:
            while True:
                typ, payload = self.master.queue.get_nowait()
                
                if typ == "playlist_progress_update":
                    # Aggiorna il colore della riga nel treeview
                    video_index, status = payload
                    try:
                        if status == "start":
                            self.tree.tag_add('downloading_tag', video_index)
                        elif status == "done":
                            self.tree.tag_remove('downloading_tag', video_index)
                            self.tree.tag_add('done_tag', video_index)
                        elif status == "failed":
                            self.tree.tag_remove('downloading_tag', video_index)
                            self.tree.tag_add('failed_tag', video_index)
                    except Exception as e:
                        log(f"Errore aggiornamento tag treeview playlist: {e}")

                elif typ == "playlist_overall_progress":
                    # Aggiorna la barra di progresso generale
                    current_done, total = payload
                    self.overall_progress_value.set(current_done)
                    self.overall_progress_text.set(f"{current_done}/{total} video scaricati.")
                    
                    # Aggiorna status bar (per mostrare il conteggio)
                    if self.downloading:
                         self.status.set(T["playlist_status_downloading"].format(
                             current=min(self.workers, total - current_done), 
                             done=current_done, 
                             total=total
                         ))

                elif typ == "playlist_done":
                    log("✅ Gestione evento 'playlist_done'. Download playlist completato.")
                    self.status.set(T["playlist_status_complete"])
                    self.overall_progress_text.set(f"{payload}/{len(self.playlist_videos)} video scaricati con successo.")
                    self.btn_download.config(state=DISABLED)
                    self.downloading = False
                    
                    messagebox.showinfo(T["playlist_title"], T["playlist_status_complete"])
                    self.destroy()
                
                elif typ == "playlist_error":
                    log(f"❌ Gestione evento 'playlist_error'. Errore: {payload}")
                    messagebox.showerror("Errore Playlist", payload)
                
                else:
                    # Rimetto in coda gli eventi non gestiti da questa finestra
                    self.master.queue.put_nowait((typ, payload))
        except queue.Empty:
            pass
        
        # [MODIFICATO] Loop più rapido per UI più reattiva
        self.after(100, self._loop)

# ---------------------- GUI PRINCIPALE ----------------------
class YTDownloaderApp(ttk.Window):
    def __init__(self):
        super().__init__(themename=SETTINGS.get("theme", "superhero"))
        self.title("Il Mangia's MUSIC WAVVER - V.2.7") # Versione aggiornata
        self.geometry("960x620")

        self.queue = queue.Queue()
        self.results = []
        self.downloading = False
        self.query = tk.StringVar()
        self.format = tk.StringVar(value="wav")
        self.status = tk.StringVar(value=T["ready"])
        self.search_max = tk.IntVar(value=10)
        
        # Configurazione base dello stile
        self.style.configure('Treeview', rowheight=25)
        
        log(f"🚀 GUI avviata. Versione: MUSIC WAVVER 2.7, Tema: {SETTINGS.get('theme')}, Lingua: {SETTINGS.get('language')}")

        self._build_ui()
        self._loop()
        log("🟢 Ciclo eventi Tkinter avviato")
        
        # [NUOVO] Avvia il controllo aggiornamenti dopo che la GUI è partita
        self.after(500, self.check_for_updates)


    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # Top bar
        top = ttk.Frame(frm)
        top.pack(fill=X)
        ttk.Label(top, text=T["welcome"], font=("Segoe UI", 18, "bold")).pack(side=LEFT)
        ttk.Button(top, text=T["settings"], bootstyle=INFO, command=self.open_settings).pack(side=RIGHT, padx=6)
        ttk.Button(top, text=T["open_log"], bootstyle=SECONDARY, command=self.open_log).pack(side=RIGHT)

        # Search
        row1 = ttk.Frame(frm)
        row1.pack(fill=X, pady=10)
        self.entry = ttk.Entry(row1, textvariable=self.query, width=70, bootstyle=INFO)
        self.entry.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))
        self.btn_search = ttk.Button(row1, text=T["search_btn"], bootstyle=PRIMARY, command=self.on_search)
        self.btn_search.pack(side=LEFT)

        # Results (Treeview)
        cols = ("Titolo", "Uploader", "Durata")
        self.tree = Treeview(frm, columns=cols, show="headings", height=14)
        
        self.tree.tag_configure('downloading_tag', background=self.style.colors.info, foreground='white')
        
        self.tree.column("Titolo", width=400, anchor=W)
        self.tree.column("Uploader", width=150, anchor=W)
        self.tree.column("Durata", width=80, anchor=CENTER)

        for c in cols:
            self.tree.heading(c, text=c)
        self.tree.pack(fill=BOTH, expand=True, pady=8)
        self.tree.bind("<Double-1>", lambda e: self.on_download())

        # Download + format
        row2 = ttk.Frame(frm)
        row2.pack(fill=X, pady=6)
        ttk.Label(row2, text="Formato:").pack(side=LEFT)
        ttk.OptionMenu(row2, self.format, self.format.get(), "wav", "mp3", "flac").pack(side=LEFT, padx=6)
        self.btn_download = ttk.Button(row2, text=T["download_btn"], bootstyle=SUCCESS, command=self.on_download)
        self.btn_download.pack(side=LEFT, padx=8)
        self.btn_play = ttk.Button(row2, text=T["play_btn"], bootstyle=INFO, command=self.play_file, state=DISABLED)
        self.btn_play.pack(side=LEFT)

        # Progress bar
        row3 = ttk.Frame(frm)
        row3.pack(fill=X, pady=(12, 6))
        self.progress = ttk.Progressbar(row3, length=500, bootstyle=INFO)
        self.progress.pack(side=LEFT, fill=X, expand=True, padx=6)
        ttk.Label(row3, textvariable=self.status, width=50).pack(side=LEFT, padx=8)

    # ---------------------- Gestione UI ----------------------
    def lock_ui(self, state: bool):
        s = DISABLED if state else NORMAL
        log(f"🔒 UI Bloccata: {state}")
        for b in [self.btn_search, self.btn_download, self.entry]:
            b.config(state=s)

    def on_search(self):
        q = self.query.get().strip()
        if not q:
            log("⚠️ Tentativo di ricerca con query vuota.")
            return

        if q.startswith("http") and is_playlist(q):
            self.handle_playlist_prompt(q)
            return

        self.lock_ui(True)
        self.btn_play.config(state=DISABLED)
        self.status.set(T["searching"])
        log(f"🔎 Avvio thread di ricerca per: '{q}'")
        # Se non è una playlist, avvio la ricerca/estrazione normale
        threading.Thread(target=self._search_thread, args=(q, int(self.search_max.get())), daemon=True).start()

    def handle_playlist_prompt(self, url):
        video_id = extract_video_id(url)
        
        if not video_id:
            # È solo un URL di playlist (es. /playlist?list=...)
            log(T["playlist_prompt_error_no_v"])
            PlaylistDownloader(self, url)
            return

        # È un URL di riproduzione che contiene anche un parametro 'list='
        win = ttk.Toplevel(self)
        win.title(T["playlist_prompt_title"])
        win.geometry("400x150")
        win.transient(self)
        win.grab_set()

        ttk.Label(win, text=T["playlist_prompt_text"], padding=10, font=("Segoe UI", 10, "bold")).pack()

        def download_single():
            win.destroy()
            log(f"▶️ Scelta: Scarica singolo video ({video_id}).")
            self.query.set(f"https://www.youtube.com/watch?v={video_id}")
            self.on_search()

        def download_full():
            win.destroy()
            log(f"▶️ Scelta: Scarica intera playlist.")
            PlaylistDownloader(self, url)

        ttk.Button(win, text=T["playlist_prompt_single"], command=download_single, bootstyle=INFO).pack(pady=5, padx=10, fill=X)
        ttk.Button(win, text=T["playlist_prompt_full"], command=download_full, bootstyle=SUCCESS).pack(pady=5, padx=10, fill=X)

        win.protocol("WM_DELETE_WINDOW", win.destroy) # Permette la chiusura normale

    def _search_thread(self, q, maxr):
        try:
            results = search_youtube(q, max_results=maxr)
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
            log("⚠️ Tentativo di avviare un download mentre uno è già in corso.")
            return
        sel = self.tree.focus()
        if not sel:
            log("⚠️ Tentativo di download senza selezione nella treeview.")
            return
        
        index = self.tree.index(sel)
        item = self.tree.item(sel)["values"]
        title = item[0]
        url = self.results[index]["url"]
        
        self.downloading = True
        self.lock_ui(True)
        self.status.set(f"Scaricamento di {title}...")

        try:
            self.tree.tag_add('downloading_tag', sel)
        except Exception as e:
            log(f"❌ Errore critico Treeview tag_add: {e}. Continuo il download.")
            
        log(f"⬇️ Avvio thread di download singolo per '{title}' ({url})")
        threading.Thread(target=self._download_thread, args=(url, self.format.get(), sel), daemon=True).start()

    def _download_thread(self, url, fmt, tree_item_id):
        try:
            def update_progress(p):
                self.queue.put(("progress", p))
            download_with_yt_dlp(url, fmt, SETTINGS["download_dir"], SETTINGS["speed_limit"], progress_cb=update_progress)
            self.queue.put(("done", tree_item_id))
        except Exception as e:
            self.queue.put(("error", str(e)))

    def play_file(self):
        if LAST_FILE and os.path.exists(LAST_FILE):
            log(f"🎵 Tentativo di riproduzione file: {LAST_FILE}")
            
            try:
                if platform.system() == "Windows":
                    os.startfile(LAST_FILE)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", LAST_FILE])
                else:
                    subprocess.call(["xdg-open", LAST_FILE])
                log(f"✅ Comando di riproduzione inviato con successo.")
            except Exception as e:
                log(f"❌ Errore durante l'apertura del file: {e}")
                messagebox.showerror("Errore", f"Impossibile aprire il file per la riproduzione: {e}")
        else:
            log(f"⚠️ Tentativo di riproduzione fallito. LAST_FILE: {LAST_FILE}")
            messagebox.showinfo("Errore", "Nessun file da riprodurre trovato.")

    # ---------------------- Impostazioni ----------------------
    def open_settings(self):
        log("⚙️ Apertura finestra Impostazioni.")
        
        win = ttk.Toplevel(self)
        win.title("Impostazioni")
        win.geometry("540x550") # [MODIFICATO] Aumentata altezza
        win.transient(self)
        win.grab_set()

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Cartella download:", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(10, 2))
        self.dir_label = ttk.Label(frm, text=SETTINGS["download_dir"], wraplength=480, bootstyle=PRIMARY)
        self.dir_label.pack(anchor=W)
        ttk.Button(frm, text="📁 Cambia cartella", bootstyle=SECONDARY, command=self.change_dir).pack(anchor=W, pady=6)

        ttk.Separator(frm).pack(fill=X, pady=8)
        
        # [NUOVO] Impostazioni per download concorrenti
        ttk.Label(frm, text="Download playlist concorrenti:", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(8, 2))
        concurrent_entry = ttk.Entry(frm)
        concurrent_entry.insert(0, str(SETTINGS.get("concurrent_playlist_downloads", 4)))
        concurrent_entry.pack(fill=X)

        ttk.Label(frm, text="Lingua:", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(6, 2))
        lang_box = ttk.Combobox(frm, values=["it", "en", "es", "de"], state="readonly")
        lang_box.set(SETTINGS.get("language", "it"))
        lang_box.pack(fill=X)

        ttk.Label(frm, text="Tema interfaccia:", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(8, 2))
        theme_box = ttk.Combobox(frm, values=["superhero", "darkly", "flatly", "minty", "cyborg", "solar"], state="readonly")
        theme_box.set(SETTINGS.get("theme", "superhero"))
        theme_box.pack(fill=X)

        ttk.Label(frm, text="Velocità download (es. 500K, 2M, 0=illimitato):", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(8, 2))
        speed_entry = ttk.Entry(frm)
        speed_entry.insert(0, SETTINGS.get("speed_limit", "0"))
        speed_entry.pack(fill=X)

        ttk.Label(frm, text="Timeout ricerca (secondi):", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(8, 2))
        timeout_entry = ttk.Entry(frm)
        timeout_entry.insert(0, str(SETTINGS.get("search_timeout", 15)))
        timeout_entry.pack(fill=X)


        def save_and_refresh():
            old_settings = SETTINGS.copy()
            
            SETTINGS["language"] = lang_box.get()
            SETTINGS["theme"] = theme_box.get()
            SETTINGS["speed_limit"] = speed_entry.get().strip() or "0"
            
            try:
                SETTINGS["search_timeout"] = int(timeout_entry.get())
            except ValueError:
                SETTINGS["search_timeout"] = 15
                
            try:
                # [NUOVO] Salva download concorrenti
                con_dls = int(concurrent_entry.get())
                SETTINGS["concurrent_playlist_downloads"] = max(1, min(con_dls, 10)) # Limita tra 1 e 10
            except ValueError:
                SETTINGS["concurrent_playlist_downloads"] = 4

            save_settings()
            
            log(f"💾 Impostazioni salvate: {SETTINGS}")
            log(f"Le impostazioni cambiate erano: { {k: v for k, v in SETTINGS.items() if v != old_settings.get(k)} }")
            
            # [MODIFICATO] Applica il tema live
            try:
                self.style.theme_use(SETTINGS["theme"])
                log(f"🎨 Tema applicato live: {SETTINGS['theme']}")
            except Exception as e:
                log(f"Errore applicazione tema live: {e}")
                
            messagebox.showinfo("Impostazioni", "Salvate. Riavvia per applicare il cambio lingua.")
            win.destroy()

        ttk.Button(frm, text="💾 Salva", bootstyle=SUCCESS, command=save_and_refresh).pack(pady=12)

    def change_dir(self):
        log(f"📁 Apertura dialogo per cambio cartella download (attuale: {SETTINGS['download_dir']})")
        
        d = filedialog.askdirectory(initialdir=SETTINGS["download_dir"], title="Seleziona la cartella di download")
        if d:
            SETTINGS["download_dir"] = d
            if hasattr(self, 'dir_label'):
                 self.dir_label.config(text=d)
            save_settings()
            log(f"📁 Cartella download aggiornata a: {d}")

    # ---------------------- Log viewer ----------------------
    def open_log(self):
        log("🧾 Apertura finestra Log.")
        if not os.path.exists(LOG_FILE):
            messagebox.showinfo("Log", "Nessun log trovato.")
            return
        win = ttk.Toplevel(self)
        win.title("Log del Programma")
        win.geometry("800x600")
        txt = tk.Text(win, wrap="word", bg="#0b132b", fg="#e6e6e6", font=("Consolas", 10))
        try:
            with open(LOG_FILE, "r", encoding="utf-8") as f:
                txt.insert("1.0", f.read())
        except Exception as e:
            txt.insert("1.0", f"Errore lettura log: {e}")
            
        txt.config(state="disabled")
        txt.pack(fill=BOTH, expand=True, padx=8, pady=8)

    # ---------------------- [NUOVO] yt-dlp Updater ----------------------
    def check_for_updates(self):
        try:
            last_check_str = SETTINGS.get("last_update_check", "1970-01-01T00:00:00")
            last_check = datetime.fromisoformat(last_check_str)
            days_passed = (datetime.now() - last_check).days

            if days_passed >= 3:
                log(f"Ultimo controllo {days_passed} giorni fa. Chiedo all'utente di aggiornare.")
                if messagebox.askyesno(T["updater_prompt_title"], T["updater_prompt_text"]):
                    self.run_updater()
                else:
                    log(T["updater_skipped"])
                    # Salva la data odierna per non richiederlo per altri 3 giorni
                    SETTINGS["last_update_check"] = datetime.now().isoformat()
                    save_settings()
            else:
                log(T["updater_not_needed"])
        except Exception as e:
            log(f"Errore nel controllo aggiornamenti: {e}")

    def run_updater(self):
        log(f"Avvio finestra updater...")
        self.updater_win = ttk.Toplevel(self)
        self.updater_win.title(T["updater_title"])
        self.updater_win.geometry("700x400")
        self.updater_win.transient(self)
        self.updater_win.grab_set()

        ttk.Label(self.updater_win, text=T["updater_running"], font=("Segoe UI", 12, "bold"), padding=10).pack()
        
        self.updater_log_text = tk.Text(self.updater_win, wrap="word", bg="#0b132b", fg="#e6e6e6", font=("Consolas", 10))
        self.updater_log_text.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.updater_log_text.config(state="disabled")

        # Avvia il thread di aggiornamento
        threading.Thread(target=self._updater_thread, daemon=True).start()
        # Avvia il loop per controllare la coda dell'updater
        self._check_updater_queue()

    def _updater_thread(self):
        log("Avvio thread subprocess per 'pip install --upgrade yt-dlp'")
        cmd = [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"]
        try:
            # Esegui il processo e cattura l'output riga per riga
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                       text=True, encoding='utf-8', bufsize=1, universal_newlines=True, 
                                       creationflags=subprocess.CREATE_NO_WINDOW if platform.system() == "Windows" else 0)

            # Invia l'output alla coda in tempo reale
            for line in process.stdout:
                self.queue.put(("updater_log", line))
            
            process.wait()

            if process.returncode == 0:
                log("✅ Aggiornamento yt-dlp completato con successo.")
                SETTINGS["last_update_check"] = datetime.now().isoformat()
                save_settings()
                self.queue.put(("updater_done", True))
            else:
                log(f"❌ Aggiornamento yt-dlp fallito. Return code: {process.returncode}")
                self.queue.put(("updater_done", False))
                
        except Exception as e:
            log(f"❌ Errore critico nel thread updater: {e}")
            self.queue.put(("updater_log", f"\nERRORE CRITICO: {e}\n"))
            self.queue.put(("updater_done", False))

    def _check_updater_queue(self):
        try:
            while True:
                typ, payload = self.queue.get_nowait()
                
                if typ == "updater_log":
                    line = payload
                    self.updater_log_text.config(state="normal")
                    self.updater_log_text.insert(tk.END, line)
                    self.updater_log_text.see(tk.END)
                    self.updater_log_text.config(state="disabled")
                
                elif typ == "updater_done":
                    success = payload
                    if success:
                        messagebox.showinfo(T["updater_title"], T["updater_success"], parent=self.updater_win)
                    else:
                        messagebox.showerror(T["updater_title"], T["updater_fail"], parent=self.updater_win)
                    self.updater_win.destroy()
                    return # Termina il loop
                
                else:
                    # Metti da parte altri messaggi per il loop principale
                    self.queue.put_nowait((typ, payload))

        except queue.Empty:
            pass # Continua a controllare
        
        # Richiama se stesso dopo 100ms
        self.updater_win.after(100, self._check_updater_queue)

    # ---------------------- Loop eventi ----------------------
    def _loop(self):
        try:
            while True:
                typ, payload = self.queue.get_nowait()
                
                if typ == "done":
                    item_id = payload
                    self.downloading = False
                    self.lock_ui(False)
                    self.btn_play.config(state=NORMAL)
                    self.progress['value'] = 100
                    self.status.set(T["complete"])
                    
                    if item_id:
                        try:
                            self.tree.tag_remove('downloading_tag', item_id)
                        except Exception as e:
                            log(f"❌ Errore rimozione tag download completato: {e}")
                            
                    log("✅ Gestione evento 'done' (singolo). Download completato e UI sbloccata.")
                    messagebox.showinfo("Completato", T["complete_msg"])
                    self.after(5000, self.reset_ui)
                
                elif typ == "error":
                    self.downloading = False
                    self.lock_ui(False)
                    log(f"❌ Gestione evento 'error' (singolo). Errore: {payload}")
                    messagebox.showerror("Errore", payload)
                
                # [MODIFICATO] Ignora gli eventi della playlist (gestiti dal Toplevel)
                elif typ.startswith("playlist_"):
                    pass
                
                # [MODIFICATO] Ignora gli eventi dell'updater (gestiti dal Toplevel)
                elif typ.startswith("updater_"):
                    pass

                elif typ == "progress":
                    self.progress['value'] = payload
        
        except queue.Empty:
            pass
        
        self.after(150, self._loop)

    def reset_ui(self):
        global LAST_FILE
        self.query.set("")
        self.results = []
        self.tree.delete(*self.tree.get_children())
        self.status.set(T["ready"])
        self.btn_play.config(state=DISABLED)
        self.progress['value'] = 0
        self.lock_ui(False)
        LAST_FILE = None 
        log("🔄 UI principale resettata e variabile LAST_FILE pulita.")

# ---------------------- MAIN ----------------------
def main():
    log("🚀 Avvio di MUSIC WAVVER (main)...")
    if not SETTINGS.get("agreement_accepted", False):
        if not show_agreement():
            log("🛑 Programma chiuso a causa del mancato consenso all'accordo legale.")
            sys.exit(0)
    app = YTDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()

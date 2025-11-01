#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA- 01/11/2025
YouTube Downloader (senza pytube) - versione completa + API Key support
- Ricerca via yt_dlp interno (ytsearchN)
- Download e conversione in wav/mp3/flac con ffmpeg locale
- Barra di avanzamento reale (progress hooks o parsing stdout)
- settings.json per preferenze e API Key YouTube
- log file (ytdownloader.log)
- GUI moderna con ttkbootstrap (ora con Treeview per i risultati)
ATTENZIONE: NON aggira DRM/protezioni. Se il contenuto è protetto, verrà segnalato.
"""

import os
import sys
import json
import threading
import queue
import logging
import platform
import time
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog, ttk as tktk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from yt_dlp import YoutubeDL

# ----------------------
# Config / Logging
# ----------------------
LOG_FILE = "ytdownloader.log"
SETTINGS_FILE = "settings.json"

# RIGA DA AGGIUNGERE: Cancella il contenuto del file di log
try:
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.truncate(0)
except Exception as e:
    # Ignora se il file non esiste ancora, ma registra l'errore se si verifica
    print(f"⚠️ Errore durante la pulizia del log: {e}")

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

def log(msg):
    # print(msg) # Disattivato per pulizia, il log è su file e console
    try:
        logging.info(msg)
    except Exception:
        pass

DEFAULT_SETTINGS = {
    "download_dir": os.path.join(os.path.expanduser("~"), "Downloads"),
    "theme": "superhero",
    "speed_limit": "0",
    "search_timeout": 15,
    "youtube_api_key": ""
}

def load_settings():
    """Carica le impostazioni dal file settings.json, aggiornando i default."""
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                DEFAULT_SETTINGS.update(s)
        except Exception as e:
            log(f"⚠️ Errore leggendo settings.json: {e}")
    return DEFAULT_SETTINGS

def save_settings():
    """Salva le impostazioni nel file settings.json."""
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(SETTINGS, f, indent=4)

SETTINGS = load_settings()

# ----------------------
# ffmpeg detection
# ----------------------
def detect_ffmpeg():
    """Cerca ffmpeg nel percorso specificato e aggiorna la variabile d'ambiente PATH."""
    base = os.path.dirname(os.path.abspath(sys.argv[0])) # Percorso assoluto della directory dello script
    sys_os = platform.system().lower()
    
    if "win" in sys_os:
        candidate = os.path.join(base, "ffmpeg", "win", "ffmpeg.exe")
    else:
        candidate = os.path.join(base, "ffmpeg", "linux", "ffmpeg")

    if not os.path.exists(candidate):
        messagebox.showerror("ffmpeg non trovato",
            f"ffmpeg non trovato nel percorso atteso:\n{candidate}\nAssicurati che ffmpeg sia presente e che sia eseguibile.")
        sys.exit(1)

    log(f"⚙️ ffmpeg trovato: {candidate}")
    
    # Aggiunge la directory di ffmpeg a PATH per farlo trovare a yt_dlp
    os.environ["PATH"] = os.path.dirname(candidate) + os.pathsep + os.environ.get("PATH","")
    return candidate

FFMPEG_PATH = detect_ffmpeg()

# ----------------------
# util: duration conversion
# ----------------------
def format_duration(seconds):
    """Converte i secondi totali in formato HH:MM:SS."""
    if seconds is None or seconds == '?':
        return 'N/D'
    try:
        seconds = int(seconds)
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return f"{h:d}:{m:02d}:{s:02d}"
    except (ValueError, TypeError):
        return 'N/D'

# ----------------------
# SEARCH (via yt_dlp)
# ----------------------
def _yt_search_worker(query, max_results, result_queue):
    """Worker thread per eseguire la ricerca yt_dlp in modo non bloccante."""
    try:
        # yt_dlp non supporta nativamente l'API Key, ma usa cookies/login.
        # L'opzione 'default_search': 'ytsearch' esegue la ricerca interna.
        opts = {"quiet": True, "extract_flat": True, "skip_download": True, "default_search": "ytsearch"}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            results = []
            for e in info.get("entries", []):
                if e.get('id'): # Filtra risultati non validi (e.g. canali)
                    results.append({
                        "title": e.get("title", "Sconosciuto"),
                        "url": f"https://www.youtube.com/watch?v={e.get('id','')}",
                        "duration": format_duration(e.get("duration", "?")),
                        "uploader": e.get("uploader", "Sconosciuto")
                    })
            result_queue.put(("ok", results))
    except Exception as ex:
        result_queue.put(("err", str(ex)))

def search_youtube(query, max_results=10, timeout_seconds=15):
    """Avvia la ricerca yt_dlp in un thread separato con un timeout."""
    log(f"🔎 Ricerca YouTube (yt_dlp): {query}")
    rq = queue.Queue()
    t = threading.Thread(target=_yt_search_worker, args=(query, max_results, rq), daemon=True)
    t.start()
    
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            typ, payload = rq.get_nowait()
            if typ == "ok":
                log(f"🟢 Ricerca completata: {len(payload)} risultati")
                return payload
            else:
                raise RuntimeError(payload)
        except queue.Empty:
            time.sleep(0.05)
            
    raise TimeoutError(f"Ricerca scaduta (timeout {timeout_seconds}s)")

# ----------------------
# DOWNLOAD via yt_dlp
# ----------------------
def download_with_yt_dlp(url, fmt, out_dir, speed_limit, progress_cb=None):
    """Esegue il download e l'estrazione audio con yt_dlp e ffmpeg."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    # Usa safe_filename per evitare problemi di percorso
    outtmpl = os.path.join(out_dir, "%(title)s - %(id)s_"+timestamp+".%(ext)s")
    
    # Imposta parametri di qualità in base al formato
    preferred_quality = "192" 
    if fmt in ["wav", "flac"]:
        preferred_quality = "best" # Migliore qualità per formati lossless
    elif fmt == "mp3":
        preferred_quality = "320" # 320kbps per mp3 di alta qualità

    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best", # Seleziona il miglior flusso audio disponibile
        "quiet": True,
        "noplaylist": True,
        "ffmpeg_location": os.path.dirname(FFMPEG_PATH),
        "postprocessors": [{
            "key":"FFmpegExtractAudio",
            "preferredcodec": fmt,
            "preferredquality": preferred_quality
        }],
    }
    
    if speed_limit and speed_limit != "0":
        v = speed_limit.upper()
        digits = ''.join(c for c in v if c.isdigit())
        if digits:
            num = int(digits)
            if "M" in v:
                num *= 1024*1024
            elif "K" in v:
                num *= 1024
            ydl_opts["ratelimit"] = num

    def hook(d):
        """Hook per aggiornare la barra di avanzamento e lo stato, gestendo i None."""
        status = d.get("status")
        
        if status == "downloading":
            perc = None
            pstr = d.get("_percent_str") or d.get("percent")
            if pstr:
                try:
                    perc = float(str(pstr).strip().replace("%",""))
                except:
                    perc = None
            
            # Recupera velocità e ETA in modo sicuro
            speed = d.get('_speed_str', 'N/D')
            eta = d.get('_eta_str', 'N/D')
            
            # Prepara il messaggio di stato in modo sicuro
            perc_display = f"{perc:.1f}" if perc is not None else "0.0"
            status_msg = f"Download {perc_display}% @ {speed} | ETA {eta}"
            
            if progress_cb:
                progress_cb(perc if perc is not None else 0.0, status_msg)
                
        elif status == "postprocessing":
             # Gestisce lo stato intermedio di conversione
             if progress_cb:
                progress_cb(99.0, "Conversione in formato " + fmt.upper() + " in corso...")

        elif status == "finished":
            if progress_cb:
                progress_cb(100.0, "Scaricamento completato, pulizia file...")

    ydl_opts["progress_hooks"] = [hook]

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info.get("is_live") or info.get("was_live"):
                raise RuntimeError("Video in live streaming non supportato.")
            
            # Controlla se il titolo esiste prima di loggare
            title = info.get("title", "Video senza titolo")
            log(f"🎧 Download avviato: '{title}' -> formato {fmt}")
            
            ydl.download([url])
            
        log("✅ Download e conversione completati")
        return True
    except Exception as e:
        msg = str(e)
        log(f"❌ Errore yt_dlp: {msg}")
        if "403" in msg or "Forbidden" in msg or "GVS" in msg or "SABR" in msg:
            raise PermissionError("Contenuto probabilmente protetto da YouTube (403/DRM).")
        raise

# ----------------------
# GUI App
# ----------------------
class YTDownloaderApp(ttk.Window):
    def __init__(self):
        super().__init__(themename=SETTINGS.get("theme","superhero"))
        self.title("Il Mangia's MUSIC WAVVER - V.2.0")
        self.geometry("960x620")
        self.queue = queue.Queue()
        self.results = []
        self.downloading = False

        self.query = tk.StringVar()
        self.format = tk.StringVar(value="wav")
        self.status = tk.StringVar(value="Pronto")
        self.search_max = tk.IntVar(value=10)

        self._build_ui()
        self._loop()
        log("🟢 GUI avviata")

    def _build_ui(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # Sezione TOP
        top = ttk.Frame(frm)
        top.pack(fill=X)
        ttk.Label(top, text="Welcome to MUSIC WAVVER", font=("Segoe UI", 18, "bold")).pack(side=LEFT)
        ttk.Button(top, text="⚙️ Impostazioni", bootstyle=INFO, command=self.open_settings).pack(side=RIGHT, padx=6)
        ttk.Button(top, text="🧾 Apri log", bootstyle=SECONDARY, command=self.open_log).pack(side=RIGHT)

        # Sezione Ricerca
        row1 = ttk.Frame(frm)
        row1.pack(fill=X, pady=10)
        ttk.Entry(row1, textvariable=self.query, width=70, bootstyle=INFO).pack(side=LEFT, fill=X, expand=True, padx=(0,8))
        self.btn_search = ttk.Button(row1, text="🔍 Cerca / Incolla link", bootstyle=PRIMARY, command=self.on_search)
        self.btn_search.pack(side=LEFT)

        # Sezione Risultati (Treeview)
        # Sostituisce la Listbox con un Treeview per una visualizzazione tabellare
        cols = ("Titolo", "Uploader", "Durata")
        self.results_list = tktk.Treeview(frm, columns=cols, show="headings", height=14)
        
        self.results_list.heading("Titolo", text="Titolo", anchor=W)
        self.results_list.heading("Uploader", text="Uploader", anchor=W)
        self.results_list.heading("Durata", text="Durata", anchor=CENTER)

        self.results_list.column("Titolo", width=400, stretch=True)
        self.results_list.column("Uploader", width=250, stretch=True)
        self.results_list.column("Durata", width=100, anchor=CENTER, stretch=False)
        
        # Stile per la Treeview (necessario un po' di hacking con ttkbootstrap)
        style = ttk.Style()
        style.configure("Treeview.Heading", font=('Segoe UI', 10, 'bold'))
        style.configure("Treeview", rowheight=25, background="#0b132b", fieldbackground="#0b132b", foreground="#f1f1f1")
        style.map('Treeview', background=[('selected', '#0078d7')]) # Colore di selezione
        
        self.results_list.pack(fill=BOTH, expand=True, pady=8)
        self.results_list.bind("<Double-Button-1>", lambda e: self.on_download())

        # Sezione Opzioni e Download
        row2 = ttk.Frame(frm)
        row2.pack(fill=X, pady=6)
        
        ttk.Label(row2, text="Formato:", bootstyle=SECONDARY).pack(side=LEFT)
        ttk.OptionMenu(row2, self.format, self.format.get(), "wav", "mp3", "flac").pack(side=LEFT, padx=6)
        
        ttk.Label(row2, text="Risultati:", bootstyle=SECONDARY).pack(side=LEFT, padx=(12,6))
        ttk.Spinbox(row2, from_=1, to=25, width=4, textvariable=self.search_max).pack(side=LEFT)
        
        self.btn_download = ttk.Button(row2, text="⬇️ Download selezionato", bootstyle=SUCCESS, command=self.on_download)
        self.btn_download.pack(side=LEFT, padx=8)

        # Sezione Stato e Progresso
        row3 = ttk.Frame(frm)
        row3.pack(fill=X, pady=(12,6))
        self.progress = ttk.Progressbar(row3, length=500, bootstyle=INFO)
        self.progress.pack(side=LEFT, fill=X, expand=True, padx=6)
        ttk.Label(row3, textvariable=self.status, width=50).pack(side=LEFT, padx=8)

        ttk.Label(frm, text="Doppio click su un risultato per avviare il download. Se il video è protetto, verrà segnalato.", font=("Segoe UI", 9)).pack(anchor=W, pady=(8,0))

    # ----- actions -----
    def on_search(self):
        q = self.query.get().strip()
        if not q:
            messagebox.showinfo("Info", "Inserisci una query o incolla il link YouTube.")
            return
        
        self.results_list.delete(*self.results_list.get_children()) # Pulisce la Treeview
        self.btn_search.config(state=DISABLED)
        self.status.set("Ricerca in corso...")
        
        is_link = "youtube.com/watch" in q or "youtu.be/" in q
        if is_link:
            # Passa il link direttamente come risultato per il download
            results = [{"title": q, "url": q, "duration": "N/A", "uploader":"Link Diretto"}]
            self.queue.put(("search_done", results))
        else:
            threading.Thread(target=self._search_thread, args=(q,int(self.search_max.get())), daemon=True).start()

    def _search_thread(self, q, maxr):
        """Esegue la ricerca vera e propria per la query (non per il link)."""
        try:
            results = search_youtube(q, max_results=maxr, timeout_seconds=SETTINGS.get("search_timeout",15))
            self.queue.put(("search_done", results))
        except Exception as e:
            self.queue.put(("search_error", str(e)))

    def on_download(self):
        if self.downloading:
            return
            
        # Ottiene l'ID del risultato selezionato nella Treeview
        sel_id = self.results_list.focus()
        if not sel_id:
            messagebox.showinfo("Info", "Seleziona un risultato dalla lista.")
            return
        
        # Recupera i dati del risultato dall'indice (i nostri dati li mettiamo in self.results)
        # L'ID del Treeview è l'indice nella nostra lista results
        try:
            idx = int(sel_id.replace("I", "", 1), 16) - 1 # Converte l'ID esadecimale interno in indice intero
            item = self.results[idx]
        except (ValueError, IndexError):
            messagebox.showerror("Errore", "Errore nel recupero del risultato selezionato.")
            return

        url = item["url"]
        fmt = self.format.get()
        
        if not messagebox.askyesno("Conferma diritti", 
                                   f"Confermi di avere i diritti per scaricare il contenuto '{item['title']}' e di aver letto le condizioni di servizio di YouTube?"):
            return
            
        self.downloading = True
        self.btn_search.config(state=DISABLED)
        self.btn_download.config(state=DISABLED)
        self.progress['value'] = 0
        self.status.set(f"Avvio download di {item['title']}...")
        threading.Thread(target=self._download_thread, args=(url, fmt), daemon=True).start()

    def _download_thread(self, url, fmt):
        """Thread worker per gestire il processo di download."""
        def progress_cb(p, msg):
            self.queue.put(("progress", (p, msg)))
        try:
            download_with_yt_dlp(url, fmt, SETTINGS["download_dir"], SETTINGS["speed_limit"], progress_cb=progress_cb)
            self.queue.put(("done", None))
        except Exception as e:
            self.queue.put(("error", str(e)))

    # ----- settings window -----
    def open_settings(self):
        """Apre la finestra delle impostazioni."""
        win = ttk.Toplevel(self)
        win.title("Impostazioni")
        win.geometry("540x450")
        win.transient(self) # Rende la finestra modale
        win.grab_set()

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Cartella download:", font=("Segoe UI",11,"bold")).pack(anchor=W, pady=(10,2))
        self.dir_label = ttk.Label(frm, text=SETTINGS["download_dir"], wraplength=480, bootstyle=PRIMARY)
        self.dir_label.pack(anchor=W)
        ttk.Button(frm, text="📁 Cambia cartella", bootstyle=SECONDARY, command=self.change_dir).pack(anchor=W, pady=6)

        ttk.Separator(frm).pack(fill=X, pady=8)
        
        # Tema interfaccia
        ttk.Label(frm, text="Tema interfaccia (richiede riavvio):", font=("Segoe UI",11,"bold")).pack(anchor=W, pady=(6,2))
        theme_box = ttk.Combobox(frm, values=["superhero","darkly","flatly","minty","cyborg","solar"], state="readonly")
        theme_box.set(SETTINGS.get("theme","superhero"))
        theme_box.pack(fill=X)

        # Velocità download
        ttk.Label(frm, text="Velocità download (es. 500K, 2M, 0=illimitato):", font=("Segoe UI",11,"bold")).pack(anchor=W, pady=(8,2))
        speed_entry = ttk.Entry(frm)
        speed_entry.insert(0, SETTINGS.get("speed_limit","0"))
        speed_entry.pack(fill=X)

        # Timeout ricerca
        ttk.Label(frm, text="Timeout ricerca (secondi):", font=("Segoe UI",11,"bold")).pack(anchor=W, pady=(8,2))
        timeout_entry = ttk.Entry(frm)
        timeout_entry.insert(0, str(SETTINGS.get("search_timeout",15)))
        timeout_entry.pack(fill=X)

        ttk.Separator(frm).pack(fill=X, pady=8)
        
        # API Key (Nota: yt-dlp usa solo la ricerca interna che non richiede chiave)
        ttk.Label(frm, text="YouTube API Key (opzionale, non usata da yt-dlp):", font=("Segoe UI",11,"bold")).pack(anchor=W, pady=(6,2))
        api_entry = ttk.Entry(frm)
        api_entry.insert(0, SETTINGS.get("youtube_api_key",""))
        api_entry.pack(fill=X)

        def save_and_refresh():
            SETTINGS["theme"] = theme_box.get()
            SETTINGS["speed_limit"] = speed_entry.get().strip() or "0"
            try:
                SETTINGS["search_timeout"] = int(timeout_entry.get())
            except ValueError:
                SETTINGS["search_timeout"] = 15
            SETTINGS["youtube_api_key"] = api_entry.get().strip()
            save_settings()
            messagebox.showinfo("Impostazioni", "Salvate. Alcuni cambi richiedono **riavvio** (tema).")
            win.destroy()

        ttk.Button(frm, text="💾 Salva", bootstyle=SUCCESS, command=save_and_refresh).pack(pady=12)
        win.wait_window()

    def change_dir(self):
        """Apre la finestra di dialogo per cambiare la directory di download."""
        d = filedialog.askdirectory(initialdir=SETTINGS["download_dir"], title="Seleziona la cartella di download")
        if d:
            SETTINGS["download_dir"] = d
            self.dir_label.config(text=d) # Aggiorna l'etichetta nella finestra settings
            log(f"📁 Nuova cartella: {d}")

    def open_log(self):
        """Apre una finestra per visualizzare il file di log."""
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
             txt.insert("1.0", f"Errore leggendo il log: {e}")
        txt.config(state="disabled")
        txt.pack(fill=BOTH, expand=True, padx=8, pady=8)

    # ----- main loop -----
    def _loop(self):
        """Ciclo principale per processare gli eventi dalla coda del thread."""
        try:
            while True:
                typ, payload = self.queue.get_nowait()
                if typ == "search_done":
                    self.results = payload
                    self.results_list.delete(*self.results_list.get_children())
                    for i, r in enumerate(payload):
                        # Inserisce i dati nella Treeview in colonne separate
                        self.results_list.insert("", "end", iid=str(i+1), 
                                                 values=(r['title'], r['uploader'], r['duration']))
                    
                    self.status.set(f"Trovati {len(payload)} risultati.")
                    self.btn_search.config(state=NORMAL)
                
                elif typ == "search_error":
                    self.status.set("Errore ricerca")
                    messagebox.showerror("Errore ricerca", payload)
                    self.btn_search.config(state=NORMAL)
                    
                elif typ == "progress":
                    perc, msg = payload
                    if perc is not None:
                        try:
                            self.progress['value'] = float(perc)
                        except:
                            pass
                    self.status.set(msg)
                    
                elif typ == "done":
                    self.status.set(f"✅ Download completato nella cartella: {SETTINGS['download_dir']}")
                    self.progress['value'] = 100
                    messagebox.showinfo("Completato", "Download e conversione terminati.")
                    self.downloading = False
                    self.btn_search.config(state=NORMAL)
                    self.btn_download.config(state=NORMAL)
                    
                elif typ == "error":
                    self.status.set("❌ Errore")
                    messagebox.showerror("Errore Download/Conversione", payload)
                    log(f"❌ Errore: {payload}")
                    self.downloading = False
                    self.btn_search.config(state=NORMAL)
                    self.btn_download.config(state=NORMAL)
                    
        except queue.Empty:
            pass
        # Richiama il loop con un breve ritardo
        self.after(150, self._loop)

# ----------------------
# Main
# ----------------------
def main():
    log("🚀 Avvio di MUSIC WAVVER...")
    app = YTDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()
# BY IL MANGIA- 01/11/2025
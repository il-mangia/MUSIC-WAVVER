 #!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BY IL MANGIA - 08/11/2025 (Aggiornato)
MUSIC WAVVER 2.5 - YouTube Downloader avanzato con GUI ttkbootstrap
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
from datetime import datetime
import subprocess
import tkinter as tk
from tkinter import messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from yt_dlp import YoutubeDL

# ---------------------- LOGGING ----------------------
LOG_FILE = "ytdownloader.log"
SETTINGS_FILE = "settings.json"

try:
    with open(LOG_FILE, 'w', encoding='utf-8') as f:
        f.truncate(0)
except Exception:
    pass

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")

def log(msg):
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
    "youtube_api_key": "",
    "agreement_accepted": False,
    "language": "it"
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
    },
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
            "El autor ('Il Mangia') no se hace responsable de un uso indebido ni de violaciones de derechos.\n\n"
            "Solo para uso personal y educativo.\n\n"
            "Presiona 'Aceptar' para continuar."
        ),
        "agreement_close": "No aceptaste el acuerdo. El programa se cerrará.",
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
    }
}

# ---------------------- SETTINGS ----------------------
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
                DEFAULT_SETTINGS.update(s)
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
        messagebox.showerror("ffmpeg", f"ffmpeg non trovato:\n{candidate}")
        sys.exit(1)
    os.environ["PATH"] = os.path.dirname(candidate) + os.pathsep + os.environ.get("PATH","")
    return candidate

FFMPEG_PATH = detect_ffmpeg()

# ---------------------- RICERCA ----------------------
def _yt_search_worker(query, max_results, result_queue):
    try:
        opts = {"quiet": True, "extract_flat": True, "skip_download": True, "default_search": "ytsearch"}
        with YoutubeDL(opts) as ydl:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)
            results = []
            for e in info.get("entries", []):
                if e.get('id'):
                    results.append({
                        "title": e.get("title", "Sconosciuto"),
                        "url": f"https://www.youtube.com/watch?v={e['id']}",
                        "duration": e.get("duration", "N/D"),
                        "uploader": e.get("uploader", "Sconosciuto")
                    })
            result_queue.put(("ok", results))
    except Exception as ex:
        result_queue.put(("err", str(ex)))

def search_youtube(query, max_results=10, timeout_seconds=15):
    rq = queue.Queue()
    t = threading.Thread(target=_yt_search_worker, args=(query, max_results, rq), daemon=True)
    t.start()
    start = time.time()
    while time.time() - start < timeout_seconds:
        try:
            typ, payload = rq.get_nowait()
            return payload if typ == "ok" else (_ for _ in ()).throw(RuntimeError(payload))
        except queue.Empty:
            time.sleep(0.05)
    raise TimeoutError("Ricerca scaduta")

# ---------------------- DOWNLOAD ----------------------
LAST_FILE = None
def download_with_yt_dlp(url, fmt, out_dir, speed_limit, progress_cb=None):
    global LAST_FILE
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outtmpl = os.path.join(out_dir, "%(title)s_"+timestamp+".%(ext)s")
    ydl_opts = {
        "outtmpl": outtmpl,
        "format": "bestaudio/best",
        "quiet": True,
        "noplaylist": True,
        "ffmpeg_location": os.path.dirname(FFMPEG_PATH),
        "postprocessors": [{"key":"FFmpegExtractAudio","preferredcodec": fmt,"preferredquality": "320"}],
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        LAST_FILE = ydl.prepare_filename(info).rsplit(".",1)[0] + f".{fmt}"
    return True
# ---------------------- GUI ----------------------
class YTDownloaderApp(ttk.Window):
    def __init__(self):
        super().__init__(themename=SETTINGS.get("theme", "superhero"))
        self.title("Il Mangia's MUSIC WAVVER - V.2.5")
        self.geometry("960x620")

        # Queue (mancava prima)
        self.queue = queue.Queue()

        self.results = []
        self.downloading = False
        self.query = tk.StringVar()
        self.format = tk.StringVar(value="wav")
        self.status = tk.StringVar(value=T["ready"])
        self.search_max = tk.IntVar(value=10)

        self._build_ui()
        self._loop()
        log("🟢 GUI avviata")

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
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=14)
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
        for b in [self.btn_search, self.btn_download, self.entry]:
            b.config(state=s)

    def on_search(self):
        q = self.query.get().strip()
        if not q:
            return
        self.lock_ui(True)
        self.btn_play.config(state=DISABLED)
        self.status.set(T["searching"])
        threading.Thread(target=self._search_thread, args=(q, int(self.search_max.get())), daemon=True).start()

    def _search_thread(self, q, maxr):
        try:
            results = search_youtube(q, max_results=maxr)
            self.results = results
            self.tree.delete(*self.tree.get_children())
            for r in results:
                self.tree.insert("", "end", values=(r["title"], r["uploader"], r["duration"]))
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
        item = self.tree.item(sel)["values"]
        title = item[0]
        url = self.results[self.tree.index(sel)]["url"]
        self.downloading = True
        self.lock_ui(True)
        self.status.set(f"Scaricamento di {title}...")
        threading.Thread(target=self._download_thread, args=(url, self.format.get()), daemon=True).start()

    def _download_thread(self, url, fmt):
        try:
            download_with_yt_dlp(url, fmt, SETTINGS["download_dir"], SETTINGS["speed_limit"])
            self.queue.put(("done", None))
        except Exception as e:
            self.queue.put(("error", str(e)))

    def play_file(self):
        if LAST_FILE and os.path.exists(LAST_FILE):
            log(f"🎵 Riproduzione file: {LAST_FILE}")
            if platform.system() == "Windows":
                os.startfile(LAST_FILE)
            elif platform.system() == "Darwin":
                subprocess.call(["open", LAST_FILE])
            else:
                subprocess.call(["xdg-open", LAST_FILE])
        else:
            messagebox.showinfo("Errore", "Nessun file da riprodurre trovato.")

    # ---------------------- Impostazioni ----------------------
    def open_settings(self):
        win = ttk.Toplevel(self)
        win.title("Impostazioni")
        win.geometry("540x480")
        win.transient(self)
        win.grab_set()

        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        ttk.Label(frm, text="Cartella download:", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(10, 2))
        self.dir_label = ttk.Label(frm, text=SETTINGS["download_dir"], wraplength=480, bootstyle=PRIMARY)
        self.dir_label.pack(anchor=W)
        ttk.Button(frm, text="📁 Cambia cartella", bootstyle=SECONDARY, command=self.change_dir).pack(anchor=W, pady=6)

        ttk.Separator(frm).pack(fill=X, pady=8)
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

        ttk.Label(frm, text="YouTube API Key (opzionale):", font=("Segoe UI", 11, "bold")).pack(anchor=W, pady=(8, 2))
        api_entry = ttk.Entry(frm)
        api_entry.insert(0, SETTINGS.get("youtube_api_key", ""))
        api_entry.pack(fill=X)

        def save_and_refresh():
            SETTINGS["language"] = lang_box.get()
            SETTINGS["theme"] = theme_box.get()
            SETTINGS["speed_limit"] = speed_entry.get().strip() or "0"
            try:
                SETTINGS["search_timeout"] = int(timeout_entry.get())
            except ValueError:
                SETTINGS["search_timeout"] = 15
            SETTINGS["youtube_api_key"] = api_entry.get().strip()
            save_settings()
            messagebox.showinfo("Impostazioni", "Salvate. Riavvia per applicare i cambi.")
            win.destroy()

        ttk.Button(frm, text="💾 Salva", bootstyle=SUCCESS, command=save_and_refresh).pack(pady=12)

    def change_dir(self):
        d = filedialog.askdirectory(initialdir=SETTINGS["download_dir"], title="Seleziona la cartella di download")
        if d:
            SETTINGS["download_dir"] = d
            self.dir_label.config(text=d)
            save_settings()

    # ---------------------- Log viewer ----------------------
    def open_log(self):
        if not os.path.exists(LOG_FILE):
            messagebox.showinfo("Log", "Nessun log trovato.")
            return
        win = ttk.Toplevel(self)
        win.title("Log del Programma")
        win.geometry("800x600")
        txt = tk.Text(win, wrap="word", bg="#0b132b", fg="#e6e6e6", font=("Consolas", 10))
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            txt.insert("1.0", f.read())
        txt.config(state="disabled")
        txt.pack(fill=BOTH, expand=True, padx=8, pady=8)

    # ---------------------- Loop eventi ----------------------
    def _loop(self):
        try:
            while True:
                typ, payload = self.queue.get_nowait()
                if typ == "done":
                    self.downloading = False
                    self.lock_ui(False)
                    self.btn_play.config(state=NORMAL)
                    self.progress['value'] = 100
                    self.status.set(T["complete"])
                    log("✅ Download completato.")
                    messagebox.showinfo("Completato", T["complete_msg"])
                    self.after(5000, self.reset_ui)
                elif typ == "error":
                    self.downloading = False
                    self.lock_ui(False)
                    messagebox.showerror("Errore", payload)
        except queue.Empty:
            pass
        self.after(150, self._loop)

    def reset_ui(self):
        self.query.set("")
        self.results = []
        self.tree.delete(*self.tree.get_children())
        self.status.set(T["ready"])
        self.btn_play.config(state=DISABLED)
        self.progress['value'] = 0
        self.lock_ui(False)

# ---------------------- MAIN ----------------------
def main():
    log("🚀 Avvio di MUSIC WAVVER...")
    if not SETTINGS.get("agreement_accepted", False):
        if not show_agreement():
            sys.exit(0)
    app = YTDownloaderApp()
    app.mainloop()

if __name__ == "__main__":
    main()
# BY IL MANGIA - 08/11/2025

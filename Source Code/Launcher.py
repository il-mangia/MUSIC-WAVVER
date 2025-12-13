import customtkinter as ctk
import subprocess
import os
import sys  # Importato per gestire i percorsi in PyInstaller
import time
from PIL import Image
import math

# CONFIGURAZIONE GLOBALE
WIDTH = 420
HEIGHT = 520

# Coordinate Y
LOGO_START_Y = -220
LOGO_END_Y = 60
TITLE_CENTER_Y = 290

# ====================================================================
# FUNZIONI UTILITY PER GESTIRE I PERCORSI E I PROCESSI
# ====================================================================

def get_launcher_dir():
    """Restituisce la directory in cui si trova l'eseguibile Launcher.exe."""
    return os.path.dirname(sys.executable)

def resource_path(relative_path):
    """
    Ottiene il percorso assoluto per le risorse INTERNE (come Logo.png).
    """
    try:
        # Per le risorse INTERNE, usiamo sys._MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        # Per lo script Python standard, usiamo la directory corrente
        base_path = os.path.abspath(".")
        
    return os.path.join(base_path, relative_path)

def start_app():
    """
    Avvia l'applicazione principale, cercando i file nella directory di Launcher.exe.
    """
    # **PUNTO CRUCIALE:** Usiamo la directory del Launcher.exe, non la directory temporanea
    launcher_dir = get_launcher_dir()
    app_exe_path = os.path.join(launcher_dir, "app.exe")
    app_py_path = os.path.join(launcher_dir, "app.py")
    
    # 1. TENTATIVO DI AVVIO FORZATO DI app.exe
    try:
        if os.path.exists(app_exe_path):
            print(f"Tentativo 1: Avvio di app.exe da: {app_exe_path}")
            # Avvio del processo: diretto e semplice, senza shell
            subprocess.Popen([app_exe_path]) 
            return
        
        # 2. TENTATIVO DI AVVIO FORZATO DI app.py
        elif os.path.exists(app_py_path):
            print(f"Tentativo 2: Avvio di app.py da: {app_py_path}")
            # Avvio dello script Python
            subprocess.Popen(["python", app_py_path])
            return
            
        else:
            # FALLBACK
            print("FATAL ERROR: app.exe o app.py non trovati nella directory del launcher.")

    except Exception as e:
        print(f"ERRORE CRITICO: Fallimento durante l'avvio del processo: {e}")

# ====================================================================
# FUNZIONI DI ANIMAZIONE E INIZIALIZZAZIONE TKINTER (INVARIATE)
# ====================================================================

def ease_out_quart(t):
    t = 1 - t
    return 1 - (t * t * t * t)

def get_center():
    import tkinter as tk
    r = tk.Tk()
    r.withdraw()
    sw = r.winfo_screenwidth()
    sh = r.winfo_screenheight()
    r.destroy()
    x = int((sw - WIDTH) / 2)
    y = int((sh - HEIGHT) / 2)
    return f"{WIDTH}x{HEIGHT}+{x}+{y}"

def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.geometry(get_center())
    root.title("Music Wavver Launcher")
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 1)

    # ----- LOGO -----
    # resource_path è CORRETTO per il Logo (risorsa INTERNA)
    try:
        pil_image = Image.open(resource_path("Logo.png"))
        img = ctk.CTkImage(
            light_image=pil_image,
            dark_image=pil_image,
            size=(200, 200)
        )
    except FileNotFoundError:
        print("Errore: Logo.png non trovato. Assicurati che sia nella stessa cartella.")
        return 
    except Exception as e:
        print(f"Errore nel caricamento del logo: {e}")
        return

    logo = ctk.CTkLabel(root, text="", image=img)
    logo.place(x=WIDTH/2, y=LOGO_START_Y, anchor="n")

    # ----- SCRITTA -----
    title = ctk.CTkLabel(
        root,
        text="MUSIC WAVVER",
        font=("Segoe UI", 28, "bold"),
        text_color="#000000"
    )
    title.place(x=WIDTH/2, y=TITLE_CENTER_Y, anchor="center")

    # ==================================
    #    ANIMAZIONE
    # ==================================

    FPS = 60
    
    # 1. ANIMAZIONE LOGO
    SLIDE_DURATION = 0.6
    TOTAL_FRAMES = int(SLIDE_DURATION * FPS)
    y_range = LOGO_END_Y - LOGO_START_Y

    for frame in range(TOTAL_FRAMES + 1):
        t_linear = frame / TOTAL_FRAMES
        t_eased = ease_out_quart(t_linear)
        current_y = LOGO_START_Y + (y_range * t_eased)
        logo.place(x=WIDTH/2, y=current_y, anchor="n")
        root.update()
        time.sleep(1/FPS)

    time.sleep(0.1)

    # 2. FADE-IN TESTO
    FADE_IN_DURATION = 0.4
    FADE_FRAMES = int(FADE_IN_DURATION * FPS)

    for frame in range(FADE_FRAMES + 1):
        t = frame / FADE_FRAMES
        val = int(255 * (t * t))
        val = max(0, min(255, val))
        
        col = f"#{val:02x}{val:02x}{val:02x}"
        title.configure(text_color=col)
        root.update()
        time.sleep(1/FPS)

    time.sleep(0.7)

    # 3. FADE-OUT FINESTRA
    FADE_OUT_DURATION = 0.3
    OUT_FRAMES = int(FADE_OUT_DURATION * FPS)

    for frame in range(OUT_FRAMES + 1):
        alpha = 1 - (frame / OUT_FRAMES)
        root.attributes("-alpha", alpha)
        root.update()
        time.sleep(1/FPS)

    root.destroy()
    start_app() # Avvia l'app esterna

if __name__ == "__main__":
    main()
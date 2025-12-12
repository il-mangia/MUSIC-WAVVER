import customtkinter as ctk
import subprocess
import os
import time
from PIL import Image
import math

# CONFIGURAZIONE GLOBALE
WIDTH = 420
HEIGHT = 520

# Coordinate Y
LOGO_START_Y = -220  # Parte da sopra
LOGO_END_Y = 60      # Arriva qui (margine dall'alto)
TITLE_CENTER_Y = 290 # Posizione verticale del CENTRO della scritta

def ease_out_quart(t):
    """Funzione per rendere il movimento fluido (veloce -> lento)."""
    t = 1 - t
    return 1 - (t * t * t * t)

def start_app():
    if os.path.exists("app.exe"):
        subprocess.Popen(["app.exe"])
    elif os.path.exists("app.py"):
        subprocess.Popen(["python", "app.py"])
    else:
        print("bro… qui non c’è niente da avviare 💀")

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
    try:
        pil_image = Image.open("Logo.png")
        # Mantieni l'immagine quadrata per facilitare i calcoli
        img = ctk.CTkImage(
            light_image=pil_image,
            dark_image=pil_image,
            size=(200, 200)
        )
    except Exception as e:
        print(f"Errore logo: {e}")
        return

    logo = ctk.CTkLabel(root, text="", image=img)
    # POSIZIONAMENTO INIZIALE LOGO
    # x=WIDTH/2 mette il punto di ancoraggio al centro della finestra.
    # anchor="n" significa che il punto di riferimento è il "North" (alto-centro) del logo.
    logo.place(x=WIDTH/2, y=LOGO_START_Y, anchor="n")

    # ----- SCRITTA -----
    title = ctk.CTkLabel(
        root,
        text="MUSIC WAVVER",
        font=("Segoe UI", 28, "bold"),
        text_color="#000000"
    )
    # POSIZIONAMENTO SCRITTA
    # anchor="center" allinea il centro esatto della scritta alla X indicata.
    # Non importa quanto sia lungo il testo, sarà sempre centrato.
    title.place(x=WIDTH/2, y=TITLE_CENTER_Y, anchor="center")

    # ==================================
    #    ANIMAZIONE
    # ==================================

    # 1. ANIMAZIONE LOGO (Slide fluido)
    SLIDE_DURATION = 0.6
    FPS = 60
    TOTAL_FRAMES = int(SLIDE_DURATION * FPS)
    
    y_range = LOGO_END_Y - LOGO_START_Y

    for frame in range(TOTAL_FRAMES + 1):
        t_linear = frame / TOTAL_FRAMES
        t_eased = ease_out_quart(t_linear)
        
        current_y = LOGO_START_Y + (y_range * t_eased)
        
        # Aggiorniamo solo la Y, la X e l'anchor rimangono fissi
        logo.place(x=WIDTH/2, y=current_y, anchor="n")
        
        root.update()
        time.sleep(1/FPS)

    time.sleep(0.1)

    # 2. FADE-IN TESTO
    FADE_IN_DURATION = 0.4
    FADE_FRAMES = int(FADE_IN_DURATION * FPS)

    for frame in range(FADE_FRAMES + 1):
        t = frame / FADE_FRAMES
        # Ease-in sul colore per renderlo meno scattoso
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
    start_app()

if __name__ == "__main__":
    main()
#!/usr/bin/env python3
import customtkinter as ctk
import subprocess
import os
import sys
import time
import platform
import requests
import webbrowser
import locale
from PIL import Image

# ============================================================================
# CONFIGURAZIONE GLOBALE
# ============================================================================
WIDTH = 420
HEIGHT = 520
LOGO_START_Y = -220
LOGO_END_Y = 60
TITLE_CENTER_Y = 290
CURRENT_VERSION = "4.0"

# URL GitHub
GITHUB_REPO = "il-mangia/MUSIC-WAVVER"
GITHUB_TAGS_URL = f"https://api.github.com/repos/{GITHUB_REPO}/tags"
GITHUB_LATEST_RELEASE_URL = f"https://github.com/{GITHUB_REPO}/releases/latest"

# ============================================================================
# SISTEMA MULTILINGUA
# ============================================================================
TRANSLATIONS = {
    "it": {  # Italiano
        "app_name": "MUSIC WAVVER",
        "window_title": f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates": "Controllo aggiornamenti...",
        "update_available": "Aggiornamento disponibile!",
        "beta_detected": "Versione beta rilevata!",
        "error_checking": "Errore nel controllo!",
        "version_updated": "Versione aggiornata ✓",
        
        # Schermata aggiornamento
        "update_title": "AGGIORNAMENTO DISPONIBILE",
        "current_version": "Versione attuale",
        "latest_stable": "Ultima versione stabile",
        "update_message": "È disponibile una nuova versione stabile di Music Wavver\ncon miglioramenti e correzioni di bug.",
        "download_stable": "SCARICA VERSIONE STABILE",
        "continue_without": "CONTINUA SENZA AGGIORNARE",
        "update_note": "Nota: Dovrai scaricare e installare\nmanualmente la nuova versione.",
        
        # Schermata beta
        "beta_title": "VERSIONE BETA RILEVATA",
        "beta_current": "Versione in uso",
        "beta_warning": "Stai avviando una versione beta.\nPotrebbero presentarsi bug e instabilità.\n\nSi consiglia di tornare all'ultima versione stabile.",
        "return_stable": "TORNA ALL'ULTIMA VERSIONE STABILE",
        "accept_risk": "ACCETTA IL RISCHIO E CONTINUA",
        "beta_note": "La versione beta è destinata a scopi di testing.\nSegnala eventuali bug agli sviluppatori.",
        
        # Schermata errore
        "error_title": "ERRORE DI CONNESSIONE",
        "error_message": "Impossibile verificare gli aggiornamenti.\n\nControlla la tua connessione Internet\ne riprova.",
        "retry_button": "RIPROVA",
        "continue_anyway": "CONTINUA COMUNQUE",
        "error_note": "L'applicazione potrebbe non essere aggiornata.",
        
        # Log
        "checking_for": "Controllo aggiornamenti per versione",
        "latest_found": "Ultima versione stabile trovata",
        "update_found": "Trovato aggiornamento",
        "up_to_date": "Sei aggiornato all'ultima versione",
        "timeout": "Timeout nel controllo aggiornamenti",
        "connection_error": "Errore di connessione",
        "check_error": "Errore nel controllo aggiornamenti",
        "no_tags": "Nessun tag trovato nel repository",
        "no_stable": "Nessuna versione stabile trovata",
        "starting_app": "Avvio applicazione principale...",
        "opening_release": "Apertura pagina release",
        "restarting": "Riavvio del launcher...",
    },
    
    "en": {  # English
        "app_name": "MUSIC WAVVER",
        "window_title": f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates": "Checking for updates...",
        "update_available": "Update available!",
        "beta_detected": "Beta version detected!",
        "error_checking": "Error checking!",
        "version_updated": "Version updated ✓",
        
        # Update screen
        "update_title": "UPDATE AVAILABLE",
        "current_version": "Current version",
        "latest_stable": "Latest stable version",
        "update_message": "A new stable version of Music Wavver is available\nwith improvements and bug fixes.",
        "download_stable": "DOWNLOAD STABLE VERSION",
        "continue_without": "CONTINUE WITHOUT UPDATING",
        "update_note": "Note: You will need to download and install\nthe new version manually.",
        
        # Beta screen
        "beta_title": "BETA VERSION DETECTED",
        "beta_current": "Version in use",
        "beta_warning": "You are launching a beta version.\nBugs and instability may occur.\n\nWe recommend returning to the latest stable version.",
        "return_stable": "RETURN TO LATEST STABLE VERSION",
        "accept_risk": "ACCEPT RISK AND CONTINUE",
        "beta_note": "The beta version is intended for testing purposes.\nReport any bugs to the developers.",
        
        # Error screen
        "error_title": "CONNECTION ERROR",
        "error_message": "Unable to check for updates.\n\nCheck your Internet connection\nand try again.",
        "retry_button": "RETRY",
        "continue_anyway": "CONTINUE ANYWAY",
        "error_note": "The application may not be up to date.",
        
        # Log
        "checking_for": "Checking for updates for version",
        "latest_found": "Latest stable version found",
        "update_found": "Update found",
        "up_to_date": "You are up to date with the latest version",
        "timeout": "Timeout checking for updates",
        "connection_error": "Connection error",
        "check_error": "Error checking for updates",
        "no_tags": "No tags found in the repository",
        "no_stable": "No stable version found",
        "starting_app": "Starting main application...",
        "opening_release": "Opening release page",
        "restarting": "Restarting launcher...",
    },
    
    "es": {  # Español
        "app_name": "MUSIC WAVVER",
        "window_title": f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates": "Buscando actualizaciones...",
        "update_available": "¡Actualización disponible!",
        "beta_detected": "¡Versión beta detectada!",
        "error_checking": "¡Error en la verificación!",
        "version_updated": "Versión actualizada ✓",
        
        # Pantalla de actualización
        "update_title": "ACTUALIZACIÓN DISPONIBLE",
        "current_version": "Versión actual",
        "latest_stable": "Última versión estable",
        "update_message": "Hay una nueva versión estable de Music Wavver disponible\ncon mejoras y correcciones de errores.",
        "download_stable": "DESCARGAR VERSIÓN ESTABLE",
        "continue_without": "CONTINUAR SIN ACTUALIZAR",
        "update_note": "Nota: Tendrás que descargar e instalar\nla nueva versión manualmente.",
        
        # Pantalla beta
        "beta_title": "VERSIÓN BETA DETECTADA",
        "beta_current": "Versión en uso",
        "beta_warning": "Estás iniciando una versión beta.\nPueden aparecer errores e inestabilidad.\n\nRecomendamos volver a la última versión estable.",
        "return_stable": "VOLVER A LA ÚLTIMA VERSIÓN ESTABLE",
        "accept_risk": "ACEPTAR EL RIESGO Y CONTINUAR",
        "beta_note": "La versión beta está destinada a pruebas.\nReporta cualquier error a los desarrolladores.",
        
        # Pantalla de error
        "error_title": "ERROR DE CONEXIÓN",
        "error_message": "No se pueden verificar las actualizaciones.\n\nVerifica tu conexión a Internet\ny vuelve a intentarlo.",
        "retry_button": "REINTENTAR",
        "continue_anyway": "CONTINUAR DE TODAS FORMAS",
        "error_note": "La aplicación puede no estar actualizada.",
        
        # Log
        "checking_for": "Buscando actualizaciones para la versión",
        "latest_found": "Última versión estable encontrada",
        "update_found": "Actualización encontrada",
        "up_to_date": "Tienes la última versión",
        "timeout": "Timeout al buscar actualizaciones",
        "connection_error": "Error de conexión",
        "check_error": "Error al buscar actualizaciones",
        "no_tags": "No se encontraron etiquetas en el repositorio",
        "no_stable": "No se encontró versión estable",
        "starting_app": "Iniciando aplicación principal...",
        "opening_release": "Abriendo página de lanzamiento",
        "restarting": "Reiniciando el lanzador...",
    },
    
    "de": {  # Deutsch
        "app_name": "MUSIC WAVVER",
        "window_title": f"Music Wavver Launcher v{CURRENT_VERSION}",
        "checking_updates": "Suche nach Updates...",
        "update_available": "Update verfügbar!",
        "beta_detected": "Beta-Version erkannt!",
        "error_checking": "Fehler bei der Überprüfung!",
        "version_updated": "Version aktualisiert ✓",
        
        # Update-Bildschirm
        "update_title": "UPDATE VERFÜGBAR",
        "current_version": "Aktuelle Version",
        "latest_stable": "Neueste stabile Version",
        "update_message": "Eine neue stabile Version von Music Wavver ist verfügbar\nmit Verbesserungen und Fehlerbehebungen.",
        "download_stable": "STABILE VERSION HERUNTERLADEN",
        "continue_without": "OHNE UPDATE FORTFAHREN",
        "update_note": "Hinweis: Sie müssen die neue Version\nmanuell herunterladen und installieren.",
        
        # Beta-Bildschirm
        "beta_title": "BETA-VERSION ERKANNT",
        "beta_current": "Verwendete Version",
        "beta_warning": "Sie starten eine Beta-Version.\nFehler und Instabilitäten können auftreten.\n\nWir empfehlen, zur neuesten stabilen Version zurückzukehren.",
        "return_stable": "ZUR NEUESTEN STABILEN VERSION ZURÜCK",
        "accept_risk": "RISIKO AKZEPTIEREN UND FORTFAHREN",
        "beta_note": "Die Beta-Version ist für Testzwecke gedacht.\nMelden Sie Fehler an die Entwickler.",
        
        # Fehlerbildschirm
        "error_title": "VERBINDUNGSFEHLER",
        "error_message": "Updates können nicht überprüft werden.\n\nÜberprüfen Sie Ihre Internetverbindung\nund versuchen Sie es erneut.",
        "retry_button": "ERNEUT VERSUCHEN",
        "continue_anyway": "TROTZDEM FORTFAHREN",
        "error_note": "Die Anwendung ist möglicherweise nicht aktuell.",
        
        # Log
        "checking_for": "Suche nach Updates für Version",
        "latest_found": "Neueste stabile Version gefunden",
        "update_found": "Update gefunden",
        "up_to_date": "Sie haben die neueste Version",
        "timeout": "Timeout bei der Update-Suche",
        "connection_error": "Verbindungsfehler",
        "check_error": "Fehler bei der Update-Suche",
        "no_tags": "Keine Tags im Repository gefunden",
        "no_stable": "Keine stabile Version gefunden",
        "starting_app": "Hauptanwendung wird gestartet...",
        "opening_release": "Release-Seite wird geöffnet",
        "restarting": "Launcher wird neu gestartet...",
    }
}

def get_system_language():
    """
    Rileva la lingua del sistema operativo.
    Restituisce il codice lingua (it, en, es, de) o 'en' come fallback.
    """
    try:
        # Prova a ottenere la lingua dal sistema (versione moderna)
        try:
            # Python 3.11+ - usa getlocale
            system_lang = locale.getlocale()[0]
        except:
            # Python più vecchio - usa getdefaultlocale con deprecation warning
            import warnings
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=DeprecationWarning)
                system_lang, _ = locale.getdefaultlocale()
        
        if system_lang:
            # Estrai le prime due lettere (es: 'it_IT' → 'it')
            lang_code = system_lang.split('_')[0].lower() if system_lang else 'en'
            
            # Verifica se la lingua è supportata
            if lang_code in TRANSLATIONS:
                print(f"Lingua sistema rilevata: {lang_code}")
                return lang_code
        
        # Fallback basato sul sistema operativo
        system_os = platform.system()
        if system_os == "Windows":
            try:
                import ctypes
                windll = ctypes.windll.kernel32
                lang_id = windll.GetUserDefaultUILanguage()
                lang_map = {
                    1040: 'it',  # Italiano
                    1033: 'en',  # Inglese
                    3082: 'es',  # Spagnolo
                    1031: 'de',  # Tedesco
                }
                if lang_id in lang_map:
                    lang = lang_map[lang_id]
                    if lang in TRANSLATIONS:
                        print(f"Lingua Windows rilevata: {lang}")
                        return lang
            except:
                pass
        
        print(f"Lingua non supportata o non rilevata. Usando Inglese.")
        return 'en'
        
    except Exception as e:
        print(f"Errore nel rilevamento lingua: {e}. Usando Inglese.")
        return 'en'

def get_translation(key, lang):
    """Restituisce la traduzione per la chiave nella lingua specificata."""
    return TRANSLATIONS.get(lang, TRANSLATIONS['en']).get(key, key)

def get_launcher_dir():
    """Restituisce la directory reale dove sta il launcher (compilato o .py)."""
    if getattr(sys, 'frozen', False):
        # PyInstaller: ritorna la cartella dell'eseguibile reale
        return os.path.dirname(sys.executable)
    else:
        # .py normale
        return os.path.dirname(os.path.abspath(__file__))

def resource_path(relative_path):
    """
    Percorso assoluto per le risorse come logo, sia .py che PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # PyInstaller usa _MEIPASS per i file estratti temporaneamente
        return os.path.join(sys._MEIPASS, relative_path)
    else:
        return os.path.join(get_launcher_dir(), relative_path)

def compare_versions(version1, version2):
    """
    Confronta due versioni semantiche (es: "3.2" vs "3.1").
    Restituisce 1 se version1 > version2, -1 se version1 < version2, 0 se uguali.
    """
    try:
        v1_parts = list(map(int, version1.split('.')))
        v2_parts = list(map(int, version2.split('.')))
        
        # Assicuriamoci che abbiano la stessa lunghezza
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        
        return 0
    except:
        # Se c'è un errore nel parsing, considera le versioni come stringhe
        if version1 > version2:
            return 1
        elif version1 < version2:
            return -1
        return 0

def get_latest_stable_version(tags):
    """
    Trova l'ultima versione stabile tra i tag.
    Ignora le versioni beta/prerelease se presenti nel formato.
    """
    stable_versions = []
    
    for tag in tags:
        tag_name = tag.get('name', '').lstrip('v').lower()
        
        # Ignora tag che contengono indicazioni di beta/alpha/rc
        if any(beta_indicator in tag_name for beta_indicator in 
               ['beta', 'alpha', 'rc', 'pre', 'dev', 'test']):
            continue
            
        # Verifica che sia una versione valida (solo numeri e punti)
        clean_tag = ''.join(c for c in tag_name if c.isdigit() or c == '.')
        if clean_tag and clean_tag.replace('.', '').isdigit():
            stable_versions.append((clean_tag, tag))
    
    if not stable_versions:
        return None, None
    
    # Trova la versione stabile più recente
    latest_stable = max(stable_versions, key=lambda x: list(map(int, x[0].split('.'))))
    return latest_stable[0], latest_stable[1].get('tarball_url')

def check_for_updates(lang):
    """
    Controlla se ci sono aggiornamenti disponibili su GitHub.
    Restituisce: (status, latest_stable_version, latest_tag_url, all_tags)
    status può essere:
      "update_available" - Aggiornamento disponibile
      "beta_version" - Versione corrente > ultima stabile (beta)
      "up_to_date" - Versione aggiornata
      "error" - Errore nel controllo
    """
    print(f"{get_translation('checking_for', lang)} {CURRENT_VERSION}...")
    
    try:
        # Effettua la richiesta a GitHub API
        headers = {'User-Agent': 'MusicWavver-Launcher'}
        response = requests.get(GITHUB_TAGS_URL, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"Errore nella richiesta GitHub: {response.status_code}")
            return "error", None, None, None
        
        tags = response.json()
        if not tags:
            print(get_translation('no_tags', lang))
            return "up_to_date", None, None, None
        
        # Trova l'ultima versione stabile
        latest_stable, latest_stable_url = get_latest_stable_version(tags)
        
        if not latest_stable:
            print(get_translation('no_stable', lang))
            return "up_to_date", None, None, tags
        
        print(f"{get_translation('latest_found', lang)}: {latest_stable}")
        
        # Confronta con la versione corrente
        comparison = compare_versions(CURRENT_VERSION, latest_stable)
        
        if comparison < 0:
            # Versione corrente < ultima stabile → Aggiornamento disponibile
            print(f"{get_translation('update_found', lang)}: {CURRENT_VERSION} -> {latest_stable}")
            return "update_available", latest_stable, latest_stable_url, tags
        elif comparison > 0:
            # Versione corrente > ultima stabile → Probabile versione beta
            return "beta_version", latest_stable, latest_stable_url, tags
        else:
            # Versioni uguali → Aggiornato
            print(f"{get_translation('up_to_date', lang)}: {CURRENT_VERSION}")
            return "up_to_date", latest_stable, None, tags
            
    except requests.exceptions.Timeout:
        print(get_translation('timeout', lang))
        return "error", None, None, None
    except requests.exceptions.RequestException as e:
        print(f"{get_translation('connection_error', lang)}: {e}")
        return "error", None, None, None
    except Exception as e:
        print(f"{get_translation('check_error', lang)}: {e}")
        return "error", None, None, None

def start_app():
    """Avvia l'app principale, sia binario Linux che app.py"""
    launcher_dir = get_launcher_dir()

    linux_exec = os.path.join(launcher_dir, "MUSIC WAVVER")  # eseguibile Linux
    py_file = os.path.join(launcher_dir, "app.py")           # file Python

    try:
        if platform.system() == "Linux":
            if os.path.exists(linux_exec):
                subprocess.Popen([linux_exec])
                return
            elif os.path.exists(py_file):
                subprocess.Popen(["python3", py_file])
                return
        elif platform.system() == "Windows":
            win_exec = os.path.join(launcher_dir, "MUSIC WAVVER.exe")
            if os.path.exists(win_exec):
                subprocess.Popen([win_exec])
                return
            elif os.path.exists(py_file):
                subprocess.Popen(["python", py_file])
                return
        print("ERRORE: app non trovata")
    except Exception as e:
        print("ERRORE avvio app:", e)


def open_github_release(lang):
    """Apre l'ultima release di GitHub nel browser."""
    print(f"{get_translation('opening_release', lang)}: {GITHUB_LATEST_RELEASE_URL}")
    webbrowser.open(GITHUB_LATEST_RELEASE_URL)

def ease_out_quart(t):
    t = 1 - t
    return 1 - (t * t * t * t)

def get_center():
    """Calcola la posizione centrata della finestra."""
    import tkinter as tk
    temp_root = tk.Tk()
    temp_root.withdraw()
    screen_width = temp_root.winfo_screenwidth()
    screen_height = temp_root.winfo_screenheight()
    temp_root.destroy()
    
    x = int((screen_width - WIDTH) / 2)
    y = int((screen_height - HEIGHT) / 2)
    return f"{WIDTH}x{HEIGHT}+{x}+{y}"

def show_update_screen(root, latest_stable_version, lang):
    """
    Mostra la schermata di aggiornamento disponibile.
    """
    # Nascondi gli elementi precedenti
    for widget in root.winfo_children():
        widget.destroy()
    
    # Imposta sfondo
    root.configure(fg_color="#2B2B2B")
    
    # Titolo aggiornamento
    update_title = ctk.CTkLabel(
        root,
        text=get_translation('update_title', lang),
        font=("Segoe UI", 24, "bold"),
        text_color="#FF6B6B"
    )
    update_title.place(x=WIDTH/2, y=80, anchor="center")
    
    # Versione corrente vs nuova
    version_info = ctk.CTkLabel(
        root,
        text=f"{get_translation('current_version', lang)}: {CURRENT_VERSION}\n{get_translation('latest_stable', lang)}: {latest_stable_version}",
        font=("Segoe UI", 16),
        text_color="#FFFFFF"
    )
    version_info.place(x=WIDTH/2, y=140, anchor="center")
    
    # Messaggio informativo
    info_text = ctk.CTkLabel(
        root,
        text=get_translation('update_message', lang),
        font=("Segoe UI", 14),
        text_color="#CCCCCC"
    )
    info_text.place(x=WIDTH/2, y=200, anchor="center")
    
    # Pulsante Scarica Aggiornamento
    download_btn = ctk.CTkButton(
        root,
        text=get_translation('download_stable', lang),
        font=("Segoe UI", 16, "bold"),
        fg_color="#4CAF50",
        hover_color="#45a049",
        width=250,
        height=45,
        command=lambda: open_github_release(lang)
    )
    download_btn.place(x=WIDTH/2, y=280, anchor="center")
    
    # Pulsante Continua Senza Aggiornare
    continue_btn = ctk.CTkButton(
        root,
        text=get_translation('continue_without', lang),
        font=("Segoe UI", 14),
        fg_color="#555555",
        hover_color="#666666",
        width=250,
        height=40,
        command=lambda: [root.destroy(), start_app()]
    )
    continue_btn.place(x=WIDTH/2, y=340, anchor="center")
    
    # Note
    note_text = ctk.CTkLabel(
        root,
        text=get_translation('update_note', lang),
        font=("Segoe UI", 12),
        text_color="#888888"
    )
    note_text.place(x=WIDTH/2, y=400, anchor="center")

def show_beta_warning_screen(root, latest_stable_version, lang):
    """
    Mostra la schermata di avviso per versione beta.
    """
    # Nascondi gli elementi precedenti
    for widget in root.winfo_children():
        widget.destroy()
    
    # Imposta sfondo
    root.configure(fg_color="#2B2B2B")
    
    # Titolo avviso beta
    beta_title = ctk.CTkLabel(
        root,
        text=get_translation('beta_title', lang),
        font=("Segoe UI", 24, "bold"),
        text_color="#FFA726"  # Arancione per avviso
    )
    beta_title.place(x=WIDTH/2, y=70, anchor="center")
    
    # Icona di avvertimento (simulata con testo)
    warning_symbol = ctk.CTkLabel(
        root,
        text="⚠️",
        font=("Segoe UI", 48),
        text_color="#FFA726"
    )
    warning_symbol.place(x=WIDTH/2, y=120, anchor="center")
    
    # Versione corrente vs stabile
    version_info = ctk.CTkLabel(
        root,
        text=f"{get_translation('beta_current', lang)}: {CURRENT_VERSION} (beta)\n{get_translation('latest_stable', lang)}: {latest_stable_version}",
        font=("Segoe UI", 16),
        text_color="#FFFFFF"
    )
    version_info.place(x=WIDTH/2, y=180, anchor="center")
    
    # Messaggio di avviso
    warning_text = ctk.CTkLabel(
        root,
        text=get_translation('beta_warning', lang),
        font=("Segoe UI", 14),
        text_color="#FFCC80",
        justify="center"
    )
    warning_text.place(x=WIDTH/2, y=240, anchor="center")
    
    # Pulsante Torna all'Ultima Versione Stabile
    stable_btn = ctk.CTkButton(
        root,
        text=get_translation('return_stable', lang),
        font=("Segoe UI", 16, "bold"),
        fg_color="#4CAF50",
        hover_color="#45a049",
        width=280,
        height=45,
        command=lambda: open_github_release(lang)
    )
    stable_btn.place(x=WIDTH/2, y=320, anchor="center")
    
    # Pulsante Accetta il Rischio e Continua
    continue_btn = ctk.CTkButton(
        root,
        text=get_translation('accept_risk', lang),
        font=("Segoe UI", 14),
        fg_color="#D32F2F",  # Rosso per indicare rischio
        hover_color="#C62828",
        width=280,
        height=40,
        command=lambda: [root.destroy(), start_app()]
    )
    continue_btn.place(x=WIDTH/2, y=380, anchor="center")
    
    # Note aggiuntive
    note_text = ctk.CTkLabel(
        root,
        text=get_translation('beta_note', lang),
        font=("Segoe UI", 12),
        text_color="#888888",
        justify="center"
    )
    note_text.place(x=WIDTH/2, y=440, anchor="center")

def show_error_screen(root, lang):
    """
    Mostra la schermata di errore nel controllo aggiornamenti.
    """
    # Nascondi gli elementi precedenti
    for widget in root.winfo_children():
        widget.destroy()
    
    # Imposta sfondo
    root.configure(fg_color="#2B2B2B")
    
    # Titolo errore
    error_title = ctk.CTkLabel(
        root,
        text=get_translation('error_title', lang),
        font=("Segoe UI", 22, "bold"),
        text_color="#FF5252"
    )
    error_title.place(x=WIDTH/2, y=120, anchor="center")
    
    # Messaggio di errore
    error_text = ctk.CTkLabel(
        root,
        text=get_translation('error_message', lang),
        font=("Segoe UI", 14),
        text_color="#CCCCCC",
        justify="center"
    )
    error_text.place(x=WIDTH/2, y=200, anchor="center")
    
    # Pulsante Riprova
    retry_btn = ctk.CTkButton(
        root,
        text=get_translation('retry_button', lang),
        font=("Segoe UI", 14, "bold"),
        fg_color="#2196F3",
        hover_color="#1976D2",
        width=180,
        height=40,
        command=lambda: restart_launcher()
    )
    retry_btn.place(x=WIDTH/2, y=290, anchor="center")
    
    # Pulsante Continua Comunque
    continue_btn = ctk.CTkButton(
        root,
        text=get_translation('continue_anyway', lang),
        font=("Segoe UI", 14),
        fg_color="#555555",
        hover_color="#666666",
        width=180,
        height=40,
        command=lambda: [root.destroy(), start_app()]
    )
    continue_btn.place(x=WIDTH/2, y=350, anchor="center")
    
    # Note
    note_text = ctk.CTkLabel(
        root,
        text=get_translation('error_note', lang),
        font=("Segoe UI", 12),
        text_color="#888888"
    )
    note_text.place(x=WIDTH/2, y=410, anchor="center")

def restart_launcher():
    """Riavvia il launcher."""
    print("Riavvio del launcher...")
    python = sys.executable
    subprocess.Popen([python] + sys.argv)
    sys.exit()

def main():
    # Rileva lingua del sistema
    lang = get_system_language()
    print(f"Lingua selezionata: {lang}")
    
    # Stampa info di debug
    print("=" * 50)
    print("Music Wavver Launcher")
    print(f"Versione: {CURRENT_VERSION}")
    print(f"Python version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print("=" * 50)
    
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.geometry(get_center())
    root.title(get_translation('window_title', lang))
    root.resizable(False, False)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 1)

    # ----- LOGO -----
    logo_path = resource_path("Logo.png")
    print(f"Percorso logo: {logo_path}")
    
    try:
        pil_image = Image.open(logo_path)
        img = ctk.CTkImage(
            light_image=pil_image,
            dark_image=pil_image,
            size=(200, 200)
        )
    except FileNotFoundError:
        print(f"ERRORE: Logo.png non trovato in: {logo_path}")
        print("Assicurati che Logo.png sia nella stessa cartella.")
        root.destroy()
        return 
    except Exception as e:
        print(f"Errore nel caricamento del logo: {e}")
        root.destroy()
        return

    logo = ctk.CTkLabel(root, text="", image=img)
    logo.place(x=WIDTH/2, y=LOGO_START_Y, anchor="n")

    # ----- SCRITTA TITOLO -----
    title = ctk.CTkLabel(
        root,
        text=get_translation('app_name', lang),
        font=("Segoe UI", 28, "bold"),
        text_color="#000000"
    )
    title.place(x=WIDTH/2, y=TITLE_CENTER_Y, anchor="center")
    
    # ----- SCRITTA CONTROLLO AGGIORNAMENTI -----
    update_label = ctk.CTkLabel(
        root,
        text="",
        font=("Segoe UI", 14),
        text_color="#666666"
    )
    update_label.place(x=WIDTH/2, y=TITLE_CENTER_Y + 50, anchor="center")

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

    time.sleep(0.5)
    
    # 3. MOSTRA MESSAGGIO CONTROLLO AGGIORNAMENTI
    update_label.configure(text=get_translation('checking_updates', lang))
    root.update()
    
    # 4. CONTROLLA AGGIORNAMENTI
    status, latest_stable, latest_url, all_tags = check_for_updates(lang)
    
    if status == "update_available":
        # Mostra schermata di aggiornamento disponibile
        update_label.configure(text=get_translation('update_available', lang))
        root.update()
        time.sleep(1)
        show_update_screen(root, latest_stable, lang)
        
    elif status == "beta_version":
        # Mostra schermata di avviso beta
        update_label.configure(text=get_translation('beta_detected', lang))
        root.update()
        time.sleep(1)
        show_beta_warning_screen(root, latest_stable, lang)
        
    elif status == "up_to_date":
        # Continua con l'applicazione
        update_label.configure(text=get_translation('version_updated', lang))
        root.update()
        time.sleep(1.5)
        
        # FADE-OUT FINESTRA
        FADE_OUT_DURATION = 0.3
        OUT_FRAMES = int(FADE_OUT_DURATION * FPS)

        for frame in range(OUT_FRAMES + 1):
            alpha = 1 - (frame / OUT_FRAMES)
            root.attributes("-alpha", alpha)
            root.update()
            time.sleep(1/FPS)

        root.destroy()
        print(get_translation('starting_app', lang))
        start_app()
        
    else:  # status == "error"
        # Mostra schermata di errore
        update_label.configure(text=get_translation('error_checking', lang))
        root.update()
        time.sleep(1)
        show_error_screen(root, lang)
    
    root.mainloop()

if __name__ == "__main__":
    main()
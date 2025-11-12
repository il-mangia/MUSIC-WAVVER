# 🎧 Music Wavver V2.5  

[➡️ Vai ai Requisiti](#🛠️-system-requirements) | [⬇️ Vai all’Installazione](#📦-installation) | [⚖️ Vai al Disclaimer](#⚖️-legal-disclaimer)

**Developed and tested on Ubuntu 25.10 and Windows 11**  
Made with ❤️ in **Italy 🇮🇹**

---

**Music Wavver** è un’app desktop costruita per cercare, scaricare e convertire tracce audio di alta qualità da YouTube con stile e precisione.  
Sviluppata in **Python 3**, **yt-dlp** e **ttkbootstrap**, combina un’interfaccia moderna con un backend potente per un’estrazione veloce, stabile e affidabile.

---

## ✨ Main Features  

* **Powerful Engine (yt-dlp):** Usa la libreria `yt-dlp` per la massima compatibilità e affidabilità.  
* **High-Quality Conversion:** Grazie a **FFmpeg**, consente la conversione audio in:
  * **WAV** (Lossless)
  * **FLAC** (Lossless)
  * **MP3** (Alta qualità, fino a 320 kbps)
* **Modern GUI:** Interfaccia elegante con `ttkbootstrap`, tabella risultati (**Treeview**) e design reattivo.  
* **Advanced Control:** Barra di progresso in tempo reale e limitatore di velocità (**Rate Limiting**).  
* **Flexible Search:** Supporta sia la ricerca per parole chiave che l’inserimento diretto di URL YouTube.  
* **AI Title Cleanup:** Rinomina automaticamente i brani in formato “Artista – Titolo” grazie a **Google Gemini 1.5 Flash** (opzionale, con API key utente).

---

## 🛠️ System Requirements  

- **DENO JS (yt_dlp)**: [Installazione ufficiale](https://docs.deno.com/runtime/getting_started/installation/)  
- **FFmpeg** (incluso nel file ZIP)  
- Compatibile con **Windows x64** e **Linux x64**

---

## 📦 Installation  

### 🪟 Windows  
1. Scarica l’ultima release `.zip`.  
2. Estrai il contenuto in una cartella a scelta.  
3. **Importante:** L’eseguibile e la cartella `ffmpeg` devono trovarsi nella stessa directory.

### 🐧 Linux / macOS  
1. Scarica l’ultima release `.zip`.  
2. Estrai i file ovunque.  
3. **Importante:** L’eseguibile e la cartella `ffmpeg` devono trovarsi nella stessa directory.

---

## ⚖️ Legal Disclaimer  

### Built-in License Agreement  
Music Wavver include un **accordo legale integrato** che appare automaticamente al primo avvio.  
L’utente deve **leggerlo e accettarlo** prima di usare il programma.  
Se non accettato, l’applicazione si chiude immediatamente.  
Questo garantisce che ogni utente comprenda la piena responsabilità legale riguardo ai contenuti scaricati.

### Copyright Notice  
Gli utenti sono **unicamente responsabili** del rispetto delle leggi sul copyright e dei Termini di Servizio di YouTube nel proprio Paese.  
Scaricando contenuti tramite questo software, l’utente conferma di avere il diritto o l’autorizzazione a farlo.  

**Music Wavver** e il suo sviluppatore (“Il Mangia”) **non sono responsabili** per abusi, violazioni di copyright o usi illeciti del programma.  
Questo strumento è fornito **“così com’è”**, solo per **uso personale, educativo e non commerciale**.  
Non viene garantita la legalità del download o della conversione di alcun contenuto specifico.

### About FFmpeg  
FFmpeg **non è sviluppato né di proprietà** di questo progetto.  
I binari sono inclusi solo per comodità.  
È un progetto open-source distribuito sotto **LGPL/GPL**, in base alla build.  

Per dettagli e codice sorgente, visita il [sito ufficiale di FFmpeg](https://ffmpeg.org).  
Usando Music Wavver, accetti i termini di licenza di FFmpeg.

---

**Developed in Italy 🇮🇹 — Built and Tested on Ubuntu 25.10 by Il Mangia — 2025**

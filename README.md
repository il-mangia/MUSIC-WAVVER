# 🎧 Music Wavver V2.0

Music Wavver V2.0 è l'applicazione desktop definitiva per la ricerca, il download e la conversione di tracce audio da YouTube. Sviluppato con **Python**, **yt-dlp** e **ttkbootstrap**, offre un'esperienza utente moderna, veloce e stabile per creare la tua collezione audio personale in alta qualità.

---

## ✨ Caratteristiche Principali

* **Motore Potente (yt-dlp):** Utilizza la robusta libreria `yt-dlp` per la massima compatibilità e affidabilità nell'estrazione audio da YouTube.
* **Conversione di Alta Qualità:** Sfrutta **FFmpeg** integrato per convertire l'audio scaricato nei formati:
    * **WAV** (Lossless)
    * **FLAC** (Lossless)
    * **MP3** (Alta Qualità, fino a 320 kbps)
* **GUI Moderna:** Interfaccia utente intuitiva e reattiva (`ttkbootstrap`) con una chiara visualizzazione dei risultati tramite tabella (**Treeview**).
* **Controllo Avanzato:** Include una barra di progresso in tempo reale e opzioni per impostare un limite di velocità di download (**Rate Limiting**).
* **Gestione Link e Ricerca:** Supporta sia la ricerca testuale che l'inserimento diretto di URL YouTube.

---

## 🛠️ Requisiti di Sistema

Per eseguire il codice sorgente, devi avere installato **Python 3.12+**

---

## 📦 Installazione e Setup

### 1. Windows
Per windows basta andare sull'ultima relase ed estrarre il contenuto dello zip del'ultima versione in una cartella a piacimento. **IMPORTANTE: L'ESEGUIBILE E LA CARTELLA DI FFMPEG DEVONO ESSERE SULLA STESSA DIR**.

### 2. Linux
Su linux, anche qui, andare sull'ultima relase ed estrarre il contenuto dello zip del'ultima versione in una cartella a piacimento. **IMPORTANTE: L'ESEGUIBILE E LA CARTELLA DI FFMPEG DEVONO ESSERE SULLA STESSA DIR**.

---

## ⚠️DISCLAIMER

### Attenzione Legale sul Contenuto Scaricato (Copyright)
È cruciale che gli utenti comprendano che la responsabilità legale del contenuto scaricato ricade esclusivamente su di loro.
L'utente finale di Music Wavver V2.0 è l'unico responsabile della verifica e del rispetto delle leggi vigenti in materia di copyright e dei termini di servizio delle piattaforme di provenienza (come YouTube) nel proprio Paese.
 Scaricando qualsiasi contenuto tramite questa applicazione, l'utente dichiara di possedere i diritti, il permesso o l'autorizzazione legale per eseguire tale download e di utilizzare il materiale in conformità con la legge.
 Questo strumento è fornito "così com'è" e ha il solo scopo di facilitare l'accesso ai dati pubblici delle piattaforme. Lo sviluppatore non è responsabile per l'uso illecito o la violazione di copyright che gli utenti potrebbero commettere utilizzando l'applicazione. Non garantiamo la legalità di scaricare qualsiasi contenuto.
Né gli sviluppatori di Music Wavver V2.0 né gli sviluppatori delle librerie di terze parti utilizzate (inclusi, ma non limitati a, yt-dlp e FFmpeg) sono consapevoli o responsabili dell'uso che l'utente fa dei file scaricati.
Queste librerie sono strumenti generici per l'elaborazione dei dati e dei media e non hanno alcun controllo o coinvolgimento sul copyright del contenuto che viene elaborato tramite di esse. La responsabilità legale rimane interamente a carico dell'utente che avvia il download.

### ffmpeg
Desideriamo chiarire che FFmpeg non è un software sviluppato né di proprietà di questo progetto (Music Wavver). I binari di FFmpeg sono inclusi a scopo di comodità e funzionalità. Ringraziamo vivamente gli sviluppatori, i contributori e la comunità di FFmpeg per aver creato e mantenuto questo potente framework multimediale open source.
FFmpeg è un progetto open source distribuito sotto la licenza LGPL/GPL (a seconda delle opzioni di compilazione).
Per maggiori informazioni sul progetto, sulla licenza e sul codice sorgente, si prega di visitare il sito ufficiale di FFmpeg.
L'utente finale è responsabile di accettare e rispettare i termini di licenza di FFmpeg.

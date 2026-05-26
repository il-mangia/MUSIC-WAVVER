# 🎵 Music Wavver 6 — API Architecture & Workflow

Questo documento descrive in dettaglio il funzionamento interno di **Music Wavver 6**, spiegando come l'applicazione interagisce con le diverse API esterne per completare il flusso di ricerca, cross-referencing e download dei brani musicali.

---

## 📌 Indice
1. [Panoramica dell'Architettura](#-panoramica-dellarchitettura)
2. [Il Ruolo Cruciale del Codice ISRC](#-il-ruolo-cruciale-del-codice-isrc)
3. [Flusso dei Dati Passo-Passo](#-flusso-dei-dati-passo-passo)
4. [Dettaglio degli Endpoint API](#-dettaglio-degli-endpoint-api)
5. [Tecnologie e Librerie Ausiliarie](#-tecnologie-e-librerie-ausiliarie)

---

## 🏗️ Panoramica dell'Architettura

Music Wavver 6 non ospita file musicali e non esegue download diretti dalle piattaforme di streaming tradizionali. Funziona invece come un **motore di elaborazione e conversione** che mette in comunicazione tre ecosistemi differenti:

1. **Spotify / Deezer:** Utilizzati come sorgenti per la ricerca testuale e la risoluzione dei metadati (copertine, titoli, album).
2. **Codice ISRC:** Il ponte standard internazionale che garantisce l'univocità del brano tra piattaforme diverse.
3. **Monochrome API (Qobuz Back-end):** La sorgente fisica da cui viene prelevato il flusso audio ad alta fedeltà (Lossless).

[User Input] ──> [Deezer/Spotify API] ──> [Estrazione ISRC]
│
▼
[File Finale] <── [FFmpeg / Mutagen] <── [Monochrome API]


---

## 🔑 Il Ruolo Cruciale del Codice ISRC

L'**ISRC** (*International Standard Recording Code*) è l'equivalente del codice fiscale per una traccia audio. 
Poiché piattaforme diverse (es. Deezer e Qobuz) catalogano gli stessi brani con ID interni differenti, la ricerca per "Titolo - Artista" genererebbe inevitabilmente falsi positivi o disallineamenti (es. scaricare una versione live, un remix o una traccia omonima).

L'applicazione risolve questo problema **imponendo l'ISRC come chiave di ricerca universale** per il download.

---

## 🔄 Flusso dei Dati Passo-Passo

Il ciclo di vita di una richiesta all'interno del programma si articola in 4 macro-fasi gestite in background tramite thread dedicati (`QThread`):

### 1. Fase di Ricerca (SearchWorker)
* **Input:** L'utente inserisce un testo libero o un URL (Spotify/Deezer).
* **Azione:** Il programma interroga l'endpoint di ricerca di Deezer o effettua lo scraping del link di Spotify.
* **Output:** Viene restituita una lista di tracce con i metadati di base e l'URL della copertina. Per ottimizzare le performance, la risoluzione dell'ISRC viene demandata alla fase successiva o parallelizzata tramite un `ThreadPoolExecutor`.

### 2. Risoluzione ISRC & Corrispondenza (DownloadWorker)
* **Azione:** Prima di avviare il download, il programma effettua una chiamata puntuale all'API di Deezer (`/track/{id}`) per estrarre il codice ISRC associato in modo univoco al brano selezionato.

### 3. Interrogazione del Gateway Monochrome
* **Azione A (Risoluzione ID):** Il codice ISRC viene inviato all'API di Monochrome (`/api/get-music?q={isrc}`). Il gateway risponde restituendo l'ID interno del brano presente sui server Qobuz (`q_id`).
* **Azione B (Generazione Stream):** Il programma invia una seconda richiesta (`/api/download-music?track_id={q_id}&quality=6`). Il parametro `quality=6` richiede la massima qualità audio disponibile (Lossless FLAC/WAV).
* **Output:** L'API restituisce un URL di streaming temporaneo e diretto al file binario.

### 4. Download, Conversione e Tagging
* **Download:** Il file audio viene scaricato a blocchi (*chunk streaming*) in una cartella temporanea.
* **Elaborazione (FFmpeg):** Se l'utente ha richiesto il formato MP3, viene invocato un sottoprocesso FFmpeg che codifica l'audio a `320kbps (libmp3lame)`. Se viene richiesto FLAC o WAV, il file viene copiato o re-incapsulato senza perdita di qualità.
* **Metadati (Mutagen):** Sui file MP3 vengono iniettati i tag ID3v2 (Titolo, Artista, Album) e l'immagine della copertina scaricata in precedenza.

---

## 🌐 Dettaglio degli Endpoint API

### 1. Deezer API (Pubblica)
* **Ricerca testo:** `https://api.deezer.com/search?q={query}`
* **Dettaglio traccia (ISRC):** `https://api.deezer.com/track/{deezer_id}`

### 2. Monochrome API (Gateway Musicale)
* **Lookup tramite ISRC:** ```http
  GET [https://qdl-api.monochrome.tf/api/get-music?q=](https://qdl-api.monochrome.tf/api/get-music?q=){isrc}&offset=0
Generazione URL di Download:

HTTP
GET [https://qdl-api.monochrome.tf/api/download-music?track_id=](https://qdl-api.monochrome.tf/api/download-music?track_id=){q_id}&quality=6

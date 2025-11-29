<p align="center">
  <img src="Logo.png" width="150" alt="Music Wavver Logo"/>
</p>

<h1 align="center">🎧 MUSIC WAVVER</h1>

[➡️ Go to Requirements](#️-system-requirements) | [⬇️ Go to Installation](#-installation) | [⚖️ Go to Disclaimer](#-legal-disclaimer)

**Developed and tested on Ubuntu 25.10 and Windows 11**  
Made with ❤️ in **Italy 🇮🇹**

---

**Music Wavver** is a desktop application built to search, download, and convert high-quality audio tracks from YouTube with style and precision.  
Developed with **Python 3**, **yt-dlp**, and **ttkbootstrap**, it combines a modern interface with a powerful backend for fast, stable, and reliable audio extraction.

---

## ✨ Main Features  

- **Powerful Engine (yt-dlp):** Uses the `yt-dlp` library for unmatched compatibility and reliability when extracting audio from YouTube.  
- **High-Quality Conversion:** Integrated **FFmpeg** allows conversion into:
  - **WAV** (Lossless)
  - **FLAC** (Lossless)
  - **MP3** (High quality, up to 320 kbps)
- **Modern GUI:** Sleek and intuitive interface powered by `ttkbootstrap`, featuring a clean results table (**Treeview**) and responsive design.  
- **Advanced Control:** Real-time progress bar and download speed limiter (**Rate Limiting**).  
- **Flexible Search:** Supports both keyword search and direct YouTube URL pasting.  
- **AI Title Cleanup:** Automatically renames tracks into the “Artist – Title” format using **Google Gemini 1.5 Flash** (optional, user-provided API key).

---

## 🛠️ System Requirements  

- **DENO JS (yt_dlp):** [Official installation guide](https://docs.deno.com/runtime/getting_started/installation/).
- ffmpeg (How to install below).

---

## 📦 Installation  

### 🪟 Windows  
1. [Download the latest `.zip` release](https://github.com/il-mangia/MUSIC-WAVVER/releases/latest)  
2. Extract it into any folder.  
3. **Important:** You need to install ffmpeg by cmd: (`winget install Gyan.FFmpeg`).

### 🐧 Linux / macOS  
1. [Download the latest `.zip` release](https://github.com/il-mangia/MUSIC-WAVVER/releases/latest)  
2. Extract it anywhere you want. 
3. **Important:** You need to install ffmpeg by cmd: (`sudo apt install ffmpeg`).
4. make the file executable (`chmod +x file`) (where "file" is the one you extracted before).

---

## ⚖️ Legal Disclaimer  

### Built-in License Agreement  
Music Wavver includes a **built-in legal agreement** that appears automatically on the first launch.  
The user must **read and accept it** before using the program.  
If not accepted, the application closes immediately.  
This ensures that every user understands their full legal responsibility regarding downloaded content.

### Copyright Notice  
Users are solely responsible for verifying and complying with copyright laws and YouTube’s Terms of Service in their country.  
By downloading any content through this software, the user confirms that they have the legal right, permission, or authorization to do so.  

Music Wavver and its developer (“Il Mangia”) are **not liable** for any misuse, copyright infringement, or legal violation committed through this program.  
This tool is provided **“as is”**, and is intended for **personal, educational, and non-commercial use** only.  
We do **not guarantee the legality** of downloading or converting any specific content.  
Neither the developer of Music Wavver nor the maintainers of third-party libraries (including `yt-dlp` and `FFmpeg`) are responsible for how downloaded media is used.  
All responsibility remains with the **end user**.

### About FFmpeg  
FFmpeg is **not developed or owned** by this project.  
Its binaries are included purely for convenience and functionality.  
FFmpeg is an open-source project distributed under **LGPL/GPL**, depending on the build configuration.  

We thank the FFmpeg team and community for their outstanding work.  
For licensing details and source code, visit the [official FFmpeg website](https://ffmpeg.org).  
By using Music Wavver, you accept the FFmpeg license terms.  

---

**Developed in Italy 🇮🇹 — Built and Tested on Ubuntu 25.10 by Il Mangia — 2025**

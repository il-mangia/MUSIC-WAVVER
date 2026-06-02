import yt_dlp
import os


def download_audio(artist: str, title: str, output_dir: str, filename_template: str) -> str | None:
    search_query = f"ytsearch1:{artist} - {title}"
    outtmpl = os.path.join(output_dir, f"{filename_template}.%(ext)s")
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": outtmpl,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "m4a",
            "preferredquality": "0",
        }],
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([search_query])
            candidates = sorted(
                [os.path.join(output_dir, f) for f in os.listdir(output_dir)
                 if os.path.isfile(os.path.join(output_dir, f))],
                key=os.path.getmtime, reverse=True
            )
            for c in candidates[:5]:
                if c.endswith((".m4a", ".webm", ".opus")):
                    return c
            return None
    except Exception:
        return None

import requests
from datetime import datetime, timezone

HEADERS_HTTP = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

COOKIES_DEEZER = {
    "captcha_verified_at": "1780071040497"
}

QOBUZ_APIS = [
    "https://qobuz.squid.wtf/api",
    "https://qobuz.kennyy.com.br/api",
    "https://qdl-api.monochrome.tf/api",
]

def _captcha_timestamp() -> str:
    return str(int(datetime.now(timezone.utc).timestamp() * 1000))

def fmt_dur(seconds: int) -> str:
    m, s = divmod(seconds, 60)
    return f"{m}:{s:02d}"

COVER_SIZES = {"small": "cover_small", "medium": "cover_medium", "large": "cover_large"}


def search_deezer_by_name(title: str, artist: str, cover_quality: str = "medium"):
    """Cerca un brano su Deezer tramite nome e artista per ottenere ISRC e ID."""
    q = f"{artist} {title}"
    url = f"https://api.deezer.com/search?q={requests.utils.quote(q)}"
    cover_key = COVER_SIZES.get(cover_quality, "cover_large")
    try:
        data = requests.get(url, headers=HEADERS_HTTP, cookies=COOKIES_DEEZER, timeout=10).json()
        items = data.get("data", [])
        if not items:
            return None
        
        # Prendi il primo risultato
        best = items[0]
        # Fetchiamo il dettaglio per avere l'ISRC
        t_info = requests.get(
            f"https://api.deezer.com/track/{best['id']}",
            headers=HEADERS_HTTP, cookies=COOKIES_DEEZER, timeout=10
        ).json()
        
        isrc = t_info.get("isrc")
        cover = t_info.get("album", {}).get(cover_key)
        
        # Se abbiamo l'ISRC, proviamo a prendere la copertina Qobuz via Monochrome
        if isrc:
            qobuz_cover = get_monochrome_cover(isrc)
            if qobuz_cover:
                cover = qobuz_cover

        return {
            "isrc":      isrc,
            "deezer_id": t_info.get("id"),
            "title":     t_info.get("title", title),
            "artist":    t_info.get("artist", {}).get("name", artist),
            "album":     t_info.get("album", {}).get("title", "—"),
            "duration":  fmt_dur(t_info.get("duration", 0)),
            "cover":     cover,
        }
    except Exception:
        return None

def get_track_detail(track_id: str, cover_quality: str = "medium"):
    """Ottiene i dettagli completi di un brano Deezer (ISRC, cover Qobuz, ecc.)."""
    cover_key = COVER_SIZES.get(cover_quality, "cover_large")
    url = f"https://api.deezer.com/track/{track_id}"
    try:
        t = requests.get(url, headers=HEADERS_HTTP, cookies=COOKIES_DEEZER, timeout=10).json()
        if "id" not in t:
            return None
        
        isrc = t.get("isrc")
        cover = t.get("album", {}).get(cover_key)
        if isrc:
            qobuz_cover = get_monochrome_cover(isrc)
            if qobuz_cover:
                cover = qobuz_cover

        return {
            "isrc":      isrc,
            "deezer_id": t["id"],
            "title":     t.get("title", "—"),
            "artist":    t.get("artist", {}).get("name", "—"),
            "album":     t.get("album", {}).get("title", "—"),
            "duration":  fmt_dur(t.get("duration", 0)),
            "cover":     cover,
        }
    except Exception:
        return None

def handle_deezer_url(track_id: str):
    """Gestisce un link diretto Deezer."""
    res = get_track_detail(track_id)
    return [res] if res else None

def get_deezer_playlist(playlist_id: str, log_cb=None, cover_quality: str = "medium") -> list:
    """Recupera i brani di una playlist Deezer pubblica (no auth richiesta)."""
    url = f"https://api.deezer.com/playlist/{playlist_id}/tracks?limit=100"
    tracks = []
    while url:
        try:
            data = requests.get(url, headers=HEADERS_HTTP, cookies=COOKIES_DEEZER, timeout=12).json()
        except Exception as e:
            if log_cb:
                log_cb(f"[PLAYLIST] ❌ Errore Deezer: {e}")
            break

        if data.get("error"):
            if log_cb:
                log_cb(f"[PLAYLIST] ❌ Deezer API error: {data['error']}")
            break

        for item in data.get("data", []):
            tid = item.get("id")
            if not tid:
                continue
            detail = get_track_detail(tid, cover_quality)
            if detail:
                tracks.append(detail)
                if log_cb:
                    log_cb(f"[PLAYLIST] ✓ {detail['title']} — {detail['artist']}")

        # Paginazione
        url = data.get("next")

    return tracks if tracks else None


def get_deezer_album(album_id: str, log_cb=None, cover_quality: str = "medium") -> list:
    """Recupera i brani di un album Deezer."""
    url = f"https://api.deezer.com/album/{album_id}/tracks?limit=100"
    tracks = []
    while url:
        try:
            data = requests.get(url, headers=HEADERS_HTTP, cookies=COOKIES_DEEZER, timeout=12).json()
        except Exception as e:
            if log_cb:
                log_cb(f"[ALBUM] ❌ Errore Deezer: {e}")
            break

        if data.get("error"):
            if log_cb:
                log_cb(f"[ALBUM] ❌ Deezer API error: {data['error']}")
            break

        for item in data.get("data", []):
            tid = item.get("id")
            if not tid:
                continue
            detail = get_track_detail(tid, cover_quality)
            if detail:
                tracks.append(detail)
                if log_cb:
                    log_cb(f"[ALBUM] ✓ {detail['title']} — {detail['artist']}")

        url = data.get("next")

    return tracks if tracks else None


def get_monochrome_cover(isrc: str):
    """Ottiene la copertina Qobuz (thumbnail) con failover su più API."""
    for base in QOBUZ_APIS:
        cookies = None
        if "squid.wtf" in base or "kennyy.com.br" in base:
            cookies = {"captcha_verified_at": _captcha_timestamp()}
        url = f"{base}/get-music?q={isrc}&offset=0"
        try:
            r = requests.get(url, headers=HEADERS_HTTP, cookies=cookies, timeout=10).json()
            if r.get("success"):
                tracks = r.get("data", {}).get("tracks", {}).get("items", [])
                if tracks:
                    thumb = tracks[0].get("album", {}).get("image", {}).get("thumbnail")
                    if thumb:
                        return thumb
                    large = tracks[0].get("album", {}).get("image", {}).get("large")
                    return large
        except Exception:
            continue
    return None

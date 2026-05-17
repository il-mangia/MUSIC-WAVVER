import requests
import re
import json
from concurrent.futures import ThreadPoolExecutor
from deezertrack import search_deezer_by_name

HEADERS_HTTP = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_spotify_data(sp_type: str, sp_id: str):
    """Estrae i dati dall'embed di Spotify senza bisogno di token."""
    url = f"https://open.spotify.com/embed/{sp_type}/{sp_id}"
    try:
        r = requests.get(url, headers=HEADERS_HTTP, timeout=12)
        r.raise_for_status()
        
        # Prova con __NEXT_DATA__
        m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', r.text)
        if m:
            data = json.loads(m.group(1))
            # Path per Next.js
            entity = data.get('props', {}).get('pageProps', {}).get('state', {}).get('data', {}).get('entity')
            if entity: return entity
            # Path alternativo
            entity = data.get('props', {}).get('pageProps', {}).get('entity')
            if entity: return entity

        # Prova con il nuovo tag "resource"
        m = re.search(r'<script id="resource" type="application/json">(.*?)</script>', r.text)
        if m:
            data = json.loads(m.group(1))
            return data

        # Prova generica per qualsiasi JSON in un tag script di tipo application/json
        # (alcune versioni dell'embed non hanno un ID specifico)
        scripts = re.findall(r'<script [^>]*type="application/json"[^>]*>(.*?)</script>', r.text)
        for s in scripts:
            try:
                data = json.loads(s)
                # Se il JSON contiene 'tracks' o 'name', è probabilmente quello giusto
                if 'tracks' in data or 'name' in data:
                    return data
            except:
                continue

        return None
    except Exception:
        return None

def handle_spotify(sp_type: str, sp_id: str, log_callback=None):
    """Gestisce i link Spotify risolvendoli tramite scraping e ricerca Deezer."""
    entity = scrape_spotify_data(sp_type, sp_id)
    if not entity:
        return None

    if sp_type == "track":
        return _handle_track(entity, log_callback)
    elif sp_type == "album":
        return _handle_album(entity, log_callback)
    elif sp_type == "playlist":
        return _handle_playlist(entity, log_callback)
    return None

def _handle_track(entity, log_callback):
    title = entity.get("title") or entity.get("name", "—")
    
    artists_data = entity.get("artists", [])
    if artists_data and isinstance(artists_data, list):
        artist = artists_data[0].get("name", "—")
    else:
        artist = entity.get("subtitle") or entity.get("artistName", "—")
    
    if artist and "," in artist: artist = artist.split(",")[0].strip()
    if artist: artist = artist.replace("\xa0", " ").strip()

    if log_callback: log_callback(f"[SEARCH] Risoluzione: {artist} - {title}")
    
    res = search_deezer_by_name(title, artist)
    return [res] if res else None

def _handle_album(entity, log_callback):
    items = []
    if "tracks" in entity and "items" in entity["tracks"]:
        items = entity["tracks"]["items"]
    elif "trackList" in entity:
        items = entity["trackList"]
    elif isinstance(entity.get("tracks"), list):
        items = entity["tracks"]
    
    if not items:
        return None

    if log_callback: log_callback(f"[SEARCH] Avvio risoluzione parallela album ({len(items)} brani)...")

    def resolve_one(item):
        title = item.get("title") or item.get("name")
        artists_data = item.get("artists", [])
        if artists_data and isinstance(artists_data, list):
            artist = artists_data[0].get("name")
        else:
            artist = item.get("subtitle") or item.get("artistName") or entity.get("subtitle")
        
        if artist and "," in artist: artist = artist.split(",")[0].strip()
        if artist: artist = artist.replace("\xa0", " ").strip()
        
        if not title or not artist:
            return None

        res = search_deezer_by_name(title, artist)
        if res:
            if log_callback: log_callback(f"[SEARCH] Track: {res['title']}")
            return res
        return None

    tracks = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(resolve_one, items))
        tracks = [r for r in results if r]
    return tracks if tracks else None

def _handle_playlist(entity, log_callback):
    items = []
    if "tracks" in entity and "items" in entity["tracks"]:
        items = entity["tracks"]["items"]
    elif "trackList" in entity:
        items = entity["trackList"]
    elif isinstance(entity.get("tracks"), list):
        items = entity["tracks"]
    
    if not items:
        if log_callback: log_callback("[SEARCH] ❌ Nessun brano trovato nella playlist Spotify.")
        return None

    if log_callback: log_callback(f"[SEARCH] Avvio risoluzione parallela di {len(items)} brani...")

    def resolve_one(item):
        track_node = item.get("track") if isinstance(item.get("track"), dict) else item
        title = track_node.get("title") or track_node.get("name")
        artists_data = track_node.get("artists", [])
        if artists_data and isinstance(artists_data, list):
            artist = artists_data[0].get("name")
        else:
            artist = track_node.get("subtitle") or track_node.get("artistName")
        
        if artist and "," in artist: artist = artist.split(",")[0].strip()
        if artist: artist = artist.replace("\xa0", " ").strip()

        if not title or not artist:
            return None

        res = search_deezer_by_name(title, artist)
        if res:
            if log_callback: log_callback(f"[SEARCH] ✓ {res['title']}")
            return res
        return None

    tracks = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(resolve_one, items))
        tracks = [r for r in results if r]
            
    return tracks if tracks else None

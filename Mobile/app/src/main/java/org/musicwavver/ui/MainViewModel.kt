package org.musicwavver.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import org.musicwavver.MusicWavverApp
import org.musicwavver.data.FavoriteTrack
import org.musicwavver.model.*
import org.musicwavver.network.RetrofitClient
import org.musicwavver.network.SpotifyConfig
import org.musicwavver.player.PlaybackService

enum class PlayMode { NONE, ALL, ONE }

sealed class UiState {
    object Idle    : UiState()
    object Loading : UiState()
    data class Results(
        val tracks: List<Track> = emptyList(),
        val artists: List<ArtistSearchItem> = emptyList(),
        val albums: List<AlbumSearchItem> = emptyList(),
        val playlists: List<DeezerPlaylistSearchItem> = emptyList(),
        val filter: String = "all"
    ) : UiState()
    data class Error(val message: String) : UiState()
}

data class HomeCategory(val id: Int, val name: String, val emoji: String, val tracks: List<Track>)

sealed class HomeState {
    object Loading : HomeState()
    data class Ready(
        val chartTracks: List<Track>,
        val categories: List<HomeCategory>,
        val playlists: List<DeezerPlaylist>
    ) : HomeState()
    data class Error(val msg: String) : HomeState()
}

sealed class PlaylistViewState {
    object Hidden  : PlaylistViewState()
    object Loading : PlaylistViewState()
    data class Ready(val title: String, val emoji: String, val tracks: List<Track>) : PlaylistViewState()
}

sealed class AlbumViewState {
    object Hidden : AlbumViewState()
    object Loading : AlbumViewState()
    data class Ready(
        val tracks: List<Track>,
        val title: String,
        val artistName: String,
        val artistId: Long = 0,
        val coverUrl: String?,
        val coverColor: Long = 0xFF0F0F1A,
        val albumId: Long = 0
    ) : AlbumViewState()
}

sealed class ArtistViewState {
    object Hidden : ArtistViewState()
    object Loading : ArtistViewState()
    data class Ready(
        val id: Long = 0,
        val name: String,
        val coverUrl: String?,
        val tracks: List<Track>,
        val monthlyListeners: String = "",
        val isFollowed: Boolean = false,
        val albums: List<DeezerArtistAlbum> = emptyList()
    ) : ArtistViewState()
}

sealed class SpotifyImportState {
    object Idle : SpotifyImportState()
    object Fetching : SpotifyImportState()
    data class Done(val imported: Int, val total: Int) : SpotifyImportState()
    data class Error(val msg: String) : SpotifyImportState()
}

class MainViewModel(application: Application) : AndroidViewModel(application) {

    private val api     = RetrofitClient.deezerApi
    private val lrcApi  = RetrofitClient.lrcApi
    private val favRepo = (application as MusicWavverApp).favoritesRepository
    private val persistence = (application as MusicWavverApp).persistence

    val uiState          = MutableStateFlow<UiState>(UiState.Idle)
    val homeState        = MutableStateFlow<HomeState>(HomeState.Loading)
    val playlistView     = MutableStateFlow<PlaylistViewState>(PlaylistViewState.Hidden)
    val albumView        = MutableStateFlow<AlbumViewState>(AlbumViewState.Hidden)
    val artistView       = MutableStateFlow<ArtistViewState>(ArtistViewState.Hidden)

    val currentTrack     = MutableStateFlow<Track?>(null)
    val isPlaying        = MutableStateFlow(false)
    val currentPosition  = MutableStateFlow(0L)
    val duration         = MutableStateFlow(0L)
    val favorites        = MutableStateFlow<List<FavoriteTrack>>(emptyList())
    val showExpanded     = MutableStateFlow(false)
    val resolving        = MutableStateFlow(false)
    val resolvingIndex   = MutableStateFlow<Long?>(null)
    val shuffleEnabled   = MutableStateFlow(false)
    val repeatMode     = MutableStateFlow(PlayMode.NONE)
    val recentlyPlayed   = MutableStateFlow<List<Track>>(emptyList())
    val searchHistory    = MutableStateFlow<List<SearchHistoryItem>>(emptyList())
    val searchSuggestions = MutableStateFlow<List<Any>>(emptyList())
    val sleepTimerRemaining = MutableStateFlow(0L)
    val showQueue        = MutableStateFlow(false)
    val showFullscreenLyrics = MutableStateFlow(false)

    val currentStreamSource = MutableStateFlow("")
    val youTubeVideoId = MutableStateFlow<String?>(null)
    val showYouTubePlayer = MutableStateFlow(false)

    val userPlaylists = MutableStateFlow<List<UserPlaylist>>(listOf(UserPlaylist(0, "Preferiti")))
    val isDarkMode = MutableStateFlow(true)
    val showSettings = MutableStateFlow(false)
    val showEqualizer = MutableStateFlow(false)

    val lyricsLines = MutableStateFlow<List<LyricLine>>(emptyList())
    val currentLyricIdx = MutableStateFlow(-1)
    private var lyricsSyncJob: Job? = null

    private val httpClient = okhttp3.OkHttpClient.Builder()
        .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
        .readTimeout(120, java.util.concurrent.TimeUnit.SECONDS)
        .followRedirects(true)
        .build()

    private val isrcCache   = HashMap<Long, String>()
    private val qobuzCache  = HashMap<String, String>()
    private val streamCache = HashMap<String, String>()

    var currentIndex = -1; private set
    var currentQueue = listOf<Track>(); private set
    private var shuffledQueue = listOf<Track>()
    private var shuffledIndex = 0

    private var _service: org.musicwavver.player.PlaybackService? = null
    private var lastStreamUrl: String? = null

    private var lastSearchQuery = ""
    private var searchJob: kotlinx.coroutines.Job? = null
    private var sleepJob: kotlinx.coroutines.Job? = null

    init {
        viewModelScope.launch { favRepo.getAll().collect { favorites.value = it } }
        viewModelScope.launch {
            currentTrack.collectLatest { track ->
                if (track != null) fetchLyrics(track)
            }
        }
        viewModelScope.launch {
            persistence.searchHistory().collect { searchHistory.value = it }
        }
        viewModelScope.launch {
            persistence.recentlyPlayed().collect { recentlyPlayed.value = it }
        }
        viewModelScope.launch {
            persistence.userPlaylists().collect { userPlaylists.value = it }
        }
        viewModelScope.launch {
            persistence.isDarkMode().collect { isDarkMode.value = it }
        }
        loadHome()
    }

    // ── HOME ────────────────────────────────────────────────────
    fun loadHome() = viewModelScope.launch {
        homeState.value = HomeState.Loading
        try {
            val chart     = async { api.getChartTracks() }
            val playlists = async { api.getChartPlaylists() }
            val dance     = async { api.getGenreChart(113) }
            val pop       = async { api.getGenreChart(132) }
            val rap       = async { api.getGenreChart(116) }
            val rock      = async { api.getGenreChart(152) }

            homeState.value = HomeState.Ready(
                chartTracks = chart.await().data?.take(15) ?: emptyList(),
                playlists   = playlists.await().data ?: emptyList(),
                categories  = listOf(
                    HomeCategory(113, "Dance",   "\uD83D\uDC83", dance.await().tracks?.data?.take(15) ?: emptyList()),
                    HomeCategory(132, "Pop",     "\u2728", pop.await().tracks?.data?.take(15)   ?: emptyList()),
                    HomeCategory(116, "Hip-Hop", "\uD83C\uDFA4", rap.await().tracks?.data?.take(15)   ?: emptyList()),
                    HomeCategory(152, "Rock",    "\uD83C\uDFB8", rock.await().tracks?.data?.take(15)  ?: emptyList())
                )
            )
        } catch (e: Exception) {
            homeState.value = HomeState.Error(e.message ?: "Errore di rete")
        }
    }

    fun closeAllOverlays() {
        showExpanded.value = false; showQueue.value = false; showSettings.value = false; showEqualizer.value = false
        showFullscreenLyrics.value = false
        playlistView.value = PlaylistViewState.Hidden
        albumView.value = AlbumViewState.Hidden
        artistView.value = ArtistViewState.Hidden
    }

    fun openPlaylist(id: Long, title: String, emoji: String) = viewModelScope.launch {
        closeAllOverlays()
        playlistView.value = PlaylistViewState.Loading
        try {
            val tracks = api.getPlaylistTracks(id).data ?: emptyList()
            currentQueue = tracks
            currentIndex = -1
            playlistView.value = PlaylistViewState.Ready(title, emoji, tracks)
        } catch (e: Exception) {
            playlistView.value = PlaylistViewState.Hidden
        }
    }

    fun openCategory(cat: HomeCategory) {
        closeAllOverlays()
        currentQueue = cat.tracks
        currentIndex = -1
        playlistView.value = PlaylistViewState.Ready(cat.name, cat.emoji, cat.tracks)
    }

    fun closePlaylist() { playlistView.value = PlaylistViewState.Hidden }

    fun openAlbum(tracks: List<Track>, title: String, artistName: String, artistId: Long = 0, coverUrl: String?, albumId: Long = 0) {
        closeAllOverlays()
        currentQueue = tracks
        currentIndex = -1
        albumView.value = AlbumViewState.Ready(tracks, title, artistName, artistId, coverUrl, albumId = albumId)
    }

    fun closeAlbum() { albumView.value = AlbumViewState.Hidden }

    fun openAlbumFromArtist(album: DeezerArtistAlbum, artistName: String) = viewModelScope.launch {
        closeAllOverlays()
        albumView.value = AlbumViewState.Loading
        try {
            val tracks = api.getAlbumTracks(album.id).data ?: emptyList()
            albumView.value = AlbumViewState.Ready(
                tracks = tracks,
                title = album.title,
                artistName = artistName,
                albumId = album.id,
                coverUrl = album.bestCover
            )
            currentQueue = tracks
            currentIndex = -1
            preWarmIsrc(tracks)
        } catch (_: Exception) {
            albumView.value = AlbumViewState.Hidden
        }
    }

    fun openArtist(name: String, coverUrl: String?, tracks: List<Track>) = viewModelScope.launch {
        closeAllOverlays()
        artistView.value = ArtistViewState.Loading
        var pic = coverUrl
        var fansCount = 0
        var artistId: Long? = null
        var resultTracks = tracks

        try {
            val search = api.searchArtists(name)
            val match = search.data?.firstOrNull { it.name.equals(name, ignoreCase = true) }
            if (match != null) {
                artistId = match.id
                fansCount = match.nbFan
                pic = match.pictureXl ?: match.pictureMedium ?: pic
            }
        } catch (_: Exception) { }

        val fans = when {
            fansCount >= 1_000_000 -> "${"%.1f".format(fansCount / 1_000_000f)} Mln"
            fansCount >= 1_000     -> "${fansCount / 1_000}K"
            else                   -> "${fansCount}"
        }
        var albums = emptyList<DeezerArtistAlbum>()

        if (artistId != null) {
            try { resultTracks = api.getArtistTopTracks(artistId).data ?: resultTracks } catch (_: Exception) { }
            try { albums = api.getArtistAlbums(artistId).data ?: emptyList() } catch (_: Exception) { }
        }

        artistView.value = ArtistViewState.Ready(artistId ?: 0, name, pic, resultTracks, "$fans ascoltatori mensili", false, albums)
        currentQueue = resultTracks
        preWarmIsrc(resultTracks)
    }

    fun closeArtist() { artistView.value = ArtistViewState.Hidden }

    fun toggleFollowArtist() {
        val cur = artistView.value as? ArtistViewState.Ready ?: return
        artistView.value = cur.copy(isFollowed = !cur.isFollowed)
    }

    // ── PLAYLISTS ─────────────────────────────────────────────────
    fun createPlaylist(name: String) {
        val list = userPlaylists.value.toMutableList()
        val id = (list.maxOfOrNull { it.id } ?: 0) + 1
        list.add(UserPlaylist(id, name))
        userPlaylists.value = list
        viewModelScope.launch { persistence.saveUserPlaylists(list) }
    }

    fun addToPlaylist(playlistId: Long, trackId: Long) {
        val list = userPlaylists.value.map { pl ->
            if (pl.id == playlistId) pl.copy(trackIds = pl.trackIds.toMutableSet().also { it.add(trackId) })
            else pl
        }
        userPlaylists.value = list
        viewModelScope.launch { persistence.saveUserPlaylists(list) }
    }

    fun removeFromPlaylist(playlistId: Long, trackId: Long) {
        val list = userPlaylists.value.map { pl ->
            if (pl.id == playlistId) pl.copy(trackIds = pl.trackIds.toMutableSet().also { it.remove(trackId) })
            else pl
        }
        userPlaylists.value = list
        viewModelScope.launch { persistence.saveUserPlaylists(list) }
    }

    fun deletePlaylist(plId: Long) {
        val list = userPlaylists.value.filter { it.id != plId }
        userPlaylists.value = list
        viewModelScope.launch { persistence.saveUserPlaylists(list) }
    }

    // ── SEARCH ──────────────────────────────────────────────────
    fun search(query: String, filter: String = "all") {
        if (query.isBlank()) return
        lastSearchQuery = query
        val h = searchHistory.value.toMutableList().also { it.removeAll { it.query == query }; it.add(0, SearchHistoryItem(query, System.currentTimeMillis())) }
        searchHistory.value = h.take(20)
        viewModelScope.launch { persistence.saveSearchHistory(searchHistory.value) }
        searchSuggestions.value = emptyList()
        uiState.value = UiState.Loading
        viewModelScope.launch {
            try {
                when (filter) {
                    "artist" -> {
                        val artists = api.searchArtists(query).data ?: emptyList()
                        uiState.value = UiState.Results(emptyList(), artists, filter = "artist")
                    }
                    "album" -> {
                        val albums = api.searchAlbums(query).data ?: emptyList()
                        uiState.value = UiState.Results(emptyList(), emptyList(), albums = albums, filter = "album")
                    }
                    "lyrics" -> {
                        val tracks = api.search(query).data ?: emptyList()
                        val matched = mutableListOf<Track>()
                        tracks.take(10).forEach { t ->
                            try {
                                val res = lrcApi.getLyrics(t.title, t.artist.name, t.album.title, t.duration)
                                val text = "${res.syncedLyrics ?: ""} ${res.plainLyrics ?: ""}"
                                if (text.contains(query, ignoreCase = true)) matched.add(t)
                            } catch (_: Exception) { }
                        }
                        if (matched.isEmpty()) {
                            uiState.value = UiState.Error("Nessuna canzone trovata per questo testo. Prova con meno parole.")
                        } else {
                            uiState.value = UiState.Results(matched, filter = filter)
                            preWarmIsrc(matched)
                        }
                    }
                    else -> {
                        val tracksDef = async { api.search(query) }
                        val artistsDef = async { api.searchArtists(query) }
                        val albumsDef = async { api.searchAlbums(query) }
                        val playlistsDef = async { api.searchPlaylists(query) }
                        val tracks = tracksDef.await().data ?: emptyList()
                        uiState.value = UiState.Results(
                            tracks = tracks,
                            artists = artistsDef.await().data ?: emptyList(),
                            albums = albumsDef.await().data ?: emptyList(),
                            playlists = playlistsDef.await().data ?: emptyList(),
                            filter = "all"
                        )
                        preWarmIsrc(tracks)
                    }
                }
            } catch (e: Exception) {
                uiState.value = UiState.Error("Ricerca fallita. Controlla la connessione.")
            }
        }
    }

    fun onSearchQueryChanged(query: String) {
        searchJob?.cancel()
        if (query.isBlank()) {
            searchSuggestions.value = emptyList()
            return
        }
        searchJob = viewModelScope.launch {
            delay(300)
            val history = searchHistory.value.filter { it.query.contains(query, ignoreCase = true) }.map { it.query }
            try {
                val tracksD = async { api.search(query, 5) }
                val artistsD = async { api.searchArtists(query, 5) }
                val albumsD  = async { api.searchAlbums(query, 5) }
                val tracks   = tracksD.await().data?.take(5) ?: emptyList()
                val artists  = artistsD.await().data?.take(3) ?: emptyList()
                val albums   = albumsD.await().data?.take(3) ?: emptyList()
                searchSuggestions.value = history + tracks + artists + albums
            } catch (_: Exception) {
                searchSuggestions.value = history
            }
        }
    }

    fun openArtist(artist: ArtistSearchItem) = viewModelScope.launch {
        closeAllOverlays()
        artistView.value = ArtistViewState.Loading
        val pic = artist.pictureXl ?: artist.pictureMedium
        val fans = when {
            artist.nbFan >= 1_000_000 -> "${"%.1f".format(artist.nbFan / 1_000_000f)} Mln"
            artist.nbFan >= 1_000     -> "${artist.nbFan / 1_000}K"
            else                      -> "${artist.nbFan}"
        }
        var tracks = emptyList<Track>()
        var albums = emptyList<DeezerArtistAlbum>()
        try { tracks = api.getArtistTopTracks(artist.id).data ?: emptyList() } catch (_: Exception) { }
        try { albums = api.getArtistAlbums(artist.id).data ?: emptyList() } catch (_: Exception) { }
        artistView.value = ArtistViewState.Ready(artist.id, artist.name, pic, tracks, "$fans ascoltatori mensili", false, albums)
        currentQueue = tracks
        preWarmIsrc(tracks)
    }

    fun setFilter(filter: String) {
        if (lastSearchQuery.isNotBlank()) {
            search(lastSearchQuery, filter)
        } else {
            val cur = uiState.value as? UiState.Results ?: return
            uiState.value = cur.copy(filter = filter)
        }
    }

    private fun preWarmIsrc(tracks: List<Track>) = viewModelScope.launch {
        tracks.take(5).forEach { t ->
            if (!isrcCache.containsKey(t.id)) launch {
                try { resolveIsrc(t) } catch (_: Exception) {}
            }
        }
    }

    // ── PLAY ────────────────────────────────────────────────────
    fun resolveAndPlay(track: Track, queue: List<Track>? = null) {
        if (resolving.value) return
        resolving.value = true
        resolvingIndex.value = track.id

        val q = queue ?: (uiState.value as? UiState.Results)?.tracks
        ?: (playlistView.value as? PlaylistViewState.Ready)?.tracks ?: currentQueue
        currentQueue = q
        currentIndex = q.indexOfFirst { it.id == track.id }.coerceAtLeast(0)
        currentTrack.value = track

        if (shuffleEnabled.value) {
            shuffledQueue = q.shuffled()
            shuffledIndex = shuffledQueue.indexOfFirst { it.id == track.id }.takeIf { it >= 0 } ?: 0
        }

        viewModelScope.launch {
            try {
                val stream = resolveStream(track)
                isPlaying.value = true
                addRecent(track)
                _service?.play(stream, track.title, track.artist.name,
                    track.album.bestCover)
                    ?: run { lastStreamUrl = stream }
                val nextIdx = currentIndex + 1
                if (nextIdx < currentQueue.size) {
                    launch { try { resolveStream(currentQueue[nextIdx]) } catch (_: Exception) { } }
                }
            } catch (e: Exception) {
                try {
                    val q = "${track.title} ${track.artist.name}"
                    val url = java.net.URL("https://pipedapi.com/search?q=${java.net.URLEncoder.encode(q, "UTF-8")}&filter=music")
                    val json = okhttp3.OkHttpClient().newCall(
                        okhttp3.Request.Builder().url(url).build()
                    ).execute().body?.string()
                    if (json != null) {
                        val items = com.google.gson.Gson().fromJson(json, PipedSearchResponse::class.java).items
                        val vid = items?.firstOrNull()?.url?.substringAfter("?v=")
                        if (vid != null) {
                            youTubeVideoId.value = vid
                            showYouTubePlayer.value = true
                            currentStreamSource.value = "Lossy · YouTube"
                            isPlaying.value = true
                            addRecent(track)
                            return@launch
                        }
                    }
                } catch (_: Exception) { }
                currentTrack.value = null; isPlaying.value = false
            } finally {
                resolving.value = false; resolvingIndex.value = null
            }
        }
    }

    private fun playAt(index: Int) {
        val t = currentQueue.getOrNull(index) ?: return
        currentIndex = index
        resolveAndPlay(t, currentQueue)
    }

    enum class DownloadState { IDLE, DOWNLOADING, CONVERTING, DONE, ERROR }

    val downloadState = MutableStateFlow(DownloadState.IDLE)
    val downloadError = MutableStateFlow<String?>(null)

    fun downloadCurrent(track: Track) = viewModelScope.launch {
        if (downloadState.value == DownloadState.DOWNLOADING || downloadState.value == DownloadState.CONVERTING) return@launch
        downloadState.value = DownloadState.DOWNLOADING
        downloadError.value = null
        try {
            val url = resolveStream(track)
            val ctx = getApplication<android.app.Application>()
            val cacheDir = ctx.cacheDir

            val inputFile  = java.io.File(cacheDir, "dl_${track.id}.tmp")
            val coverFile  = java.io.File(cacheDir, "dl_${track.id}.jpg")
            val outputFile = java.io.File(cacheDir, "dl_${track.id}.mp3")

            val req = okhttp3.Request.Builder().url(url).build()
            httpClient.newCall(req).execute().use { resp ->
                resp.body?.byteStream()?.use { input ->
                    inputFile.outputStream().use { output -> input.copyTo(output) }
                } ?: throw Exception("Empty response body")
            }

            val coverUrl = track.album.bestCover
            if (coverUrl != null) {
                try {
                    val coverReq = okhttp3.Request.Builder().url(coverUrl).build()
                    httpClient.newCall(coverReq).execute().use { resp ->
                        resp.body?.byteStream()?.use { input ->
                            coverFile.outputStream().use { output -> input.copyTo(output) }
                        }
                    }
                } catch (_: Exception) { }
            }

            downloadState.value = DownloadState.CONVERTING
            val result = org.musicwavver.player.AudioConverter.flacToMp3(
                input = inputFile, output = outputFile,
                title = track.title, artist = track.artist.name,
                album = track.album.title,
                genre = null,
                year = null,
                coverArt = if (coverFile.exists()) coverFile else null
            )
            if (result.isFailure) throw result.exceptionOrNull()!!

            org.musicwavver.player.MediaStoreFileManager.saveMp3(
                ctx, outputFile, track.title, track.artist.name, track.album.title
            ).getOrThrow()

            downloadState.value = DownloadState.DONE
        } catch (e: Exception) {
            downloadState.value = DownloadState.ERROR
            downloadError.value = e.message ?: "Download fallito"
        } finally {
            listOf("dl_${track.id}.tmp", "dl_${track.id}.jpg", "dl_${track.id}.mp3").forEach {
                try { java.io.File(getApplication<android.app.Application>().cacheDir, it).delete() } catch (_: Exception) { }
            }
        }
    }

    fun resetDownloadState() {
        downloadState.value = DownloadState.IDLE
        downloadError.value = null
    }

    private suspend fun resolveStream(track: Track): String {
        val isrc = resolveIsrc(track)
        val qid  = qobuzCache.getOrPut(isrc) { resolveQobuzId(isrc) }
        return streamCache.getOrPut(qid) { resolveStreamUrl(qid) }
    }

    private suspend fun resolveQobuzId(isrc: String): String {
        for (inst in RetrofitClient.monoInstances) {
            try {
                val r = inst.api.getMusic(isrc)
                if (r.success && !r.data?.tracks?.items.isNullOrEmpty())
                    return r.data!!.tracks!!.items!![0].id
            } catch (_: Exception) { }
        }
        throw Exception("Nessuna istanza disponibile per ISRC $isrc")
    }

    private suspend fun resolveStreamUrl(qid: String): String {
        for (inst in RetrofitClient.monoInstances) {
            try {
                val r = inst.api.downloadMusic(qid, inst.quality)
                if (r.success && !r.data?.url.isNullOrBlank()) {
                    currentStreamSource.value = "LOSSLESS · ${inst.name}"
                    return r.data!!.url!!
                }
            } catch (_: Exception) { }
        }
        throw Exception("Nessuna istanza disponibile per ID $qid")
    }

    private suspend fun resolveIsrc(track: Track): String =
        isrcCache.getOrPut(track.id) {
            api.getTrack(track.id).isrc ?: throw Exception("No ISRC")
        }

    private fun addRecent(track: Track) {
        val l = recentlyPlayed.value.toMutableList()
        l.removeAll { it.id == track.id }
        l.add(0, track)
        recentlyPlayed.value = l.take(30)
        viewModelScope.launch { persistence.saveRecentlyPlayed(recentlyPlayed.value) }
    }

    // ── CONTROLS ────────────────────────────────────────────────
    fun setService(svc: PlaybackService?) {
        _service = svc
        if (svc != null && lastStreamUrl != null) {
            val t = currentTrack.value ?: return
            svc.play(lastStreamUrl!!, t.title, t.artist.name,
                t.album.bestCover)
            lastStreamUrl = null
        }
    }

    // FIX: guard contro valori invariati — evita di propagare ricomposizioni
    //      inutili a tutti i composable che leggono currentPosition/duration.
    fun updateProgress(pos: Long, dur: Long) {
        if (pos != currentPosition.value) currentPosition.value = pos
        if (dur != duration.value) duration.value = dur
    }
    fun updatePlayState(v: Boolean) { isPlaying.value = v }

    fun prev() {
        when {
            currentPosition.value > 3_000L -> _service?.seekTo(0L)
            shuffleEnabled.value && shuffledQueue.isNotEmpty() -> {
                if (shuffledIndex > 0) shuffledIndex--
                val t = shuffledQueue[shuffledIndex]
                currentIndex = currentQueue.indexOf(t)
                resolveAndPlay(t, currentQueue)
            }
            currentIndex > 0 -> playAt(currentIndex - 1)
        }
    }

    fun next() {
        if (repeatMode.value == PlayMode.ONE) { _service?.seekTo(0L); return }
        if (shuffleEnabled.value && shuffledQueue.isNotEmpty()) {
            shuffledIndex = (shuffledIndex + 1).let { if (it >= shuffledQueue.size) 0 else it }
            val t = shuffledQueue[shuffledIndex]
            currentIndex = currentQueue.indexOf(t)
            resolveAndPlay(t, currentQueue)
        } else {
            val next = currentIndex + 1
            when {
                next < currentQueue.size  -> playAt(next)
                repeatMode.value == PlayMode.ALL -> playAt(0)
                recentlyPlayed.value.isNotEmpty() -> {
                    val auto = recentlyPlayed.value.random()
                    resolveAndPlay(auto, currentQueue + auto)
                }
                else -> { isPlaying.value = false; _service?.pause() }
            }
        }
    }

    fun toggleShuffle() {
        val on = !shuffleEnabled.value
        shuffleEnabled.value = on
        if (on && currentQueue.isNotEmpty()) {
            shuffledQueue = currentQueue.shuffled()
            shuffledIndex = shuffledQueue.indexOfFirst { it.id == currentTrack.value?.id }.takeIf { it >= 0 } ?: 0
        }
    }

    fun cycleRepeat() {
        repeatMode.value = when (repeatMode.value) {
            PlayMode.NONE -> PlayMode.ALL
            PlayMode.ALL  -> PlayMode.ONE
            PlayMode.ONE  -> PlayMode.NONE
        }
    }

    fun setSleepTimer(minutes: Int) {
        sleepJob?.cancel()
        if (minutes <= 0) { sleepTimerRemaining.value = 0L; return }
        val total = minutes * 60_000L
        sleepTimerRemaining.value = total
        sleepJob = viewModelScope.launch {
            val start = System.currentTimeMillis()
            while (true) {
                delay(1_000)
                val rem = total - (System.currentTimeMillis() - start)
                if (rem <= 0) { sleepTimerRemaining.value = 0L; _service?.pause(); break }
                sleepTimerRemaining.value = rem
            }
        }
    }

    fun cancelSleepTimer() { sleepJob?.cancel(); sleepTimerRemaining.value = 0L }

    fun toggleFav(track: Track) = viewModelScope.launch {
        favRepo.toggle(FavoriteTrack(track.id, track.title, track.artist.name,
            track.album.title, track.album.bestCover, track.duration))
    }

    fun removeSearchHistory(q: String) {
        searchHistory.value = searchHistory.value.filter { it.query != q }
        viewModelScope.launch { persistence.saveSearchHistory(searchHistory.value) }
    }

    fun clearSearchHistory() {
        searchHistory.value = emptyList()
        viewModelScope.launch { persistence.saveSearchHistory(emptyList()) }
    }

    fun toggleQueue()   { showQueue.value = !showQueue.value }
    fun openExpanded(){
        closeAllOverlays(); showExpanded.value = true
    }
    fun closeExpanded() { showExpanded.value = false; showQueue.value = false }

    fun closeYouTubePlayer() { showYouTubePlayer.value = false; youTubeVideoId.value = null; currentTrack.value = null; isPlaying.value = false }

    fun playFromQueue(t: Track) {
        showQueue.value = false
        currentIndex = currentQueue.indexOf(t)
        resolveAndPlay(t, currentQueue)
    }

    fun removeFromQueue(t: Track) {
        if (t.id == currentTrack.value?.id) return
        val i = currentQueue.indexOf(t)
        if (i < 0) return
        val q = currentQueue.toMutableList().also { it.removeAt(i) }
        currentQueue = q
        if (i < currentIndex) currentIndex--
    }

    fun moveQueueUp(index: Int) {
        if (index <= 0 || index >= currentQueue.size) return
        val q = currentQueue.toMutableList()
        val tmp = q[index]
        q[index] = q[index - 1]
        q[index - 1] = tmp
        currentQueue = q
        if (currentIndex == index) currentIndex--
        else if (currentIndex == index - 1) currentIndex++
    }

    fun moveQueueDown(index: Int) {
        if (index < 0 || index >= currentQueue.size - 1) return
        val q = currentQueue.toMutableList()
        val tmp = q[index]
        q[index] = q[index + 1]
        q[index + 1] = tmp
        currentQueue = q
        if (currentIndex == index) currentIndex++
        else if (currentIndex == index + 1) currentIndex--
    }

    fun setDarkMode(v: Boolean) {
        isDarkMode.value = v
        viewModelScope.launch { persistence.saveDarkMode(v) }
    }

    // ── SPOTIFY IMPORT ──────────────────────────────────────────
    val spotifyImportState = MutableStateFlow<SpotifyImportState>(SpotifyImportState.Idle)

    fun importSpotifyPlaylist(url: String) = viewModelScope.launch {
        val id = url.substringAfter("playlist/").substringBefore("?")
        if (id.isBlank()) { spotifyImportState.value = SpotifyImportState.Error("URL non valido"); return@launch }

        spotifyImportState.value = SpotifyImportState.Fetching
        try {
            val token = withContext(Dispatchers.IO) {
                RetrofitClient.getSpotifyToken(SpotifyConfig.clientId, SpotifyConfig.clientSecret)
            }
            val resp = RetrofitClient.spotifyApi.getPlaylistTracks(id, "Bearer $token")
            val items = resp.items.filter { it.track.external_ids?.isrc != null }
            val total = items.size

            val imported = items.map { item ->
                async {
                    try { api.getTrackByIsrc(item.track.external_ids!!.isrc!!) } catch (_: Exception) { null }
                }
            }.awaitAll().filterNotNull()

            currentQueue = imported
            currentIndex = -1
            preWarmIsrc(imported)
            spotifyImportState.value = SpotifyImportState.Done(imported.size, total)
        } catch (e: Exception) {
            spotifyImportState.value = SpotifyImportState.Error(e.message ?: "Import fallito")
        }
    }

    fun clearSpotifyImport() {
        spotifyImportState.value = SpotifyImportState.Idle
    }

    // ── LYRICS ──────────────────────────────────────────────────
    private suspend fun parseLrc(input: String): List<LyricLine> = withContext(Dispatchers.Default) {
        val regex = "\\[(\\d+):(\\d+\\.\\d+)\\] (.*)".toRegex()
        input.lines().mapNotNull { line ->
            val match = regex.find(line) ?: return@mapNotNull null
            val min = match.groupValues[1].toLong()
            val sec = match.groupValues[2].toDouble()
            val text = match.groupValues[3]
            LyricLine((min * 60 * 1000) + (sec * 1000).toLong(), text)
        }
    }

    private fun fetchLyrics(track: Track) {
        lyricsSyncJob?.cancel()
        lyricsLines.value = emptyList()
        currentLyricIdx.value = -1
        viewModelScope.launch {
            try {
                val res = lrcApi.getLyrics(
                    track = track.title,
                    artist = track.artist.name,
                    album = track.album.title,
                    duration = track.duration
                )
                val synced = res.syncedLyrics
                if (!synced.isNullOrBlank()) {
                    lyricsLines.value = parseLrc(synced)
                    startLyricSync()
                }
            } catch (_: Exception) { }
        }
    }

    private fun findLineIndex(lines: List<LyricLine>, posMs: Long): Int {
        var lo = 0
        var hi = lines.size - 1
        var result = -1
        while (lo <= hi) {
            val mid = (lo + hi) / 2
            if (lines[mid].timeMs <= posMs) { result = mid; lo = mid + 1 }
            else hi = mid - 1
        }
        return result
    }

    private fun startLyricSync() {
        lyricsSyncJob?.cancel()
        lyricsSyncJob = viewModelScope.launch {
            // FIX: collectLatest evita l'accumulo di aggiornamenti di posizione in coda.
            // FIX: aggiornamento di currentLyricIdx solo se il valore cambia davvero,
            //      evitando ricomposizioni inutili ogni 250ms.
            currentPosition
                .collectLatest { pos ->
                    val lines = lyricsLines.value
                    if (lines.isNotEmpty()) {
                        val newIdx = findLineIndex(lines, pos)
                        if (newIdx != currentLyricIdx.value) {
                            currentLyricIdx.value = newIdx
                        }
                    }
                }
        }
    }
}

private data class PipedSearchResponse(val items: List<PipedSearchItem>?)
private data class PipedSearchItem(val url: String?, val title: String?)
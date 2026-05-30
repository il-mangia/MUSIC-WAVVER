package org.musicwavver

import android.Manifest
import android.content.ComponentName
import android.content.Context
import android.content.Intent
import android.content.ServiceConnection
import android.content.pm.PackageManager

import android.os.Build
import android.os.Bundle
import android.os.IBinder
import androidx.activity.ComponentActivity
import androidx.activity.compose.BackHandler
import androidx.activity.compose.setContent
import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material.icons.outlined.Home
import androidx.compose.material.icons.outlined.Search
import androidx.compose.material.icons.outlined.Bookmarks
import androidx.compose.material3.*
import androidx.compose.runtime.*
import org.musicwavver.data.FavoriteTrack
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.window.Dialog
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.core.content.ContextCompat
import androidx.lifecycle.compose.collectAsStateWithLifecycle
import androidx.lifecycle.viewmodel.compose.viewModel
import org.musicwavver.model.*
import org.musicwavver.player.PlaybackService
import org.musicwavver.ui.*
import org.musicwavver.ui.theme.*

class MainActivity : ComponentActivity() {

    private val serviceState = mutableStateOf<PlaybackService?>(null)

    private val connection = object : ServiceConnection {
        override fun onServiceConnected(name: ComponentName?, service: IBinder?) {
            serviceState.value = (service as PlaybackService.LocalBinder).getService()
        }
        override fun onServiceDisconnected(name: ComponentName?) {
            serviceState.value = null
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        if (Build.VERSION.SDK_INT >= 33) {
            if (ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED)
                requestPermissions(arrayOf(Manifest.permission.POST_NOTIFICATIONS), 100)
            if (Build.VERSION.SDK_INT < Build.VERSION_CODES.Q && ContextCompat.checkSelfPermission(this,
                    Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED)
                requestPermissions(arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE), 101)
        }

        Intent(this, PlaybackService::class.java).also {
            if (Build.VERSION.SDK_INT >= 26) startForegroundService(it) else startService(it)
            bindService(it, connection, Context.BIND_AUTO_CREATE)
        }

        setContent {
            val vm: MainViewModel = viewModel()
            val isDarkMode by vm.isDarkMode.collectAsStateWithLifecycle()
            MusicWavverTheme(darkMode = isDarkMode) { MainScreen(serviceState.value) }
        }
    }

    override fun onDestroy() {
        serviceState.value?.let { it.onPlayStateChanged = null; it.onTrackEnded = null }
        unbindService(connection)
        super.onDestroy()
    }
}

private enum class NavTab { HOME, SEARCH, LIBRARY }

@Composable
fun MainScreen(service: PlaybackService?) {
    val vm: MainViewModel = viewModel()

    LaunchedEffect(service) {
        vm.setService(service)
        if (service != null) {
            service.onPlayStateChanged = { playing -> vm.updatePlayState(playing) }
            service.onTrackEnded = { vm.next() }
        }
    }

    val uiState          by vm.uiState.collectAsStateWithLifecycle()
    val homeState        by vm.homeState.collectAsStateWithLifecycle()
    val playlistView     by vm.playlistView.collectAsStateWithLifecycle()
    val albumView        by vm.albumView.collectAsStateWithLifecycle()
    val artistView       by vm.artistView.collectAsStateWithLifecycle()
    val currentTrack     by vm.currentTrack.collectAsStateWithLifecycle()
    val isPlaying        by vm.isPlaying.collectAsStateWithLifecycle()
    val favorites        by vm.favorites.collectAsStateWithLifecycle()
    val showExpanded     by vm.showExpanded.collectAsStateWithLifecycle()
    val resolving        by vm.resolving.collectAsStateWithLifecycle()
    val resolvingIndex   by vm.resolvingIndex.collectAsStateWithLifecycle()
    val shuffleEnabled   by vm.shuffleEnabled.collectAsStateWithLifecycle()
    val repeatMode       by vm.repeatMode.collectAsStateWithLifecycle()
    val sleepTimer       by vm.sleepTimerRemaining.collectAsStateWithLifecycle()
    val recentlyPlayed   by vm.recentlyPlayed.collectAsStateWithLifecycle()
    val searchHistory    by vm.searchHistory.collectAsStateWithLifecycle()
    val searchSuggestions by vm.searchSuggestions.collectAsStateWithLifecycle()
    val showQueue        by vm.showQueue.collectAsStateWithLifecycle()
    val userPlaylists    by vm.userPlaylists.collectAsStateWithLifecycle()
    val lyricsLines      by vm.lyricsLines.collectAsStateWithLifecycle()
    val currentLyricIdx  by vm.currentLyricIdx.collectAsStateWithLifecycle()
    val showSettings     by vm.showSettings.collectAsStateWithLifecycle()
    val showEqualizer    by vm.showEqualizer.collectAsStateWithLifecycle()
    val showFullscreenLyrics by vm.showFullscreenLyrics.collectAsStateWithLifecycle()

    val currentPosition by vm.currentPosition.collectAsStateWithLifecycle()
    val duration        by vm.duration.collectAsStateWithLifecycle()

    BackHandler(
        enabled = showExpanded || showFullscreenLyrics || showSettings || showEqualizer ||
                  playlistView !is PlaylistViewState.Hidden ||
                  albumView !is AlbumViewState.Hidden || artistView !is ArtistViewState.Hidden
    ) {
        when {
            showFullscreenLyrics -> vm.showFullscreenLyrics.value = false
            showExpanded -> vm.closeExpanded()
            showEqualizer -> vm.showEqualizer.value = false
            showSettings -> vm.showSettings.value = false
            playlistView !is PlaylistViewState.Hidden -> vm.closePlaylist()
            albumView !is AlbumViewState.Hidden -> vm.closeAlbum()
            artistView !is ArtistViewState.Hidden -> vm.closeArtist()
        }
    }

    var showPlaylistPicker by remember { mutableStateOf(false) }
    var newPlaylistName by remember { mutableStateOf("") }
    var searchQuery by remember { mutableStateOf("") }
    var activeTab   by remember { mutableStateOf(NavTab.HOME) }

    LaunchedEffect(isPlaying, service) {
        while (isPlaying && service != null) {
            vm.updateProgress(service.currentPosition, service.duration)
            kotlinx.coroutines.delay(250)
        }
    }

    val favIds by remember { derivedStateOf { favorites.map { it.deezerId }.toSet() } }

    val downloadState by vm.downloadState.collectAsStateWithLifecycle()
    val downloadError by vm.downloadError.collectAsStateWithLifecycle()
    val ctx = LocalContext.current

    LaunchedEffect(downloadState) {
        if (downloadState == MainViewModel.DownloadState.DONE) {
            kotlinx.coroutines.delay(2000)
            vm.resetDownloadState()
        }
        if (downloadState == MainViewModel.DownloadState.ERROR && downloadError != null) {
            android.widget.Toast.makeText(ctx, downloadError, android.widget.Toast.LENGTH_LONG).show()
        }
    }

    Box(modifier = Modifier.fillMaxSize().background(Bg)) {
        Column(modifier = Modifier.fillMaxSize()) {
            if (activeTab == NavTab.SEARCH) {
                Surface(color = Bg.copy(alpha = 0f), modifier = Modifier.fillMaxWidth()) {
                    Column(
                        modifier = Modifier
                            .statusBarsPadding()
                            .background(Brush.verticalGradient(listOf(Bg2, Bg.copy(alpha = 0f)), 0f, 200f))
                            .padding(start = 20.dp, end = 20.dp, top = 12.dp, bottom = 4.dp)
                    ) {
                        Text("Cerca", color = TextPrimary, fontWeight = FontWeight.Bold,
                            fontSize = 26.sp, letterSpacing = (-0.5).sp)
                        Spacer(Modifier.height(16.dp))
                        SearchBar(
                            query = searchQuery,
                            onQueryChange = { searchQuery = it; vm.onSearchQueryChanged(it) },
                            onSearch = { vm.search(searchQuery); activeTab = NavTab.SEARCH },
                            searchHistory = searchHistory,
                            searchSuggestions = searchSuggestions,
                            onHistorySelect = { searchQuery = it; vm.search(it); activeTab = NavTab.SEARCH },
                            onHistoryRemove = { vm.removeSearchHistory(it) },
                            onClearHistory = { vm.clearSearchHistory() },
                            onArtistClick = { vm.openArtist(it); activeTab = NavTab.HOME },
                            onAlbumClick = { searchQuery = "${it.title} ${it.artist.name}"; vm.search(searchQuery); activeTab = NavTab.SEARCH }
                        )
                    }
                }
            }

            Box(modifier = Modifier.weight(1f)) {
                when (activeTab) {
                    NavTab.HOME -> HomeScreen(
                        state = homeState,
                        currentTrackId = currentTrack?.id,
                        recentlyPlayed = recentlyPlayed,
                        onTrackClick = { vm.resolveAndPlay(it) },
                        onCategoryClick = { vm.openCategory(it) },
                        onPlaylistClick = { vm.openPlaylist(it.id, it.title, "\uD83C\uDFB5") },
                        onAlbumClick = { tracks, title, artist, cover ->
                            vm.openAlbum(tracks, title, artist, 0, cover)
                        },
                        onArtistClick = { name, cover, tracks ->
                            vm.openArtist(name, cover, tracks)
                        },
                        onRetry = { vm.loadHome() }
                    )
                    NavTab.LIBRARY -> LibraryScreen(
                        favorites = favorites,
                        recentlyPlayed = recentlyPlayed,
                        userPlaylists = userPlaylists,
                        currentTrackId = currentTrack?.id,
                        onSettingsClick = { vm.showSettings.value = true },
                        onTrackClick = { fav ->
                            val t = Track(fav.deezerId, fav.title,
                                Artist(0, fav.artist),
                                Album(fav.album, fav.art), fav.duration)
                            vm.resolveAndPlay(t)
                        },
                        onRemove = { fav ->
                            vm.toggleFav(Track(fav.deezerId, fav.title,
                                org.musicwavver.model.Artist(0, fav.artist),
                                org.musicwavver.model.Album(fav.album), fav.duration))
                        },
                        onRecentClick = { track ->
                            vm.resolveAndPlay(track)
                            activeTab = NavTab.SEARCH
                        },
                        onPlaylistTrackClick = { track ->
                            vm.resolveAndPlay(track)
                        },
                        onRemoveFromPlaylist = { plId, trackId ->
                            vm.removeFromPlaylist(plId, trackId)
                        },
                        onDeletePlaylist = { vm.deletePlaylist(it) },
                        spotifyImportState = vm.spotifyImportState.collectAsStateWithLifecycle().value,
                        onImportSpotify = { url -> vm.importSpotifyPlaylist(url) },
                        spotifyConfigured = org.musicwavver.network.SpotifyConfig.isConfigured,
                        onSetSpotifyCredentials = { id, secret ->
                            org.musicwavver.network.SpotifyConfig.clientId = id
                            org.musicwavver.network.SpotifyConfig.clientSecret = secret
                        },
                        onClearSpotifyImport = { vm.clearSpotifyImport() }
                    )
                    NavTab.SEARCH -> {
                        when (uiState) {
                            is UiState.Idle    -> IdleState()
                            is UiState.Loading -> LoadingState()
                            is UiState.Error   -> ErrorState((uiState as UiState.Error).message)
                            is UiState.Results -> {
                                val state = uiState as UiState.Results
                                TrackList(
                                    tracks = state.tracks,
                                    artists = state.artists,
                                    albums = state.albums,
                                    playlists = state.playlists,
                                    filter = state.filter,
                                    currentTrackId = currentTrack?.id,
                                    resolvingTrackId = resolvingIndex,
                                    favorites = favIds,
                                    onTrackClick = { vm.resolveAndPlay(it) },
                                    onFavClick = { vm.toggleFav(it) },
                                    onArtistClick = { vm.openArtist(it) },
                                    onAlbumClick = { alb ->
                                        vm.search("${alb.title} ${alb.artist.name}")
                                        vm.setFilter("album")
                                    },
                                    onPlaylistClick = { pl ->
                                        vm.openPlaylist(pl.id, pl.title, "\uD83D\uDCC1")
                                    }
                                )
                            }
                        }
                    }
                }
            }
        }

        if (showExpanded && !showFullscreenLyrics)
            ExpandedPlayerSection(service, vm, showExpanded, currentTrack, isPlaying, favIds, showQueue, shuffleEnabled, repeatMode, sleepTimer, sleepTimer, lyricsLines, currentLyricIdx, downloadState, ctx)

        val overlayKey = when {
            showSettings -> 4
            playlistView !is PlaylistViewState.Hidden -> 1
            albumView !is AlbumViewState.Hidden -> 2
            artistView !is ArtistViewState.Hidden -> 3
            else -> 0
        }
        AnimatedContent(targetState = overlayKey, transitionSpec = {
            (slideInVertically { it } + fadeIn()) togetherWith (slideOutVertically { -it } + fadeOut())
        }) { key ->
            when (key) {
                0 -> Box(Modifier.fillMaxSize())
                1 -> PlaylistScreen(
                    state = playlistView,
                    currentTrackId = currentTrack?.id,
                    favorites = favIds,
                    onTrackClick = { vm.resolveAndPlay(it) },
                    onFavClick = { vm.toggleFav(it) },
                    onClose = { vm.closePlaylist() }
                )
                2 -> AlbumScreen(
                    state = albumView,
                    currentTrackId = currentTrack?.id,
                    favorites = favIds,
                    onTrackClick = { vm.resolveAndPlay(it) },
                    onFavClick = { vm.toggleFav(it) },
                    onArtistClick = { name, cover, tracks -> vm.openArtist(name, cover, tracks) },
                    onClose = { vm.closeAlbum() },
                    onPlayAll = { tracks ->
                        tracks.firstOrNull()?.let { vm.resolveAndPlay(it, tracks) }
                    },
                    onShuffleAll = { tracks ->
                        tracks.ifEmpty { return@AlbumScreen }
                        val shuffled = tracks.shuffled()
                        shuffled.firstOrNull()?.let { vm.resolveAndPlay(it, shuffled) }
                    },
                    onShare = {
                        val s = albumView as? AlbumViewState.Ready ?: return@AlbumScreen
                        val url = "https://www.deezer.com/album/${s.albumId}"
                        val intent = Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, "${s.title} — ${s.artistName}\n$url")
                        }
                        ctx.startActivity(Intent.createChooser(intent, null))
                    }
                )
                3 -> ArtistScreen(
                    state = artistView,
                    currentTrackId = currentTrack?.id,
                    favorites = favIds,
                    onTrackClick = { vm.resolveAndPlay(it) },
                    onFavClick = { vm.toggleFav(it) },
                    onFollowClick = { vm.toggleFollowArtist() },
                    onClose = { vm.closeArtist() },
                    onPlayAll = { tracks ->
                        tracks.firstOrNull()?.let { vm.resolveAndPlay(it, tracks) }
                    },
                    onShuffleAll = { tracks ->
                        tracks.ifEmpty { return@ArtistScreen }
                        val shuffled = tracks.shuffled()
                        shuffled.firstOrNull()?.let { vm.resolveAndPlay(it, shuffled) }
                    },
                    onAlbumClick = { album ->
                        val artistName = (vm.artistView.value as? ArtistViewState.Ready)?.name ?: ""
                        vm.openAlbumFromArtist(album, artistName)
                    },
                    onShare = {
                        val s = artistView as? ArtistViewState.Ready ?: return@ArtistScreen
                        val url = "https://www.deezer.com/artist/${s.id}"
                        val intent = Intent(Intent.ACTION_SEND).apply {
                            type = "text/plain"
                            putExtra(Intent.EXTRA_TEXT, "${s.name}\n$url")
                        }
                        ctx.startActivity(Intent.createChooser(intent, null))
                    }
                )
                4 -> SettingsScreen(
                        isDarkMode = vm.isDarkMode.value,
                        onToggleDarkMode = { vm.setDarkMode(!vm.isDarkMode.value) },
                        onClose = { vm.showSettings.value = false }
                    )
            }
        }

        if (!showExpanded && !showFullscreenLyrics) {
            BottomBarSection(service, vm, currentTrack, isPlaying, resolving, favIds, shuffleEnabled, repeatMode, activeTab, favorites, recentlyPlayed, showPlaylistPicker, onTabSelect = { vm.closeAllOverlays(); activeTab = it }, onShowPicker = { showPlaylistPicker = true })
        }

        if (showPlaylistPicker) {
            PlaylistPickerDialog(
                playlists = userPlaylists,
                currentTrackId = currentTrack?.id,
                onAddToPlaylist = { plId -> currentTrack?.let { vm.addToPlaylist(plId, it.id) } },
                onCreatePlaylist = { name -> vm.createPlaylist(name); newPlaylistName = "" },
                newPlaylistName = newPlaylistName,
                onNewNameChange = { newPlaylistName = it },
                onDismiss = { showPlaylistPicker = false }
            )
        }

        if (showEqualizer) {
            EqualizerDialog(
                audioSessionId = service?.audioSessionId ?: 0,
                onDismiss = { vm.showEqualizer.value = false }
            )
        }

        AnimatedVisibility(
            visible = showFullscreenLyrics,
            enter = fadeIn(animationSpec = tween(200)),
            exit = fadeOut(animationSpec = tween(200))
        ) {
            FullscreenLyrics(
                track = currentTrack,
                isPlaying = isPlaying,
                currentPosition = currentPosition,
                duration = duration,
                lyricsLines = lyricsLines,
                currentLyricIdx = currentLyricIdx,
                shuffleEnabled = shuffleEnabled,
                repeatMode = repeatMode,
                isFav = currentTrack?.id?.let { favIds.contains(it) } ?: false,
                onTogglePlay = { service?.togglePlay() },
                onPrev = { vm.prev() },
                onNext = { vm.next() },
                onSeek = { p -> service?.seekTo((p * duration.coerceAtLeast(1)).toLong()) },
                onToggleShuffle = { vm.toggleShuffle() },
                onCycleRepeat = { vm.cycleRepeat() },
                onFavToggle = { currentTrack?.let { vm.toggleFav(it) } },
                onBack = { vm.showFullscreenLyrics.value = false }
            )
        }
    }
}

@Composable
private fun ExpandedPlayerSection(
    service: PlaybackService?, vm: MainViewModel, showExpanded: Boolean, currentTrack: Track?, isPlaying: Boolean,
    favIds: Set<Long>, showQueue: Boolean, shuffleEnabled: Boolean, repeatMode: PlayMode,
    sleepTimer: Long, sleepTimerRemaining: Long, lyricsLines: List<LyricLine>, currentLyricIdx: Int,
    downloadState: MainViewModel.DownloadState,
    ctx: android.content.Context
) {
    val currentPosition by vm.currentPosition.collectAsStateWithLifecycle()
    val duration by vm.duration.collectAsStateWithLifecycle()

    ExpandedPlayer(
        visible = showExpanded,
        track = currentTrack,
        isPlaying = isPlaying,
        currentPosition = currentPosition,
        duration = duration,
        shuffleEnabled = shuffleEnabled,
        repeatMode = repeatMode,
        sleepTimerRemaining = sleepTimer,
        currentQueue = vm.currentQueue,
        showQueue = showQueue,
        onTogglePlay = { service?.togglePlay() },
        onPrev = { vm.prev() },
        onNext = { vm.next() },
        onSeek = { p -> service?.seekTo((p * duration.coerceAtLeast(1)).toLong()) },
        onClose = { vm.closeExpanded() },
        onToggleShuffle = { vm.toggleShuffle() },
        onCycleRepeat = { vm.cycleRepeat() },
        onSetSleepTimer = { vm.setSleepTimer(it) },
        onCancelSleepTimer = { vm.cancelSleepTimer() },
        onToggleQueue   = { vm.toggleQueue() },
        onPlayFromQueue = { vm.playFromQueue(it) },
        onRemoveFromQueue = { vm.removeFromQueue(it) },
        isFav = currentTrack?.id?.let { favIds.contains(it) } ?: false,
        onFavToggle = { currentTrack?.let { vm.toggleFav(it) } },
        onAddToPlaylist = { },
        onArtistClick = {
            currentTrack?.let { t ->
                val tracks = vm.currentQueue.filter { it.artist.name == t.artist.name }
                vm.openArtist(t.artist.name, t.album.coverMedium ?: t.album.cover, tracks)
            }
        },
        onDownload = { currentTrack?.let { vm.downloadCurrent(it) } },
        downloadState = downloadState,
        onMoveQueueUp = { vm.moveQueueUp(it) },
        onMoveQueueDown = { vm.moveQueueDown(it) },
        onEqualizer = { vm.showEqualizer.value = true },
        onFullscreenLyrics = { vm.showFullscreenLyrics.value = true; vm.showExpanded.value = false },
        lyricsLines = lyricsLines,
        currentLyricIdx = currentLyricIdx,
        onShare = {
            currentTrack?.let { t ->
                val url = "https://www.deezer.com/track/${t.id}"
                val intent = Intent(Intent.ACTION_SEND).apply {
                    type = "text/plain"
                    putExtra(Intent.EXTRA_TEXT, "${t.title} — ${t.artist.name}\n$url")
                }
                ctx.startActivity(Intent.createChooser(intent, null))
            }
        }
    )
}

@Composable
private fun BoxScope.BottomBarSection(
    service: PlaybackService?, vm: MainViewModel, currentTrack: Track?, isPlaying: Boolean, resolving: Boolean,
    favIds: Set<Long>, shuffleEnabled: Boolean, repeatMode: PlayMode, activeTab: NavTab,
    favorites: List<FavoriteTrack>, recentlyPlayed: List<Track>,
    showPlaylistPicker: Boolean, onTabSelect: (NavTab) -> Unit, onShowPicker: () -> Unit
) {
    val isFav by remember(currentTrack, favIds) { derivedStateOf { currentTrack?.let { favIds.contains(it.id) } ?: false } }

    Column(Modifier.align(Alignment.BottomCenter)) {
        PlayerBar(
            track = currentTrack,
            isPlaying = isPlaying,
            isResolving = resolving,
            shuffleEnabled = shuffleEnabled,
            repeatMode = repeatMode,
            isFav = isFav,
            onTap   = { vm.openExpanded() },
            onTogglePlay = { service?.togglePlay() },
            onPrev  = { vm.prev() },
            onNext  = { vm.next() },
            onFavToggle = { currentTrack?.let { vm.toggleFav(it) } },
            onAddToPlaylist = onShowPicker,
            onArtistClick = {
                currentTrack?.let { t ->
                    val tracks = vm.currentQueue.filter { it.artist.name == t.artist.name }
                    vm.openArtist(t.artist.name, t.album.coverMedium ?: t.album.cover, tracks)
                }
            }
        )
        BottomNavBar(
            activeTab = activeTab,
            hasFavorites = favorites.isNotEmpty(),
            hasRecent    = recentlyPlayed.isNotEmpty(),
            onTabSelect  = onTabSelect
        )
    }
}

// ─────────────────────────────────────────────────────────────
//  BottomNavBar
// ─────────────────────────────────────────────────────────────
@Composable
private fun BottomNavBar(
    activeTab: NavTab,
    hasFavorites: Boolean,
    hasRecent: Boolean,
    onTabSelect: (NavTab) -> Unit
) {
    NavigationBar(
        containerColor = Bg.copy(alpha = 0.96f),
        tonalElevation = 0.dp,
        modifier = Modifier.navigationBarsPadding()
    ) {
        NavigationBarItem(
            selected = activeTab == NavTab.HOME,
            onClick  = { onTabSelect(NavTab.HOME) },
            icon     = {
                Icon(
                    if (activeTab == NavTab.HOME) Icons.Filled.Home else Icons.Outlined.Home,
                    contentDescription = "Home",
                    tint = if (activeTab == NavTab.HOME) Purple else TextSecondary
                )
            },
            label = { Text("Home", color = if (activeTab == NavTab.HOME) Purple else TextSecondary,
                fontSize = 11.sp, fontWeight = FontWeight.SemiBold) },
            colors = NavigationBarItemDefaults.colors(indicatorColor = PurpleDim)
        )
        NavigationBarItem(
            selected = activeTab == NavTab.SEARCH,
            onClick  = { onTabSelect(NavTab.SEARCH) },
            icon     = {
                Icon(
                    if (activeTab == NavTab.SEARCH) Icons.Filled.Search else Icons.Outlined.Search,
                    contentDescription = "Cerca",
                    tint = if (activeTab == NavTab.SEARCH) Purple else TextSecondary
                )
            },
            label = { Text("Cerca", color = if (activeTab == NavTab.SEARCH) Purple else TextSecondary,
                fontSize = 11.sp, fontWeight = FontWeight.SemiBold) },
            colors = NavigationBarItemDefaults.colors(indicatorColor = PurpleDim)
        )
        NavigationBarItem(
            selected = activeTab == NavTab.LIBRARY,
            onClick  = { onTabSelect(NavTab.LIBRARY) },
            icon     = {
                BadgedBox(badge = {
                    if ((hasFavorites || hasRecent) && activeTab != NavTab.LIBRARY)
                        Badge(containerColor = Purple)
                }) {
                    Icon(
                        if (activeTab == NavTab.LIBRARY) Icons.Filled.Bookmarks else Icons.Outlined.Bookmarks,
                        contentDescription = "Libreria",
                        tint = if (activeTab == NavTab.LIBRARY) Purple else TextSecondary
                    )
                }
            },
            label = { Text("Libreria", color = if (activeTab == NavTab.LIBRARY) Purple else TextSecondary,
                fontSize = 11.sp, fontWeight = FontWeight.SemiBold) },
            colors = NavigationBarItemDefaults.colors(indicatorColor = PurpleDim)
        )
    }
}

// ─────────────────────────────────────────────────────────────
//  Auxiliary screens
// ─────────────────────────────────────────────────────────────
@Composable
private fun IdleState() {
    Column(
        modifier = Modifier.fillMaxSize().padding(horizontal = 32.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        val bars = remember { List(6) { Animatable(if (it % 2 == 0) 0.3f else 0.7f) } }
        bars.forEachIndexed { i, anim ->
            LaunchedEffect(anim) {
                while (true) {
                    anim.animateTo(
                        if (i % 2 == 0) 0.9f else 0.3f,
                        infiniteRepeatable(tween(600 + i * 120, easing = FastOutSlowInEasing), RepeatMode.Reverse)
                    )
                }
            }
        }
        Row(verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(6.dp),
            modifier = Modifier.height(48.dp)) {
            bars.forEachIndexed { i, anim ->
                Box(Modifier.width(6.dp).fillMaxHeight(anim.value)
                    .clip(RoundedCornerShape(3.dp))
                    .background(Purple.copy(alpha = 0.4f + i * 0.1f)))
            }
        }
        Spacer(Modifier.height(24.dp))
        Text("Scopri la Musica", fontSize = 26.sp, fontWeight = FontWeight.Bold,
            color = TextPrimary, letterSpacing = (-0.5).sp)
        Spacer(Modifier.height(10.dp))
        Text("Streaming lossless via Monochrome\nQualit\u00E0 senza compromessi",
            fontSize = 14.sp, color = TextSecondary, textAlign = TextAlign.Center, lineHeight = 22.sp)
        Spacer(Modifier.height(8.dp))
        Text("Cerca un brano per iniziare", fontSize = 12.sp, color = TextTertiary, textAlign = TextAlign.Center)
    }
}

@Composable
private fun LoadingState() {
    Column(modifier = Modifier.fillMaxSize(), horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center) {
        CircularProgressIndicator(color = Purple, modifier = Modifier.size(44.dp), strokeWidth = 3.dp)
        Spacer(Modifier.height(16.dp))
        Text("Ricerca in corso\u2026", fontSize = 13.sp, color = TextTertiary, letterSpacing = 1.sp)
    }
}

@Composable
private fun ErrorState(message: String) {
    Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
        Column(
            modifier = Modifier.clip(RoundedCornerShape(20.dp)).background(Bg2).padding(24.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text("\u26A0", fontSize = 32.sp)
            Spacer(Modifier.height(12.dp))
            Text(message, color = TextSecondary, textAlign = TextAlign.Center, fontSize = 14.sp)
        }
    }
}

// ─────────────────────────────────────────────────────────────
//  PlaylistPickerDialog
// ─────────────────────────────────────────────────────────────
@Composable
private fun PlaylistPickerDialog(
    playlists: List<UserPlaylist>,
    currentTrackId: Long?,
    onAddToPlaylist: (Long) -> Unit,
    onCreatePlaylist: (String) -> Unit,
    newPlaylistName: String,
    onNewNameChange: (String) -> Unit,
    onDismiss: () -> Unit
) {
    Dialog(onDismissRequest = onDismiss) {
        Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Bg2).padding(20.dp)) {
            Text("Aggiungi a playlist", color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Spacer(Modifier.height(16.dp))

            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                OutlinedTextField(
                    value = newPlaylistName,
                    onValueChange = onNewNameChange,
                    placeholder = { Text("Nuova playlist", color = TextTertiary, fontSize = 14.sp) },
                    singleLine = true,
                    modifier = Modifier.weight(1f),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = Purple, unfocusedBorderColor = Border,
                        cursorColor = Purple, focusedTextColor = TextPrimary, unfocusedTextColor = TextPrimary,
                        focusedContainerColor = Bg3, unfocusedContainerColor = Bg3
                    ),
                    shape = RoundedCornerShape(12.dp)
                )
                FilledTonalButton(
                    onClick = { if (newPlaylistName.isNotBlank()) onCreatePlaylist(newPlaylistName.trim()) },
                    enabled = newPlaylistName.isNotBlank(),
                    colors = ButtonDefaults.filledTonalButtonColors(containerColor = Purple, contentColor = Color(0xFF0A0714))
                ) { Text("Crea") }
            }

            Spacer(Modifier.height(16.dp))
            playlists.forEach { pl ->
                Row(
                    modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp))
                        .clickable { onAddToPlaylist(pl.id); onDismiss() }
                        .padding(vertical = 12.dp, horizontal = 4.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Box(Modifier.size(40.dp).clip(RoundedCornerShape(8.dp)).background(PurpleDim), Alignment.Center) {
                        Icon(Icons.Default.QueueMusic, "Coda", Modifier.size(20.dp), Purple)
                    }
                    Column(Modifier.weight(1f)) {
                        Text(pl.name, color = TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 14.sp)
                        Text("${pl.trackIds.size} brani", color = TextTertiary, fontSize = 11.sp)
                    }
                    if (currentTrackId != null && pl.trackIds.contains(currentTrackId)) {
                        Icon(Icons.Default.Check, "Conferma", Modifier.size(18.dp), Purple)
                    }
                }
            }
            Spacer(Modifier.height(8.dp))
            TextButton(onDismiss, Modifier.align(Alignment.CenterHorizontally)) {
                Text("Annulla", color = TextSecondary, fontSize = 14.sp)
            }
        }
    }
}

// ─────────────────────────────────────────────────────────────
//  SettingsScreen
// ─────────────────────────────────────────────────────────────
@Composable
private fun SettingsScreen(
    isDarkMode: Boolean,
    onToggleDarkMode: () -> Unit,
    onClose: () -> Unit
) {
    Box(modifier = Modifier.fillMaxSize().background(Bg)) {
        Column(modifier = Modifier.fillMaxSize().padding(top = 52.dp)) {
            Row(
                Modifier.fillMaxWidth().padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onClose, Modifier.size(40.dp)) {
                    Icon(Icons.Filled.Close, "Chiudi", modifier = Modifier.size(20.dp), tint = TextSecondary)
                }
                Text("Impostazioni", color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                Spacer(Modifier.size(40.dp))
            }
            Spacer(Modifier.height(24.dp))
            HorizontalDivider(color = Border, thickness = 0.5.dp)

            Row(
                Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 16.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column {
                    Text("Tema scuro", color = TextPrimary, fontSize = 16.sp)
                    Text("Passa al tema chiaro", color = TextTertiary, fontSize = 12.sp)
                }
                Switch(
                    checked = isDarkMode,
                    onCheckedChange = { onToggleDarkMode() },
                    colors = SwitchDefaults.colors(checkedTrackColor = Purple)
                )
            }
            HorizontalDivider(color = Border, thickness = 0.5.dp)
        }
    }
}

// ─────────────────────────────────────────────────────────────
//  EqualizerDialog
// ─────────────────────────────────────────────────────────────
@Composable
private fun EqualizerDialog(audioSessionId: Int, onDismiss: () -> Unit) {
    val eqData = remember {
        if (audioSessionId > 0) {
            try {
                val eq = android.media.audiofx.Equalizer(0, audioSessionId)
                val bc = eq.numberOfBands
                val r = eq.getBandLevelRange()
                val lvls = (0 until bc.toInt()).map { i -> eq.getBandLevel(i.toShort()).toInt() }
                eq.release()
                EqData(bc.toInt(), r[0].toInt(), r[1].toInt(), lvls)
            } catch (_: Exception) { null }
        } else null
    }

    Dialog(onDismissRequest = onDismiss) {
        Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Bg2).padding(20.dp)) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                Text("Equalizzatore", color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 18.sp)
                IconButton(onClick = onDismiss, Modifier.size(32.dp)) {
                    Icon(Icons.Default.Close, "Chiudi", Modifier.size(18.dp), TextSecondary)
                }
            }
            Spacer(Modifier.height(12.dp))
            if (eqData == null || audioSessionId <= 0) {
                Text("Nessun brano in riproduzione", color = TextTertiary, fontSize = 14.sp)
            } else {
                Text("${eqData.bandCount} bande", color = TextTertiary, fontSize = 12.sp)
                Spacer(Modifier.height(8.dp))
                eqData.levels.forEachIndexed { i, level ->
                    val freq = when (i) { 0 -> "32"; 1 -> "64"; 2 -> "125"; 3 -> "250"; 4 -> "500"
                        5 -> "1K"; 6 -> "2K"; 7 -> "4K"; 8 -> "8K"; 9 -> "16K"; else -> "${i}" }
                    Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
                        Text("${freq}Hz", color = TextTertiary, fontSize = 11.sp, modifier = Modifier.width(40.dp))
                        Slider(
                            value = level.toFloat(),
                            onValueChange = { },
                            valueRange = eqData.min.toFloat()..eqData.max.toFloat(),
                            modifier = Modifier.weight(1f).height(24.dp),
                            colors = SliderDefaults.colors(thumbColor = Purple, activeTrackColor = Purple, inactiveTrackColor = Surface3)
                        )
                    }
                }
            }
        }
    }
}

private data class EqData(val bandCount: Int, val min: Int, val max: Int, val levels: List<Int>)

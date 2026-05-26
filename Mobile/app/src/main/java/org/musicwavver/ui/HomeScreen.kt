package org.musicwavver.ui

import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import org.musicwavver.R
import org.musicwavver.model.*
import org.musicwavver.ui.theme.*

data class GridItem(val title: String, val subtitle: String, val coverUrl: String?, val tracks: List<Track>, val type: String, val artistName: String)

fun deriveGridItems(recentlyPlayed: List<Track>, fallback: List<Track>): List<GridItem> {
    val source = if (recentlyPlayed.size >= 4) recentlyPlayed else fallback
    if (source.isEmpty()) return emptyList()
    val uniqueAlbums = source.distinctBy { it.album.title to it.artist.name }.take(4)
    val albums = uniqueAlbums.map { t ->
        GridItem(t.album.title, t.artist.name, t.album.bestCover,
            source.filter { r -> r.album.title == t.album.title && r.artist.name == t.artist.name }, "album", t.artist.name)
    }
    val uniqueArtists = source.distinctBy { it.artist.name }.take(4)
    val artists = uniqueArtists.map { t ->
        GridItem(t.artist.name, "Artista", null,
            source.filter { r -> r.artist.name == t.artist.name }, "artist", t.artist.name)
    }
    return (albums + artists).take(8)
}

fun deriveContinueItems(recentlyPlayed: List<Track>): List<Track> = recentlyPlayed.take(10)

@Composable
fun HomeScreen(
    state: HomeState,
    currentTrackId: Long?,
    recentlyPlayed: List<Track>,
    onTrackClick: (Track) -> Unit,
    onCategoryClick: (HomeCategory) -> Unit,
    onPlaylistClick: (DeezerPlaylist) -> Unit,
    onAlbumClick: (List<Track>, String, String, String?) -> Unit,
    onArtistClick: (String, String?, List<Track>) -> Unit,
    onRetry: () -> Unit
) {
    when (state) {
        is HomeState.Loading -> HomeLoadingSkeleton()
        is HomeState.Error   -> HomeError(onRetry)
        is HomeState.Ready   -> HomeContent(state, currentTrackId, recentlyPlayed, onTrackClick, onCategoryClick, onPlaylistClick, onAlbumClick, onArtistClick)
    }
}

@Composable
private fun HomeContent(
    state: HomeState.Ready,
    currentTrackId: Long?,
    recentlyPlayed: List<Track>,
    onTrackClick: (Track) -> Unit,
    onCategoryClick: (HomeCategory) -> Unit,
    onPlaylistClick: (DeezerPlaylist) -> Unit,
    onAlbumClick: (List<Track>, String, String, String?) -> Unit,
    onArtistClick: (String, String?, List<Track>) -> Unit
) {
    val gridItems = remember(recentlyPlayed, state.chartTracks) { deriveGridItems(recentlyPlayed, state.chartTracks) }
    val continueItems = remember(recentlyPlayed) { deriveContinueItems(recentlyPlayed) }

    LazyColumn(
        contentPadding = PaddingValues(bottom = 130.dp),
        modifier = Modifier.fillMaxSize()
    ) {
        item {
            Box(
                modifier = Modifier.fillMaxWidth()
                    .statusBarsPadding()
                    .background(Brush.verticalGradient(listOf(Bg2, Bg.copy(alpha = 0f)), 0f, 140f))
                    .padding(start = 20.dp, end = 20.dp, top = 12.dp, bottom = 4.dp)
            ) {
                Column {
                    LogoBrand()
                    Spacer(Modifier.height(12.dp))
                }
            }
        }

        if (gridItems.isNotEmpty()) {
            item {
                Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2)
                    .padding(vertical = 12.dp)) {
                    Column {
                        Text("Buona giornata", color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 21.sp,
                            modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
                        GridSection(gridItems, currentTrackId, onTrackClick, onAlbumClick, onArtistClick)
                    }
                }
                Spacer(Modifier.height(12.dp))
            }
        }

        if (continueItems.isNotEmpty()) {
            item {
                Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2)
                    .padding(vertical = 12.dp)) {
                    Column {
                        SectionHeader("Continua ad ascoltare")
                        ContinueRow(continueItems, currentTrackId, onTrackClick)
                    }
                }
                Spacer(Modifier.height(12.dp))
            }
        }

        if (state.playlists.isNotEmpty()) {
            item {
                Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2)
                    .padding(vertical = 12.dp)) {
                    Column {
                        SectionHeader("Le tue playlist")
                        PlaylistsRow(state.playlists, onPlaylistClick)
                    }
                }
                Spacer(Modifier.height(12.dp))
            }
        }

        state.categories.forEach { cat ->
            if (cat.tracks.isNotEmpty()) {
                item {
                    Box(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2)
                        .padding(vertical = 10.dp)) {
                        Column {
                            Row(
                                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Text("${cat.emoji} ${cat.name}", color = TextPrimary,
                                    fontWeight = FontWeight.Bold, fontSize = 17.sp)
                                Text("Vedi tutti \u2192", color = Purple, fontSize = 12.sp,
                                    fontWeight = FontWeight.SemiBold,
                                    modifier = Modifier.clickable { onCategoryClick(cat) })
                            }
                            HorizontalTrackRow(cat.tracks, currentTrackId, onTrackClick)
                        }
                    }
                    Spacer(Modifier.height(8.dp))
                }
            }
        }
    }
}

@Composable
private fun GridSection(
    items: List<GridItem>,
    currentTrackId: Long?,
    onTrackClick: (Track) -> Unit,
    onAlbumClick: (List<Track>, String, String, String?) -> Unit,
    onArtistClick: (String, String?, List<Track>) -> Unit
) {
    val chunked = items.chunked(2)
    Column(Modifier.padding(horizontal = 16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
        chunked.forEach { row ->
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                row.forEach { item ->
                    Box(
                        modifier = Modifier.weight(1f).clip(RoundedCornerShape(6.dp))
                            .background(Bg2).clickable {
                                when (item.type) {
                                    "artist" -> onArtistClick(item.title, item.coverUrl, item.tracks)
                                    else -> onAlbumClick(item.tracks, item.title, item.artistName, item.coverUrl)
                                }
                            }.padding(end = 8.dp)
                    ) {
                        Row(verticalAlignment = Alignment.CenterVertically) {
                            if (!item.coverUrl.isNullOrBlank() && item.type == "album") {
                                AsyncImage(model = item.coverUrl, contentDescription = null,
                                    contentScale = ContentScale.Crop,
                                    modifier = Modifier.size(54.dp).clip(RoundedCornerShape(6.dp)))
                            } else {
                                Box(Modifier.size(54.dp).clip(RoundedCornerShape(6.dp))
                                    .background(Brush.linearGradient(listOf(PurpleMid.copy(0.3f), Bg3))),
                                    Alignment.Center) {
                                    Text(item.title.take(1).uppercase().ifEmpty { "\u266A" },
                                        color = Purple.copy(0.7f), fontSize = 20.sp, fontWeight = FontWeight.Bold)
                                }
                            }
                            Spacer(Modifier.width(10.dp))
                            Column(Modifier.weight(1f)) {
                                Text(item.title.ifEmpty { "Album" }, color = TextPrimary,
                                    fontWeight = FontWeight.SemiBold, fontSize = 13.sp,
                                    maxLines = 2, overflow = TextOverflow.Ellipsis)
                                if (item.subtitle.isNotEmpty() && item.subtitle != item.title) {
                                    Text(item.subtitle, color = TextSecondary, fontSize = 11.sp,
                                        maxLines = 1, overflow = TextOverflow.Ellipsis)
                                }
                            }
                        }
                    }
                }
                if (row.size < 2) {
                    Spacer(Modifier.weight(1f))
                }
            }
        }
    }
}

@Composable
private fun ContinueRow(tracks: List<Track>, currentTrackId: Long?, onTrackClick: (Track) -> Unit) {
    LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(tracks, key = { it.id }) { track ->
            ContinueCard(track, isPlaying = track.id == currentTrackId, onClick = { onTrackClick(track) })
        }
    }
}

@Composable
private fun ContinueCard(track: Track, isPlaying: Boolean, onClick: () -> Unit) {
    val art = track.album.bestCover
    Column(
        modifier = Modifier.width(140.dp).clickable(onClick = onClick),
        horizontalAlignment = Alignment.Start
    ) {
        Box(modifier = Modifier.size(140.dp).clip(RoundedCornerShape(8.dp))) {
            if (!art.isNullOrBlank()) {
                AsyncImage(model = art, contentDescription = null,
                    contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            } else {
                Box(Modifier.fillMaxSize().background(Bg3), Alignment.Center) {
                    Text("\u266A", color = TextTertiary, fontSize = 28.sp)
                }
            }
            if (isPlaying) {
                Box(Modifier.fillMaxSize().background(Purple.copy(alpha = 0.25f)), Alignment.Center) {
                    Text("\u25B6", color = TextPrimary, fontSize = 28.sp)
                }
            }
        }
        Spacer(Modifier.height(6.dp))
        Text(track.title, color = TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 12.sp,
            maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(track.artist.name, color = TextSecondary, fontSize = 11.sp,
            maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

@Composable
private fun PlaylistsRow(playlists: List<DeezerPlaylist>, onPlaylistClick: (DeezerPlaylist) -> Unit) {
    LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        items(playlists.take(5), key = { it.id }) { pl ->
            PlaylistCard(pl, onClick = { onPlaylistClick(pl) })
        }
    }
}

@Composable
private fun PlaylistCard(pl: DeezerPlaylist, onClick: () -> Unit) {
    val pic = pl.pictureMedium
    Column(
        modifier = Modifier.width(150.dp).clickable(onClick = onClick),
        horizontalAlignment = Alignment.Start
    ) {
        Box(modifier = Modifier.size(150.dp).clip(RoundedCornerShape(8.dp))) {
            if (!pic.isNullOrBlank()) {
                AsyncImage(model = pic, contentDescription = null,
                    contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            } else {
                Box(Modifier.fillMaxSize().background(Surface2), Alignment.Center) {
                    Text("\uD83C\uDFB5", fontSize = 32.sp)
                }
            }
        }
        Spacer(Modifier.height(6.dp))
        Text(pl.title, color = TextPrimary, fontWeight = FontWeight.SemiBold,
            fontSize = 13.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
        if (pl.nbTracks > 0)
            Text("${pl.nbTracks} brani", color = TextTertiary, fontSize = 11.sp)
    }
}

@Composable
private fun HorizontalTrackRow(tracks: List<Track>, currentTrackId: Long?, onTrackClick: (Track) -> Unit) {
    LazyRow(
        contentPadding = PaddingValues(horizontal = 16.dp),
        horizontalArrangement = Arrangement.spacedBy(10.dp)
    ) {
        items(tracks, key = { it.id }) { track ->
            HomeTrackCard(track, isPlaying = track.id == currentTrackId, onClick = { onTrackClick(track) })
        }
    }
}

@Composable
private fun HomeTrackCard(track: Track, isPlaying: Boolean, onClick: () -> Unit) {
    val art = track.album.bestCover
    Column(
        modifier = Modifier.width(130.dp).clickable(onClick = onClick),
        horizontalAlignment = Alignment.Start
    ) {
        Box(modifier = Modifier.size(130.dp).clip(RoundedCornerShape(8.dp))) {
            if (!art.isNullOrBlank()) {
                AsyncImage(model = art, contentDescription = null,
                    contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            } else {
                Box(Modifier.fillMaxSize().background(Bg3), Alignment.Center) {
                    Text("\u266A", color = TextTertiary, fontSize = 28.sp)
                }
            }
            if (isPlaying) {
                Box(Modifier.fillMaxSize().background(Purple.copy(alpha = 0.25f)),
                    Alignment.Center) {
                    Text("\u25B6", color = TextPrimary, fontSize = 28.sp)
                }
            }
        }
        Spacer(Modifier.height(6.dp))
        Text(track.title, color = TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 12.sp,
            maxLines = 1, overflow = TextOverflow.Ellipsis)
        Text(track.artist.name, color = TextSecondary, fontSize = 11.sp,
            maxLines = 1, overflow = TextOverflow.Ellipsis)
    }
}

@Composable
private fun SectionHeader(title: String) {
    Text(title, color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 17.sp,
        modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp))
}

@Composable
fun LogoBrand() {
    Row(verticalAlignment = Alignment.CenterVertically) {
        AsyncImage(model = R.drawable.ic_logo, contentDescription = "Music Wavver",
            modifier = Modifier.size(28.dp))
        Spacer(Modifier.width(8.dp))
        Text("Music Wavver", fontSize = 18.sp, fontWeight = FontWeight.Bold,
            color = TextPrimary, letterSpacing = (-0.5).sp)
    }
}

@Composable
private fun HomeLoadingSkeleton() {
    val alpha by rememberInfiniteTransition("sk").animateFloat(
        0.3f, 0.7f, infiniteRepeatable(tween(900), RepeatMode.Reverse), "a"
    )
    LazyColumn(contentPadding = PaddingValues(bottom = 130.dp)) {
        item {
            Spacer(Modifier.height(52.dp))
            Box(Modifier.padding(horizontal = 16.dp).fillMaxWidth().height(20.dp)
                .clip(RoundedCornerShape(10.dp)).background(Surface2.copy(alpha = alpha)))
            Spacer(Modifier.height(16.dp))
            repeat(4) {
                Row(Modifier.padding(horizontal = 16.dp).fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.weight(1f).height(54.dp).clip(RoundedCornerShape(6.dp)).background(Surface2.copy(alpha = alpha)))
                    Box(Modifier.weight(1f).height(54.dp).clip(RoundedCornerShape(6.dp)).background(Surface2.copy(alpha = alpha)))
                }
                Spacer(Modifier.height(8.dp))
            }
            Spacer(Modifier.height(16.dp))
            Box(Modifier.padding(horizontal = 16.dp).width(140.dp).height(16.dp)
                .clip(RoundedCornerShape(8.dp)).background(Surface2.copy(alpha = alpha)))
            Spacer(Modifier.height(10.dp))
            Row(modifier = Modifier.padding(horizontal = 16.dp),
                horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                repeat(4) {
                    Box(Modifier.size(130.dp).clip(RoundedCornerShape(8.dp))
                        .background(Surface2.copy(alpha = alpha)))
                }
            }
            Spacer(Modifier.height(24.dp))
        }
    }
}

@Composable
private fun HomeError(onRetry: () -> Unit) {
    Box(Modifier.fillMaxSize(), Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text("\u26A0", fontSize = 36.sp)
            Spacer(Modifier.height(12.dp))
            Text("Impossibile caricare la home", color = TextSecondary, fontSize = 15.sp)
            Spacer(Modifier.height(16.dp))
            FilledTonalButton(onClick = onRetry) {
                Icon(Icons.Default.Refresh, "Riprova", modifier = Modifier.size(16.dp))
                Spacer(Modifier.width(6.dp))
                Text("Riprova")
            }
        }
    }
}

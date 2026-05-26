package org.musicwavver.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardActions
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.focus.onFocusChanged
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalFocusManager
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.ImeAction
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.DpOffset
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import org.musicwavver.model.*
import org.musicwavver.ui.theme.*

@Composable
fun SearchBar(
    query: String,
    onQueryChange: (String) -> Unit,
    onSearch: () -> Unit,
    searchHistory: List<String> = emptyList(),
    searchSuggestions: List<Any> = emptyList(),
    onHistorySelect: (String) -> Unit = {},
    onHistoryRemove: (String) -> Unit = {},
    onClearHistory: () -> Unit = {}
) {
    val fm = LocalFocusManager.current
    var focused by remember { mutableStateOf(false) }
    val showHistory = focused && query.isBlank() && searchHistory.isNotEmpty()
    val showSuggestions = focused && query.isNotBlank() && (searchSuggestions.isNotEmpty() || searchHistory.any { it.contains(query, ignoreCase = true) })
    val filteredHistory = if (query.isNotBlank()) searchHistory.filter { it.contains(query, ignoreCase = true) } else emptyList()

    Column {
        OutlinedTextField(
            value = query,
            onValueChange = { onQueryChange(it); if (it.isNotBlank()) focused = true },
            placeholder = { Text("Artista, brano, album\u2026", color = TextTertiary, fontSize = 15.sp) },
            leadingIcon = {
                Icon(Icons.Default.Search, "Cerca", tint = if (focused) Purple else TextTertiary,
                    modifier = Modifier.size(20.dp))
            },
            trailingIcon = {
                if (query.isNotBlank())
                    IconButton(onClick = { onQueryChange("") }, modifier = Modifier.size(32.dp)) {
                        Icon(Icons.Default.Close, "Cancella ricerca", tint = TextTertiary, modifier = Modifier.size(16.dp))
                    }
            },
            singleLine = true,
            keyboardOptions = KeyboardOptions(imeAction = ImeAction.Search),
            keyboardActions = KeyboardActions(onSearch = { fm.clearFocus(); onSearch() }),
            colors = OutlinedTextFieldDefaults.colors(
                focusedBorderColor   = Purple.copy(alpha = 0.7f),
                unfocusedBorderColor = Border,
                cursorColor          = Purple,
                focusedTextColor     = TextPrimary,
                unfocusedTextColor   = TextPrimary,
                focusedContainerColor   = Bg3,
                unfocusedContainerColor = Bg3
            ),
            shape = RoundedCornerShape(16.dp),
            modifier = Modifier.fillMaxWidth().onFocusChanged { focused = it.isFocused }
        )

        AnimatedVisibility(showHistory) {
            Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2).padding(vertical = 8.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 4.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text("Ricerche recenti", color = TextTertiary, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    TextButton(onClick = onClearHistory, contentPadding = PaddingValues(0.dp)) {
                        Text("Cancella", color = Purple, fontSize = 12.sp)
                    }
                }
                searchHistory.take(6).forEach { q ->
                    Row(
                        modifier = Modifier.fillMaxWidth().clickable { onHistorySelect(q); fm.clearFocus() }
                            .padding(horizontal = 16.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Icon(Icons.Default.History, "Cronologia", tint = TextTertiary, modifier = Modifier.size(16.dp))
                        Text(q, color = TextSecondary, fontSize = 14.sp, modifier = Modifier.weight(1f),
                            maxLines = 1, overflow = TextOverflow.Ellipsis)
                        IconButton(onClick = { onHistoryRemove(q) }, modifier = Modifier.size(24.dp)) {
                            Icon(Icons.Default.Close, "Rimuovi", tint = TextTertiary, modifier = Modifier.size(14.dp))
                        }
                    }
                }
            }
        }

        AnimatedVisibility(showSuggestions) {
            Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2).padding(vertical = 8.dp)) {
                if (filteredHistory.isNotEmpty()) {
                    Text("Suggerimenti", color = TextTertiary, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp))
                    filteredHistory.take(3).forEach { q ->
                        Row(
                            modifier = Modifier.fillMaxWidth().clickable { onHistorySelect(q); fm.clearFocus() }
                                .padding(horizontal = 16.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Icon(Icons.Default.History, "Cronologia", tint = TextTertiary, modifier = Modifier.size(16.dp))
                            Text(q, color = TextSecondary, fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                    }
                }
                val tracks = searchSuggestions.filterIsInstance<Track>()
                if (tracks.isNotEmpty()) {
                    Text("Brani", color = TextTertiary, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.padding(horizontal = 16.dp, vertical = 4.dp))
                    tracks.forEach { t ->
                        Row(
                            modifier = Modifier.fillMaxWidth().clickable { onHistorySelect(t.title); fm.clearFocus() }
                                .padding(horizontal = 16.dp, vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Box(Modifier.size(32.dp).clip(RoundedCornerShape(6.dp)).background(PurpleDim), Alignment.Center) {
                                Text("\u266A", color = Purple, fontSize = 14.sp)
                            }
                            Column(Modifier.weight(1f)) {
                                Text(t.title, color = TextPrimary, fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                Text(t.artist.name, color = TextSecondary, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun FilterBar(filter: String, onFilter: (String) -> Unit) {
    LazyRow(Modifier.fillMaxWidth().padding(vertical = 10.dp),
        horizontalArrangement = Arrangement.spacedBy(8.dp)) {
        items(listOf("all" to "Tutti", "track" to "Brani", "album" to "Album", "artist" to "Artisti", "lyrics" to "Testo")) { (f, label) ->
            val active = filter == f
            FilterChip(
                selected = active, onClick = { onFilter(f) },
                label = { Text(label, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
                    color = if (active) Color(0xFF0A0714) else TextSecondary) },
                colors = FilterChipDefaults.filterChipColors(
                    selectedContainerColor = Purple, containerColor = PurpleDim.copy(alpha = 0.08f)),
                border = FilterChipDefaults.filterChipBorder(
                    enabled = true, borderColor = Border, selectedBorderColor = Purple.copy(alpha = 0.5f),
                    selected = active),
                shape = RoundedCornerShape(24.dp)
            )
        }
    }
}

@Composable
fun TrackList(
    tracks: List<Track>,
    artists: List<ArtistSearchItem>,
    albums: List<AlbumSearchItem> = emptyList(),
    filter: String,
    currentTrackId: Long?,
    resolvingTrackId: Long?,
    favorites: Set<Long>,
    onTrackClick: (Track) -> Unit,
    onFavClick: (Track) -> Unit,
    onArtistClick: (ArtistSearchItem) -> Unit,
    onAlbumClick: (AlbumSearchItem) -> Unit = {}
) {
    if (filter == "artist") {
        if (artists.isEmpty()) {
            Box(Modifier.fillMaxSize(), Alignment.Center) {
                Text("Nessun artista trovato", color = TextTertiary, fontSize = 14.sp)
            }
            return
        }
        LazyColumn(modifier = Modifier.padding(horizontal = 12.dp).padding(bottom = 120.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)) {
            items(artists, key = { it.id }) { a ->
                ArtistCard(a, onClick = { onArtistClick(a) })
            }
        }
        return
    }

    if (filter == "album") {
        if (albums.isEmpty()) {
            Box(Modifier.fillMaxSize(), Alignment.Center) {
                Text("Nessun album trovato", color = TextTertiary, fontSize = 14.sp)
            }
            return
        }
        LazyColumn(modifier = Modifier.padding(horizontal = 12.dp).padding(bottom = 120.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)) {
            items(albums, key = { it.id }) { a ->
                AlbumCard(a, onClick = { onAlbumClick(a) })
            }
        }
        return
    }

    if (filter == "lyrics") {
        if (tracks.isEmpty()) {
            Box(Modifier.fillMaxSize(), Alignment.Center) {
                Text("Nessun risultato per questo testo", color = TextTertiary, fontSize = 14.sp)
            }
            return
        }
        LazyColumn(modifier = Modifier.padding(horizontal = 12.dp).padding(bottom = 120.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)) {
            items(tracks, key = { it.id }) { track ->
                TrackCard(
                    track = track,
                    isFav = favorites.contains(track.id),
                    isNowPlaying = track.id == currentTrackId,
                    isResolving  = track.id == resolvingTrackId,
                    onClick  = { onTrackClick(track) },
                    onFavClick = { onFavClick(track) }
                )
            }
        }
        return
    }

    val filtered = if (filter == "all") tracks else tracks.filter { it.type == filter }
    if (filtered.isEmpty()) {
        Box(Modifier.fillMaxSize(), Alignment.Center) {
            Text("Nessun risultato", color = TextTertiary, fontSize = 14.sp)
        }
        return
    }

    LazyColumn(modifier = Modifier.padding(horizontal = 12.dp).padding(bottom = 120.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)) {
        items(filtered, key = { it.id }) { track ->
            TrackCard(
                track = track,
                isFav = favorites.contains(track.id),
                isNowPlaying = track.id == currentTrackId,
                isResolving  = track.id == resolvingTrackId,
                onClick  = { onTrackClick(track) },
                onFavClick = { onFavClick(track) }
            )
        }
    }
}

@Composable
fun AlbumCard(album: AlbumSearchItem, onClick: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp))
            .background(Bg2).clickable(onClick = onClick).padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        val pic = album.bestCover
        Box(modifier = Modifier.size(54.dp).clip(RoundedCornerShape(12.dp))) {
            if (!pic.isNullOrBlank()) {
                AsyncImage(model = pic, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            } else {
                Box(Modifier.fillMaxSize().background(PurpleDim), Alignment.Center) {
                    Text("\u266A", color = Purple, fontWeight = FontWeight.Bold, fontSize = 20.sp)
                }
            }
        }
        Column(Modifier.weight(1f)) {
            Text(album.title, color = TextPrimary, fontWeight = FontWeight.SemiBold,
                fontSize = 15.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text("${album.artist.name}  \u00B7  ${album.nbTracks} brani", color = TextSecondary, fontSize = 12.sp,
                maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        Icon(Icons.Default.ChevronRight, null, Modifier.size(20.dp), TextTertiary)
    }
}

@Composable
fun ArtistCard(artist: ArtistSearchItem, onClick: () -> Unit) {
    val pic = artist.pictureMedium
    Row(
        modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp))
            .background(Bg2).clickable(onClick = onClick).padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(14.dp)
    ) {
        Box(modifier = Modifier.size(54.dp).clip(CircleShape)) {
            if (!pic.isNullOrBlank()) {
                AsyncImage(model = pic, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            } else {
                Box(Modifier.fillMaxSize().background(PurpleDim), Alignment.Center) {
                    Text(artist.name.take(1).uppercase(), color = Purple,
                        fontWeight = FontWeight.Bold, fontSize = 20.sp)
                }
            }
        }
        Column(Modifier.weight(1f)) {
            Text(artist.name, color = TextPrimary, fontWeight = FontWeight.SemiBold,
                fontSize = 15.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            if (artist.nbFan > 0) {
                val fans = when {
                    artist.nbFan >= 1_000_000 -> "${"%.1f".format(artist.nbFan / 1_000_000f)}M fan"
                    artist.nbFan >= 1_000     -> "${artist.nbFan / 1_000}K fan"
                    else                      -> "${artist.nbFan} fan"
                }
                Text(fans, color = TextTertiary, fontSize = 12.sp)
            }
        }
        Icon(Icons.Default.ChevronRight, null, tint = TextTertiary, modifier = Modifier.size(20.dp))
    }
}

@Composable
fun TrackCard(
    track: Track,
    isFav: Boolean,
    isNowPlaying: Boolean,
    isResolving: Boolean,
    onClick: () -> Unit,
    onFavClick: () -> Unit
) {
    val art = track.album.bestCover
    val haptic = LocalHapticFeedback.current
    var showMenu by remember { mutableStateOf(false) }

    Box {
        Row(
            modifier = Modifier.fillMaxWidth()
                .clip(RoundedCornerShape(16.dp))
                .background(if (isNowPlaying)
                    Brush.linearGradient(listOf(PurpleDim, Bg2), Offset.Zero, Offset(400f, 0f))
                else Brush.linearGradient(listOf(Bg2, Bg2)))
                .pointerInput(Unit) {
                    detectTapGestures(
                        onTap = { onClick() },
                        onLongPress = { haptic.performHapticFeedback(HapticFeedbackType.LongPress); showMenu = true }
                    )
                }
                .padding(12.dp),
            verticalAlignment = Alignment.CenterVertically,
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            Box(Modifier.size(54.dp).clip(RoundedCornerShape(12.dp))) {
                if (!art.isNullOrBlank())
                    AsyncImage(model = art, contentDescription = null, contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize())
                else
                    Box(Modifier.fillMaxSize().background(Bg3), Alignment.Center) {
                        Text("\u266A", color = TextTertiary, fontSize = 22.sp)
                    }
                if (isResolving) {
                    Box(Modifier.fillMaxSize().background(Bg.copy(alpha = 0.6f)), Alignment.Center) {
                        CircularProgressIndicator(color = Purple, modifier = Modifier.size(20.dp), strokeWidth = 2.dp)
                    }
                }
            }

            Column(Modifier.weight(1f)) {
                Text(track.title, color = if (isNowPlaying) Purple else TextPrimary,
                    fontWeight = FontWeight.SemiBold, fontSize = 15.sp,
                    maxLines = 1, overflow = TextOverflow.Ellipsis)
                Spacer(Modifier.height(2.dp))
                Text(track.artist.name, color = TextSecondary, fontSize = 12.sp,
                    maxLines = 1, overflow = TextOverflow.Ellipsis)
                Text(track.album.title, color = TextTertiary, fontSize = 11.sp,
                    maxLines = 1, overflow = TextOverflow.Ellipsis)
            }

            if (isNowPlaying) PlayingBars()
            else if (!isResolving) Text(formatDuration(track.duration), color = TextTertiary, fontSize = 11.sp)

            Box(Modifier.size(36.dp).clip(RoundedCornerShape(10.dp)).clickable(onClick = onFavClick),
                Alignment.Center) {
                Text(if (isFav) "\u2665" else "\u2661", color = if (isFav) Coral else TextTertiary, fontSize = 20.sp)
            }
        }

        DropdownMenu(expanded = showMenu, onDismissRequest = { showMenu = false },
            offset = DpOffset(60.dp, (-8).dp), containerColor = Bg2) {
            DropdownMenuItem(
                text = { Text(if (isFav) "Rimuovi dai preferiti" else "Aggiungi ai preferiti",
                    color = TextPrimary, fontSize = 14.sp) },
                leadingIcon = { Text(if (isFav) "\u2665" else "\u2661", color = Coral, fontSize = 16.sp) },
                onClick = { onFavClick(); showMenu = false }
            )
        }
    }
}

@Composable
private fun PlayingBars() {
    val bars = remember { List(4) { Animatable(0.3f) } }
    bars.forEachIndexed { i, anim ->
        LaunchedEffect(anim) {
            while (true) {
                anim.animateTo(
                    (0.3f + Math.random().toFloat() * 0.7f).coerceIn(0.3f, 1f),
                    tween(200 + i * 80, easing = FastOutSlowInEasing)
                )
            }
        }
    }
    Row(Modifier.height(16.dp), verticalAlignment = Alignment.Bottom, horizontalArrangement = Arrangement.spacedBy(2.dp)) {
        bars.forEach { anim ->
            Box(Modifier.width(3.dp).fillMaxHeight(anim.value).clip(RoundedCornerShape(2.dp)).background(Purple))
        }
    }
}

fun formatDuration(s: Int): String {
    if (s <= 0) return "0:00"
    return "${s / 60}:${(s % 60).toString().padStart(2, '0')}"
}

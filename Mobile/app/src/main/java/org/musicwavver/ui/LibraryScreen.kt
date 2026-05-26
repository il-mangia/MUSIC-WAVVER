package org.musicwavver.ui

import androidx.compose.animation.core.tween
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import org.musicwavver.data.FavoriteTrack
import org.musicwavver.model.Track
import org.musicwavver.model.UserPlaylist
import org.musicwavver.ui.theme.*

enum class LibrarySort(val label: String) { ADDED("Aggiunti"), AZ("A\u2192Z"), DURATION("Durata"), ARTIST("Artista") }

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LibraryScreen(
    favorites: List<FavoriteTrack>,
    recentlyPlayed: List<Track>,
    userPlaylists: List<UserPlaylist>,
    currentTrackId: Long?,
    onTrackClick: (FavoriteTrack) -> Unit,
    onRemove: (FavoriteTrack) -> Unit,
    onRecentClick: (Track) -> Unit,
    onPlaylistTrackClick: (Track) -> Unit,
    onRemoveFromPlaylist: (Long, Long) -> Unit,
    onDeletePlaylist: (Long) -> Unit,
    onSettingsClick: () -> Unit = {},
    spotifyImportState: SpotifyImportState = SpotifyImportState.Idle,
    onImportSpotify: (String) -> Unit = {},
    spotifyConfigured: Boolean = false,
    onSetSpotifyCredentials: (String, String) -> Unit = { _, _ -> },
    onClearSpotifyImport: () -> Unit = {}
) {
    var sort by remember { mutableStateOf(LibrarySort.ADDED) }
    var tab  by remember { mutableIntStateOf(0) }
    var showSpotifyDialog by remember { mutableStateOf(false) }
    var spotifyUrl by remember { mutableStateOf("") }
    var clientIdInput by remember { mutableStateOf("") }
    var clientSecretInput by remember { mutableStateOf("") }

    val sorted = remember(favorites, sort) {
        when (sort) {
            LibrarySort.ADDED    -> favorites
            LibrarySort.AZ       -> favorites.sortedBy { it.title.lowercase() }
            LibrarySort.DURATION -> favorites.sortedByDescending { it.duration }
            LibrarySort.ARTIST   -> favorites.sortedBy { it.artist.lowercase() }
        }
    }

    Column(Modifier.fillMaxSize()) {
        Box(Modifier.fillMaxWidth()
            .statusBarsPadding()
            .background(Brush.verticalGradient(listOf(Bg2, Bg.copy(alpha = 0f)), 0f, 160f))
            .padding(start = 20.dp, end = 20.dp, top = 12.dp)) {
            Column {
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text("Libreria", color = TextPrimary, fontWeight = FontWeight.Bold,
                        fontSize = 26.sp, letterSpacing = (-0.5).sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(0.dp)) {
                        IconButton(onClick = { showSpotifyDialog = true }, modifier = Modifier.size(36.dp)) {
                            Icon(Icons.Default.MusicNote, "Importa da Spotify", tint = TextSecondary, modifier = Modifier.size(20.dp))
                        }
                        IconButton(onClick = onSettingsClick, modifier = Modifier.size(36.dp)) {
                            Icon(Icons.Default.Menu, "Menu", tint = TextSecondary, modifier = Modifier.size(20.dp))
                        }
                    }
                }
                Spacer(Modifier.height(16.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    LibTab("Preferiti", Icons.Default.Favorite, tab == 0) { tab = 0 }
                    LibTab("Recenti", Icons.Default.History, tab == 1) { tab = 1 }
                    LibTab("Playlist", Icons.Default.QueueMusic, tab == 2) { tab = 2 }
                }
                Spacer(Modifier.height(4.dp))
            }
        }
        HorizontalDivider(color = Border, thickness = 0.5.dp, modifier = Modifier.padding(horizontal = 16.dp))

        when (tab) {
            0 -> FavTab(sorted, sort, { sort = it }, onTrackClick, onRemove)
            1 -> RecentTab(recentlyPlayed, onRecentClick)
            2 -> PlaylistTab(userPlaylists, currentTrackId, onPlaylistTrackClick, onRemoveFromPlaylist, onDeletePlaylist)
        }
    }

    if (showSpotifyDialog) {
        AlertDialog(onDismissRequest = { showSpotifyDialog = false }) {
            Box(Modifier.background(Bg2, RoundedCornerShape(24.dp)).padding(24.dp)) {
                when (val state = spotifyImportState) {
                    is SpotifyImportState.Fetching -> {
                        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                            CircularProgressIndicator(color = Purple, modifier = Modifier.size(40.dp))
                            Spacer(Modifier.height(16.dp))
                            Text("Importazione in corso...", color = TextSecondary, fontSize = 14.sp)
                        }
                    }
                    is SpotifyImportState.Done -> {
                        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                            Text("\u2705", fontSize = 40.sp)
                            Spacer(Modifier.height(12.dp))
                            Text("Importati ${state.imported}/${state.total} brani", color = TextPrimary, fontSize = 16.sp, fontWeight = FontWeight.Bold)
                            Spacer(Modifier.height(6.dp))
                            Text("Trovati nella tua libreria. Vai su Playlist per riprodurli.", color = TextTertiary, fontSize = 13.sp)
                            Spacer(Modifier.height(18.dp))
                            Button({ showSpotifyDialog = false; onClearSpotifyImport() }, colors = ButtonDefaults.buttonColors(Purple)) {
                                Text("OK", color = Color(0xFF0A0714))
                            }
                        }
                    }
                    is SpotifyImportState.Error -> {
                        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.fillMaxWidth()) {
                            Text("\u274C", fontSize = 40.sp)
                            Spacer(Modifier.height(12.dp))
                            Text(state.msg, color = Coral, fontSize = 14.sp)
                            Spacer(Modifier.height(18.dp))
                            Button({ showSpotifyDialog = false }, colors = ButtonDefaults.buttonColors(Purple)) {
                                Text("Chiudi", color = Color(0xFF0A0714))
                            }
                        }
                    }
                    is SpotifyImportState.Idle -> {
                        Column(modifier = Modifier.fillMaxWidth()) {
                            Text("Importa playlist Spotify", color = TextPrimary, fontSize = 18.sp, fontWeight = FontWeight.Bold)
                            Spacer(Modifier.height(16.dp))
                            OutlinedTextField(spotifyUrl, { spotifyUrl = it },
                                label = { Text("URL playlist") },
                                placeholder = { Text("https://open.spotify.com/playlist/...", fontSize = 13.sp) },
                                modifier = Modifier.fillMaxWidth(),
                                colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Purple, unfocusedBorderColor = Border, cursorColor = Purple),
                                singleLine = true)
                            if (!spotifyConfigured) {
                                Spacer(Modifier.height(12.dp))
                                OutlinedTextField(clientIdInput, { clientIdInput = it },
                                    label = { Text("Spotify Client ID") },
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Purple, unfocusedBorderColor = Border, cursorColor = Purple),
                                    singleLine = true)
                                Spacer(Modifier.height(10.dp))
                                OutlinedTextField(clientSecretInput, { clientSecretInput = it },
                                    label = { Text("Spotify Client Secret") },
                                    modifier = Modifier.fillMaxWidth(),
                                    colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = Purple, unfocusedBorderColor = Border, cursorColor = Purple),
                                    singleLine = true)
                            }
                            Spacer(Modifier.height(20.dp))
                            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                                OutlinedButton({ showSpotifyDialog = false }, Modifier.weight(1f)) {
                                    Text("Annulla", color = TextSecondary)
                                }
                                Button({
                                    if (!spotifyConfigured) {
                                        onSetSpotifyCredentials(clientIdInput, clientSecretInput)
                                    }
                                    onImportSpotify(spotifyUrl)
                                }, Modifier.weight(1f), colors = ButtonDefaults.buttonColors(Purple)) {
                                    Text("Importa", color = Color(0xFF0A0714))
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun PlaylistTab(
    playlists: List<UserPlaylist>,
    currentTrackId: Long?,
    onTrackClick: (Track) -> Unit,
    onRemoveFromPlaylist: (Long, Long) -> Unit,
    onDeletePlaylist: (Long) -> Unit
) {
    if (playlists.isEmpty()) {
        Empty("\uD83C\uDFB6", "Nessuna playlist", "Crea una playlist dal player toccando +")
        return
    }
    LazyColumn(
        modifier = Modifier.padding(horizontal = 12.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 130.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        items(playlists, key = { it.id }) { pl ->
            Column(modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2).padding(12.dp)) {
                Row(
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(12.dp)
                ) {
                    Box(Modifier.size(48.dp).clip(RoundedCornerShape(12.dp)).background(PurpleDim), Alignment.Center) {
                        Icon(Icons.Default.QueueMusic, "Playlist", Modifier.size(24.dp), Purple)
                    }
                    Column(Modifier.weight(1f)) {
                        Text(pl.name, color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 15.sp)
                        Text("${pl.trackIds.size} brani", color = TextTertiary, fontSize = 12.sp)
                    }
                    IconButton(onClick = { onDeletePlaylist(pl.id) }, Modifier.size(32.dp)) {
                        Icon(Icons.Default.Delete, "Elimina", Modifier.size(18.dp), TextTertiary)
                    }
                }
            }
        }
    }
}

@Composable
private fun FavTab(favs: List<FavoriteTrack>, sort: LibrarySort, onSort: (LibrarySort) -> Unit,
                   onClick: (FavoriteTrack) -> Unit, onRemove: (FavoriteTrack) -> Unit) {
    if (favs.isEmpty()) { Empty("\u2661", "Nessun brano salvato", "Cerca un brano e tocca \u2661 per salvarlo"); return }
    Column {
        LazyRow(Modifier.fillMaxWidth().padding(horizontal = 14.dp, vertical = 10.dp),
            horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            items(LibrarySort.entries, key = { it.name }) { s ->
                val a = sort == s
                FilterChip(selected = a, onClick = { onSort(s) },
                    label = { Text(s.label, fontSize = 12.sp, fontWeight = FontWeight.SemiBold,
                        color = if (a) Color(0xFF0A0714) else TextSecondary) },
                    colors = FilterChipDefaults.filterChipColors(
                        selectedContainerColor = Purple, containerColor = PurpleDim.copy(alpha = 0.08f)),
                    border = FilterChipDefaults.filterChipBorder(
                        enabled = true, borderColor = Border, selectedBorderColor = Purple.copy(0.5f),
                        selected = a),
                    shape = RoundedCornerShape(24.dp))
            }
        }
        LazyColumn(Modifier.padding(horizontal = 12.dp),
            contentPadding = PaddingValues(bottom = 130.dp),
            verticalArrangement = Arrangement.spacedBy(6.dp)) {
            items(favs, key = { it.deezerId }) { FavItem(it, { onClick(it) }, { onRemove(it) }) }
        }
    }
}

@Composable
private fun RecentTab(recent: List<Track>, onClick: (Track) -> Unit) {
    if (recent.isEmpty()) { Empty("\u23EE", "Nessun brano ascoltato", "I brani recenti appariranno qui"); return }
    LazyColumn(
        modifier = Modifier.padding(horizontal = 12.dp),
        contentPadding = PaddingValues(top = 12.dp, bottom = 130.dp),
        verticalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        items(recent, key = { it.id }) { track ->
            Row(
                modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2)
                    .clickable { onClick(track) }.padding(12.dp),
                verticalAlignment = Alignment.CenterVertically,
                horizontalArrangement = Arrangement.spacedBy(12.dp)
            ) {
                val a = track.album.bestCover
                if (!a.isNullOrBlank())
                    AsyncImage(model = a, contentDescription = null, contentScale = ContentScale.Crop,
                        modifier = Modifier.size(50.dp).clip(RoundedCornerShape(10.dp)))
                else
                    Box(Modifier.size(50.dp).clip(RoundedCornerShape(10.dp)).background(Bg3), Alignment.Center) {
                        Text("\u266A", color = TextTertiary, fontSize = 20.sp)
                    }
                Column(Modifier.weight(1f)) {
                    Text(track.title, color = TextPrimary, fontWeight = FontWeight.SemiBold,
                        fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    Text(track.artist.name, color = TextSecondary, fontSize = 12.sp,
                        maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
                Icon(Icons.Default.PlayArrow, "Riproduci", Modifier.size(20.dp), TextTertiary)
            }
        }
    }
}

@Composable
private fun FavItem(fav: FavoriteTrack, onClick: () -> Unit, onRemove: () -> Unit) {
    Row(
        modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(16.dp)).background(Bg2)
            .clickable(onClick = onClick).padding(12.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        val a = fav.art
        if (!a.isNullOrBlank())
            AsyncImage(model = a, contentDescription = null, contentScale = ContentScale.Crop,
                modifier = Modifier.size(54.dp).clip(RoundedCornerShape(12.dp)))
        else
            Box(Modifier.size(54.dp).clip(RoundedCornerShape(12.dp))
                .background(Brush.linearGradient(listOf(PurpleMid.copy(0.3f), Bg3), Offset.Zero, Offset(54f, 54f))),
                Alignment.Center) { Text("\u266A", color = Purple.copy(0.6f), fontSize = 22.sp) }
        Column(Modifier.weight(1f)) {
            Text(fav.title, color = TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 14.sp,
                maxLines = 1, overflow = TextOverflow.Ellipsis)
            Spacer(Modifier.height(2.dp))
            Text(fav.artist, color = TextSecondary, fontSize = 12.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
            Text(buildString { append(fav.album); if (fav.duration > 0) append("  \u00B7  ${formatDuration(fav.duration)}") },
                color = TextTertiary, fontSize = 11.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
        }
        Box(Modifier.size(36.dp).clip(RoundedCornerShape(10.dp)).background(CoralDim).clickable(onClick = onRemove),
            Alignment.Center) {
            Text("\u2665", color = Coral, fontSize = 18.sp)
        }
    }
}

@Composable
private fun LibTab(label: String, icon: ImageVector, selected: Boolean, onClick: () -> Unit) {
    Row(
        modifier = Modifier.clip(RoundedCornerShape(20.dp)).background(if (selected) PurpleDim else Color.Transparent)
            .clickable(onClick = onClick).padding(horizontal = 14.dp, vertical = 8.dp),
        verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(6.dp)
    ) {
        Icon(icon, label, Modifier.size(14.dp), tint = if (selected) Purple else TextTertiary)
        Text(label, color = if (selected) Purple else TextTertiary, fontSize = 13.sp, fontWeight = FontWeight.SemiBold)
    }
}

@Composable
private fun Empty(icon: String, title: String, sub: String) {
    Box(Modifier.fillMaxSize(), Alignment.Center) {
        Column(horizontalAlignment = Alignment.CenterHorizontally) {
            Text(icon, fontSize = 48.sp, color = TextTertiary)
            Spacer(Modifier.height(16.dp))
            Text(title, color = TextSecondary, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(6.dp))
            Text(sub, color = TextTertiary, fontSize = 13.sp, textAlign = TextAlign.Center)
        }
    }
}

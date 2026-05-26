package org.musicwavver.ui

import androidx.compose.animation.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import org.musicwavver.model.DeezerArtistAlbum
import org.musicwavver.model.Track
import org.musicwavver.ui.theme.*

@Composable
fun ArtistScreen(
    state: ArtistViewState,
    currentTrackId: Long?,
    favorites: Set<Long>,
    onTrackClick: (Track) -> Unit,
    onFavClick: (Track) -> Unit,
    onFollowClick: () -> Unit,
    onClose: () -> Unit,
    onPlayAll: (List<Track>) -> Unit,
    onShuffleAll: (List<Track>) -> Unit,
    onAlbumClick: (DeezerArtistAlbum) -> Unit = {},
    onShare: () -> Unit = {}
) {
    val visible = state !is ArtistViewState.Hidden

    AnimatedVisibility(
        visible = visible,
        enter = slideInVertically(initialOffsetY = { it }),
        exit  = slideOutVertically(targetOffsetY = { it })
    ) {
        when (state) {
            is ArtistViewState.Hidden  -> {}
            is ArtistViewState.Loading -> Box(Modifier.fillMaxSize().background(Bg), Alignment.Center) {
                CircularProgressIndicator(color = Purple, strokeWidth = 3.dp)
            }
            is ArtistViewState.Ready   -> ArtistContent(state, currentTrackId, favorites, onTrackClick, onFavClick, onFollowClick, onClose, onPlayAll, onShuffleAll, onAlbumClick, onShare)
        }
    }
}

@Composable
private fun ArtistContent(
    state: ArtistViewState.Ready,
    currentTrackId: Long?,
    favorites: Set<Long>,
    onTrackClick: (Track) -> Unit,
    onFavClick: (Track) -> Unit,
    onFollowClick: () -> Unit,
    onClose: () -> Unit,
    onPlayAll: (List<Track>) -> Unit,
    onShuffleAll: (List<Track>) -> Unit,
    onAlbumClick: (DeezerArtistAlbum) -> Unit = {},
    onShare: () -> Unit = {}
) {
    val scrollState = rememberScrollState()
    var tab by remember { mutableIntStateOf(0) }

    Box(Modifier.fillMaxSize().background(Bg)) {
        Column(Modifier.fillMaxSize()) {
            Box(
                modifier = Modifier.fillMaxWidth().height(360.dp)
            ) {
                if (!state.coverUrl.isNullOrBlank()) {
                    AsyncImage(model = state.coverUrl, contentDescription = null,
                        contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
                } else {
                    Box(Modifier.fillMaxSize().background(Bg2))
                }
                Box(Modifier.fillMaxSize().background(
                    Brush.verticalGradient(
                        colors = listOf(Bg.copy(alpha = 0.3f), Color.Transparent, Bg),
                        0f, Float.POSITIVE_INFINITY
                    )
                ))

                Column(
                    modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
                    verticalArrangement = Arrangement.Bottom
                ) {
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(onClick = onClose, Modifier.size(40.dp)) {
                            Icon(Icons.Default.ArrowBackIosNew, "Indietro", tint = TextSecondary, modifier = Modifier.size(20.dp))
                        }
                        IconButton(onShare, Modifier.size(40.dp)) {
                            Icon(Icons.Default.Share, "Condividi", Modifier.size(20.dp), TextSecondary)
                        }
                    }
                    Spacer(Modifier.weight(1f))
                    Text(state.name, color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 32.sp,
                        maxLines = 2, overflow = TextOverflow.Ellipsis)
                    if (state.monthlyListeners.isNotEmpty()) {
                        Text(state.monthlyListeners, color = TextSecondary, fontSize = 13.sp,
                            modifier = Modifier.padding(top = 4.dp, bottom = 16.dp))
                    } else {
                        Spacer(Modifier.height(16.dp))
                    }
                }
            }

            Column(
                modifier = Modifier.fillMaxSize()
                    .verticalScroll(scrollState)
                    .padding(horizontal = 16.dp)
            ) {
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    OutlinedButton(onClick = onFollowClick,
                        border = BorderStroke(1.dp, if (state.isFollowed) Purple else TextSecondary),
                        shape = RoundedCornerShape(20.dp),
                        colors = ButtonDefaults.outlinedButtonColors(
                            contentColor = if (state.isFollowed) Purple else TextSecondary
                        )
                    ) {
                        Text(if (state.isFollowed) "Segui gi\u00E0" else "Segui",
                            fontWeight = FontWeight.Bold, fontSize = 13.sp)
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        FilledIconButton(onClick = { onShuffleAll(state.tracks) }, Modifier.size(48.dp),
                            colors = IconButtonDefaults.filledIconButtonColors(
                                containerColor = Color(0xFF1DB954),
                                contentColor = Color(0xFF0A0714)
                            )) {
                            Icon(Icons.Default.Shuffle, "Riproduci in ordine casuale", Modifier.size(24.dp))
                        }
                        IconButton(onClick = { onPlayAll(state.tracks) }, Modifier.size(48.dp)) {
                            Icon(Icons.Default.PlayArrow, "Riproduci tutto", Modifier.size(28.dp), Color(0xFF1DB954))
                        }
                    }
                }

                Spacer(Modifier.height(20.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(24.dp)) {
                    TabBtn("Musica", tab == 0) { tab = 0 }
                    TabBtn("Eventi", tab == 1) { tab = 1 }
                }
                Spacer(Modifier.height(4.dp))
                HorizontalDivider(color = Border, thickness = 0.5.dp)
                Spacer(Modifier.height(12.dp))

                if (tab == 0) {
                    Text("Popolari", color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 17.sp)
                    Spacer(Modifier.height(8.dp))
                    state.tracks.take(5).forEachIndexed { i, track ->
                        val isFav = favorites.contains(track.id)
                        val isCurrent = track.id == currentTrackId
                        Row(
                            modifier = Modifier.fillMaxWidth()
                                .clip(RoundedCornerShape(8.dp))
                                .clickable { onTrackClick(track) }
                                .padding(vertical = 8.dp),
                            verticalAlignment = Alignment.CenterVertically,
                            horizontalArrangement = Arrangement.spacedBy(12.dp)
                        ) {
                            Text("${i + 1}", color = TextTertiary, fontSize = 14.sp,
                                fontWeight = FontWeight.Bold, modifier = Modifier.width(24.dp))
                            val art = track.album.bestCover
                            Box(Modifier.size(48.dp).clip(RoundedCornerShape(6.dp))) {
                                if (!art.isNullOrBlank()) {
                                    AsyncImage(model = art, contentDescription = null,
                                        contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
                                } else {
                                    Box(Modifier.fillMaxSize().background(Bg3), Alignment.Center) {
                                        Text("\u266A", color = TextTertiary, fontSize = 18.sp)
                                    }
                                }
                                if (isCurrent) {
                                    Box(Modifier.fillMaxSize().background(Purple.copy(alpha = 0.3f)), Alignment.Center) {
                                        Text("\u25B6", color = TextPrimary, fontSize = 18.sp)
                                    }
                                }
                            }
                            Column(Modifier.weight(1f)) {
                                Text(track.title, color = TextPrimary, fontWeight = FontWeight.SemiBold, fontSize = 14.sp,
                                    maxLines = 1, overflow = TextOverflow.Ellipsis)
                                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                                    Box(Modifier.clip(RoundedCornerShape(2.dp)).background(Surface3)
                                        .padding(horizontal = 4.dp, vertical = 1.dp)) {
                                        Text("E", color = TextTertiary, fontSize = 9.sp, fontWeight = FontWeight.Bold)
                                    }
                                    val count = 50_000_000 - i * 8_000_000 + (track.hashCode() % 1_000_000)
                                    val label = if (count >= 1_000_000) "${"%.0f".format(count / 1_000_000f)}" else "${count / 1_000}K"
                                    Text("$label", color = TextTertiary, fontSize = 11.sp)
                                }
                            }
                            if (isFav) {
                                Icon(Icons.Default.Favorite, "Salvato", Modifier.size(16.dp), Color(0xFF1DB954))
                            }
                            IconButton(onClick = { onFavClick(track) }, Modifier.size(32.dp)) {
                                Icon(Icons.Default.MoreHoriz, "Altre opzioni", Modifier.size(16.dp), TextTertiary)
                            }
                        }
                        if (i < state.tracks.size - 1 && i < 4) {
                            HorizontalDivider(color = Border.copy(alpha = 0.5f), thickness = 0.5.dp,
                                modifier = Modifier.padding(start = 36.dp))
                        }
                    }

                    if (state.albums.isNotEmpty()) {
                        Spacer(Modifier.height(24.dp))
                        Text("Album", color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 17.sp)
                        Spacer(Modifier.height(8.dp))
                        state.albums.forEach { album ->
                            Row(
                                modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(8.dp))
                                    .clickable { onAlbumClick(album) }
                                    .padding(vertical = 6.dp),
                                verticalAlignment = Alignment.CenterVertically,
                                horizontalArrangement = Arrangement.spacedBy(12.dp)
                            ) {//giorgio non sa cos'è il # su python
                                val pic = album.bestCover
                                Box(Modifier.size(52.dp).clip(RoundedCornerShape(6.dp))) {
                                    if (!pic.isNullOrBlank()) {
                                        AsyncImage(model = pic, contentDescription = null,
                                            contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
                                    } else {
                                        Box(Modifier.fillMaxSize().background(Bg3), Alignment.Center) {
                                            Text("\u266A", color = TextTertiary, fontSize = 18.sp)
                                        }
                                    }
                                }
                                Column(Modifier.weight(1f)) {
                                    Text(album.title, color = TextPrimary, fontWeight = FontWeight.SemiBold,
                                        fontSize = 14.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                                    Text("${album.releaseDate?.take(4) ?: ""}  \u00B7  ${album.nbTracks} brani",
                                        color = TextSecondary, fontSize = 12.sp)
                                }
                            }
                        }
                    }
                } else {
                    Box(Modifier.fillMaxWidth().padding(vertical = 48.dp), Alignment.Center) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Text("\uD83C\uDF89", fontSize = 36.sp)
                            Spacer(Modifier.height(12.dp))
                            Text("Nessun evento imminente", color = TextTertiary, fontSize = 14.sp)
                        }
                    }
                }
                Spacer(Modifier.height(32.dp).navigationBarsPadding())
            }
        }
    }
}

@Composable
private fun TabBtn(label: String, selected: Boolean, onClick: () -> Unit) {
    Column(horizontalAlignment = Alignment.CenterHorizontally) {
        Text(label, color = if (selected) TextPrimary else TextTertiary,
            fontWeight = FontWeight.SemiBold, fontSize = 14.sp,
            modifier = Modifier.clickable(onClick = onClick).padding(vertical = 8.dp))
        if (selected) {
            Box(Modifier.width(24.dp).height(3.dp).clip(RoundedCornerShape(2.dp)).background(Color(0xFF1DB954)))
        } else {
            Spacer(Modifier.height(3.dp))
        }
    }
}

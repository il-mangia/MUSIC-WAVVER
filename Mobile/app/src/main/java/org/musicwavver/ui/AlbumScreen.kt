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
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import org.musicwavver.model.Track
import org.musicwavver.ui.theme.*

@Composable
fun AlbumScreen(
    state: AlbumViewState,
    currentTrackId: Long?,
    favorites: Set<Long>,
    onTrackClick: (Track) -> Unit,
    onFavClick: (Track) -> Unit,
    onArtistClick: (String, String?, List<Track>) -> Unit,
    onClose: () -> Unit,
    onPlayAll: (List<Track>) -> Unit,
    onShuffleAll: (List<Track>) -> Unit,
    onShare: () -> Unit = {}
) {
    val visible = state !is AlbumViewState.Hidden

    AnimatedVisibility(
        visible = visible,
        enter = slideInVertically(initialOffsetY = { it }),
        exit  = slideOutVertically(targetOffsetY = { it })
    ) {
        when (state) {
            is AlbumViewState.Hidden  -> {}
            is AlbumViewState.Loading -> Box(Modifier.fillMaxSize().background(Bg), Alignment.Center) {
                CircularProgressIndicator(color = Purple, strokeWidth = 3.dp)
            }
            is AlbumViewState.Ready   -> AlbumContent(state, currentTrackId, favorites, onTrackClick, onFavClick, onArtistClick, onClose, onPlayAll, onShuffleAll, onShare)
        }
    }
}

@Composable
private fun AlbumContent(
    state: AlbumViewState.Ready,
    currentTrackId: Long?,
    favorites: Set<Long>,
    onTrackClick: (Track) -> Unit,
    onFavClick: (Track) -> Unit,
    onArtistClick: (String, String?, List<Track>) -> Unit,
    onClose: () -> Unit,
    onPlayAll: (List<Track>) -> Unit,
    onShuffleAll: (List<Track>) -> Unit,
    onShare: () -> Unit = {}
) {
    val scrollState = rememberScrollState()
    val bgColor = Color(state.coverColor)

    Box(Modifier.fillMaxSize().background(Bg)) {
        Column(Modifier.fillMaxSize()) {
            Box(
                modifier = Modifier.fillMaxWidth().height(360.dp)
            ) {
                Box(Modifier.fillMaxSize().background(
                    Brush.verticalGradient(colors = listOf(bgColor, Bg))
                ))
                if (!state.coverUrl.isNullOrBlank()) {
                    AsyncImage(model = state.coverUrl, contentDescription = null,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.fillMaxSize().alpha(0.15f))
                }
                Box(Modifier.fillMaxSize().background(
                    Brush.verticalGradient(colors = listOf(Color.Transparent, Bg))
                ))

                Column(
                    modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Spacer(Modifier.height(8.dp).statusBarsPadding())
                    Row(
                        Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        IconButton(onClick = onClose, modifier = Modifier.size(40.dp)) {
                            Icon(Icons.Default.ArrowBackIosNew, "Indietro", tint = TextSecondary, modifier = Modifier.size(20.dp))
                        }
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            IconButton({}, Modifier.size(40.dp)) {
                                Icon(Icons.Default.FavoriteBorder, "Aggiungi ai preferiti", Modifier.size(20.dp), TextTertiary)
                            }
                            IconButton(onShare, Modifier.size(40.dp)) {
                                Icon(Icons.Default.Share, "Condividi", Modifier.size(20.dp), TextTertiary)
                            }
                        }
                    }
                    Spacer(Modifier.weight(1f))
                    Box(
                        modifier = Modifier.size(200.dp).clip(RoundedCornerShape(12.dp))
                            .background(Bg3, RoundedCornerShape(12.dp))
                    ) {
                        if (!state.coverUrl.isNullOrBlank()) {
                            AsyncImage(model = state.coverUrl, contentDescription = null,
                                contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
                        } else {
                            Box(Modifier.fillMaxSize(), Alignment.Center) {
                                Text("\u266A", color = TextTertiary, fontSize = 48.sp)
                            }
                        }
                    }
                    Spacer(Modifier.height(16.dp))
                }
            }

            Column(
                modifier = Modifier.fillMaxSize().verticalScroll(scrollState)
                    .padding(horizontal = 16.dp),
                horizontalAlignment = Alignment.Start
            ) {
                Text(state.title, color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 22.sp,
                    maxLines = 2, overflow = TextOverflow.Ellipsis)

                Spacer(Modifier.height(8.dp))
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    Box(Modifier.size(24.dp).clip(CircleShape).background(PurpleDim), Alignment.Center) {
                        Text(state.artistName.take(1).uppercase(), color = Purple, fontSize = 11.sp, fontWeight = FontWeight.Bold)
                    }
                    Text(state.artistName, color = Purple, fontWeight = FontWeight.SemiBold, fontSize = 14.sp,
                        modifier = Modifier.clickable { onArtistClick(state.artistName, state.coverUrl, state.tracks) })
                }
                Spacer(Modifier.height(4.dp))
                Text("Album \u00B7 ${state.tracks.size} brani", color = TextTertiary, fontSize = 12.sp)

                Spacer(Modifier.height(16.dp))
                Row(
                    Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        IconButton({}, Modifier.size(36.dp).clip(RoundedCornerShape(10.dp)).background(Surface2)) {
                            Icon(Icons.Default.FavoriteBorder, "Aggiungi ai preferiti", Modifier.size(18.dp), TextTertiary)
                        }
                        IconButton({}, Modifier.size(36.dp).clip(RoundedCornerShape(10.dp)).background(Surface2)) {
                            Icon(Icons.Default.FileDownload, "Scarica", Modifier.size(18.dp), TextTertiary)
                        }
                        IconButton({}, Modifier.size(36.dp).clip(RoundedCornerShape(10.dp)).background(Surface2)) {
                            Icon(Icons.Default.MoreHoriz, "Altre opzioni", Modifier.size(18.dp), TextTertiary)
                        }
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
                        IconButton(onClick = { onShuffleAll(state.tracks) }, Modifier.size(36.dp)) {
                            Icon(Icons.Default.Shuffle, "Riproduci in ordine casuale", Modifier.size(22.dp), TextTertiary)
                        }
                        FilledIconButton(onClick = { onPlayAll(state.tracks) }, Modifier.size(56.dp).clip(CircleShape),
                            colors = IconButtonDefaults.filledIconButtonColors(
                                containerColor = Color(0xFF1DB954),
                                contentColor = Color(0xFF0A0714)
                            )) {
                            Icon(Icons.Default.PlayArrow, "Riproduci tutto", Modifier.size(32.dp))
                        }
                    }
                }

                Spacer(Modifier.height(16.dp))
                HorizontalDivider(color = Border, thickness = 0.5.dp)
                Spacer(Modifier.height(8.dp))

                state.tracks.forEachIndexed { i, track ->
                    val isFav = favorites.contains(track.id)
                    val isCurrent = track.id == currentTrackId
                    Row(
                        modifier = Modifier.fillMaxWidth()
                            .clip(RoundedCornerShape(8.dp))
                            .background(if (isCurrent) PurpleDim.copy(0.3f) else Color.Transparent)
                            .clickable { onTrackClick(track) }
                            .padding(horizontal = 4.dp, vertical = 10.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(12.dp)
                    ) {
                        Text("${i + 1}", color = if (isCurrent) Purple else TextTertiary, fontSize = 12.sp,
                            fontWeight = FontWeight.Medium, modifier = Modifier.width(24.dp))
                        Column(Modifier.weight(1f)) {
                            Text(track.title, color = if (isCurrent) Purple else TextPrimary,
                                fontWeight = FontWeight.Medium, fontSize = 14.sp,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text(track.artist.name, color = TextSecondary, fontSize = 12.sp,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                        IconButton(onClick = { onFavClick(track) }, Modifier.size(32.dp)) {
                            if (isFav) {
                                Icon(Icons.Default.Favorite, "Rimuovi dai preferiti", Modifier.size(16.dp), Coral)
                            } else {
                                Icon(Icons.Default.MoreHoriz, "Altre opzioni", Modifier.size(16.dp), TextTertiary)
                            }
                        }
                    }
                }
                Spacer(Modifier.height(32.dp).navigationBarsPadding())
            }
        }
    }
}

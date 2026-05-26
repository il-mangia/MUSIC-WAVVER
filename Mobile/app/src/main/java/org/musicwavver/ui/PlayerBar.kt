package org.musicwavver.ui

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
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
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import org.musicwavver.model.Track
import org.musicwavver.ui.theme.*

@Composable
fun PlayerBar(
    track: Track?,
    isPlaying: Boolean,
    isResolving: Boolean,
    shuffleEnabled: Boolean,
    repeatMode: PlayMode,
    isFav: Boolean,
    onTap: () -> Unit,
    onTogglePlay: () -> Unit,
    onPrev: () -> Unit,
    onNext: () -> Unit,
    onFavToggle: () -> Unit,
    onAddToPlaylist: () -> Unit,
    onArtistClick: () -> Unit
) {
    if (track == null) return

    val haptic = LocalHapticFeedback.current

    val playRotation by animateFloatAsState(
        targetValue = if (isPlaying) 0f else -90f,
        animationSpec = spring(stiffness = Spring.StiffnessMediumLow)
    )
    val favScale by animateFloatAsState(
        targetValue = if (isFav) 1.25f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessHigh)
    )

    val art = track.album.bestCover

    Column(Modifier.background(Bg).clickable(onClick = onTap).padding(start = 8.dp, end = 4.dp, top = 4.dp, bottom = 4.dp)) {
        Row(Modifier.fillMaxWidth().height(52.dp), verticalAlignment = Alignment.CenterVertically) {
            AsyncImage(
                model = art, contentDescription = "Copertina album",
                modifier = Modifier.size(44.dp).clip(RoundedCornerShape(6.dp)),
                contentScale = ContentScale.Crop
            )
            Spacer(Modifier.width(10.dp))
            Column(Modifier.weight(1f)) {
                Text(track.title, maxLines = 1, overflow = TextOverflow.Ellipsis,
                    color = TextPrimary, fontSize = 13.sp, fontWeight = FontWeight.Medium)
                Text(track.artist.name, maxLines = 1, overflow = TextOverflow.Ellipsis,
                    color = TextSecondary, fontSize = 11.sp)
            }
            IconButton(onClick = { haptic.performHapticFeedback(HapticFeedbackType.LongPress); onFavToggle() },
                Modifier.size(36.dp)) {
                Icon(
                    if (isFav) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                    if (isFav) "Rimuovi dai preferiti" else "Aggiungi ai preferiti",
                    Modifier.size(18.dp).graphicsLayer { scaleX = favScale; scaleY = favScale },
                    tint = if (isFav) Purple else TextTertiary
                )
            }
            IconButton(onClick = onPrev, Modifier.size(36.dp)) {
                Icon(Icons.Default.SkipPrevious, "Brano precedente", Modifier.size(20.dp), tint = TextSecondary)
            }
            IconButton(onClick = onTogglePlay, Modifier.size(36.dp).clip(CircleShape).background(Purple.copy(alpha = 0.2f))) {
                Icon(if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                    if (isPlaying) "Metti in pausa" else "Riproduci",
                    Modifier.size(22.dp).rotate(playRotation), tint = TextPrimary)
            }
            IconButton(onClick = onNext, Modifier.size(36.dp)) {
                Icon(Icons.Default.SkipNext, "Brano successivo", Modifier.size(20.dp), tint = TextSecondary)
            }
            IconButton(onClick = onAddToPlaylist, Modifier.size(36.dp)) {
                Icon(Icons.Default.PlaylistAdd, "Aggiungi alla playlist", Modifier.size(18.dp), tint = TextTertiary)
            }
        }
    }
}

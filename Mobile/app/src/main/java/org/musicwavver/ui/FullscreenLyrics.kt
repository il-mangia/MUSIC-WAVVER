package org.musicwavver.ui

import androidx.compose.animation.core.Spring
import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.animation.core.spring
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.itemsIndexed
import androidx.compose.foundation.lazy.rememberLazyListState
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
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import org.musicwavver.model.LyricLine
import org.musicwavver.model.Track
import org.musicwavver.ui.theme.*

@Composable
fun FullscreenLyrics(
    track: Track?,
    isPlaying: Boolean,
    currentPosition: Long,
    duration: Long,
    lyricsLines: List<LyricLine>,
    currentLyricIdx: Int,
    shuffleEnabled: Boolean,
    repeatMode: PlayMode,
    isFav: Boolean,
    onTogglePlay: () -> Unit,
    onPrev: () -> Unit,
    onNext: () -> Unit,
    onSeek: (Float) -> Unit,
    onToggleShuffle: () -> Unit,
    onCycleRepeat: () -> Unit,
    onFavToggle: () -> Unit,
    onBack: () -> Unit
) {
    val art = track?.album?.bestCover
    val listState = rememberLazyListState()

    val favScale by animateFloatAsState(
        targetValue = if (isFav) 1.25f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessHigh)
    )

    LaunchedEffect(currentLyricIdx) {
        if (currentLyricIdx < 0 || currentLyricIdx >= lyricsLines.size) return@LaunchedEffect
        withFrameNanos { }
        val info = listState.layoutInfo
        val vh = info.viewportEndOffset - info.viewportStartOffset
        if (vh > 0) {
            listState.scrollToItem(currentLyricIdx.coerceAtMost(lyricsLines.size - 1), -vh / 2)
        }
    }

    Box(Modifier.fillMaxSize().background(Bg)) {
        if (!art.isNullOrBlank()) {
            AsyncImage(
                model = art, contentDescription = null,
                contentScale = ContentScale.Crop,
                modifier = Modifier.fillMaxSize()
            )
        }
        Box(Modifier.fillMaxSize().background(Brush.verticalGradient(
            listOf(Bg.copy(alpha = 0.65f), Bg.copy(alpha = 0.88f), Bg.copy(alpha = 0.92f))
        )))

        Column(Modifier.fillMaxSize().statusBarsPadding()) {
            Spacer(Modifier.height(8.dp))

            Row(
                Modifier.fillMaxWidth().padding(horizontal = 8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onBack, Modifier.size(36.dp)) {
                    Icon(Icons.Filled.KeyboardArrowLeft, "Indietro", Modifier.size(22.dp), TextSecondary)
                }
                Spacer(Modifier.width(4.dp))
                if (!art.isNullOrBlank()) {
                    AsyncImage(
                        model = art, contentDescription = null,
                        contentScale = ContentScale.Crop,
                        modifier = Modifier.size(40.dp).clip(RoundedCornerShape(6.dp))
                    )
                }
                Spacer(Modifier.width(10.dp))
                Column(Modifier.weight(1f)) {
                    Text(track?.title ?: "", color = TextPrimary, fontWeight = FontWeight.Bold,
                        fontSize = 15.sp, maxLines = 1, overflow = TextOverflow.Ellipsis)
                    Text(track?.artist?.name ?: "", color = TextSecondary, fontSize = 12.sp,
                        maxLines = 1, overflow = TextOverflow.Ellipsis)
                }
                val haptic = LocalHapticFeedback.current
                IconButton(onClick = { haptic.performHapticFeedback(HapticFeedbackType.LongPress); onFavToggle() }, Modifier.size(36.dp)) {
                    Icon(
                        if (isFav) Icons.Default.Favorite else Icons.Default.FavoriteBorder,
                        null, Modifier.size(20.dp).graphicsLayer { scaleX = favScale; scaleY = favScale },
                        tint = if (isFav) Coral else TextSecondary
                    )
                }
                IconButton(onClick = { }, Modifier.size(36.dp)) {
                    Icon(Icons.Default.MoreVert, "Altre opzioni", Modifier.size(20.dp), TextSecondary)
                }
            }

            Spacer(Modifier.height(16.dp))

            if (lyricsLines.isEmpty()) {
                Box(Modifier.weight(1f), contentAlignment = Alignment.Center) {
                    Text("Nessun testo disponibile", color = TextTertiary, fontSize = 14.sp)
                }
            } else {
                LazyColumn(
                    state = listState,
                    modifier = Modifier.weight(1f).fillMaxWidth(),
                    horizontalAlignment = Alignment.CenterHorizontally,
                    contentPadding = PaddingValues(horizontal = 32.dp),
                    verticalArrangement = Arrangement.spacedBy(16.dp)
                ) {
                    itemsIndexed(lyricsLines) { i, line ->
                        val isCurrent = i == currentLyricIdx
                        Text(
                            text = line.text,
                            color = if (isCurrent) TextPrimary else TextTertiary.copy(alpha = 0.35f),
                            fontSize = if (isCurrent) 20.sp else 15.sp,
                            fontWeight = if (isCurrent) FontWeight.Bold else FontWeight.Normal,
                            textAlign = TextAlign.Center,
                            modifier = Modifier.fillMaxWidth(),
                            maxLines = 3,
                            overflow = TextOverflow.Ellipsis
                        )
                    }
                }
            }

            Column(Modifier.fillMaxWidth().padding(horizontal = 24.dp)) {
                Slider(
                    value = if (duration > 0) (currentPosition.toFloat() / duration).coerceIn(0f, 1f) else 0f,
                    onValueChange = onSeek,
                    colors = SliderDefaults.colors(
                        thumbColor = Purple, activeTrackColor = Purple, inactiveTrackColor = Surface3
                    ),
                    modifier = Modifier.fillMaxWidth().height(24.dp)
                )
                Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                    Text(formatDurationMsFull(currentPosition), color = TextTertiary, fontSize = 11.sp)
                    Text(formatDurationMsFull(duration), color = TextTertiary, fontSize = 11.sp)
                }
            }

            Spacer(Modifier.height(8.dp))

            Row(
                Modifier.fillMaxWidth().padding(horizontal = 24.dp, vertical = 8.dp),
                horizontalArrangement = Arrangement.SpaceEvenly,
                verticalAlignment = Alignment.CenterVertically
            ) {
                IconButton(onClick = onToggleShuffle, Modifier.size(44.dp)) {
                    Icon(Icons.Default.Shuffle, "Mescola", Modifier.size(22.dp),
                        tint = if (shuffleEnabled) Purple else TextTertiary)
                }
                IconButton(onClick = onPrev, Modifier.size(48.dp)) {
                    Icon(Icons.Default.SkipPrevious, "Brano precedente", Modifier.size(28.dp), TextSecondary)
                }
                FilledIconButton(onClick = onTogglePlay, Modifier.size(64.dp),
                    colors = IconButtonDefaults.filledIconButtonColors(Purple, Color(0xFF0A0714)),
                    shape = CircleShape
                ) {
                    Icon(
                        if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow,
                        null, Modifier.size(32.dp)
                    )
                }
                IconButton(onClick = onNext, Modifier.size(48.dp)) {
                    Icon(Icons.Default.SkipNext, "Brano successivo", Modifier.size(28.dp), TextSecondary)
                }
                IconButton(onClick = onCycleRepeat, Modifier.size(44.dp)) {
                    Icon(
                        when (repeatMode) { PlayMode.ONE -> Icons.Default.RepeatOne; else -> Icons.Default.Repeat },
                        null, Modifier.size(22.dp),
                        tint = if (repeatMode == PlayMode.NONE) TextTertiary else Purple
                    )
                }
            }

            Spacer(Modifier.height(16.dp).navigationBarsPadding())
        }
    }
}

private fun formatDurationMsFull(ms: Long): String {
    val s = (ms / 1000).toInt()
    return "${s / 60}:${(s % 60).toString().padStart(2, '0')}"
}

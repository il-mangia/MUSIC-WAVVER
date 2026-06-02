package org.musicwavver.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.foundation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.rotate
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.hapticfeedback.HapticFeedbackType
import androidx.compose.ui.platform.LocalHapticFeedback
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import org.musicwavver.model.LyricLine
import org.musicwavver.model.Track
import org.musicwavver.ui.MainViewModel.DownloadState
import org.musicwavver.ui.theme.*
import coil.compose.AsyncImage
import androidx.compose.ui.window.Dialog

@Composable
fun ExpandedPlayer(
    visible: Boolean,
    track: Track?,
    isPlaying: Boolean,
    currentPosition: Long,
    duration: Long,
    shuffleEnabled: Boolean,
    repeatMode: PlayMode,
    sleepTimerRemaining: Long,
    currentQueue: List<Track>,
    showQueue: Boolean,
    onTogglePlay: () -> Unit,
    onPrev: () -> Unit,
    onNext: () -> Unit,
    onSeek: (Float) -> Unit,
    onClose: () -> Unit,
    onToggleShuffle: () -> Unit,
    onCycleRepeat: () -> Unit,
    onSetSleepTimer: (Int) -> Unit,
    onCancelSleepTimer: () -> Unit,
    onToggleQueue: () -> Unit,
    onPlayFromQueue: (Track) -> Unit,
    onRemoveFromQueue: (Track) -> Unit,
    isFav: Boolean = false,
    onFavToggle: () -> Unit = {},
    onAddToPlaylist: () -> Unit = {},
    onArtistClick: () -> Unit = {},
    onDownload: () -> Unit = {},
    downloadState: DownloadState = DownloadState.IDLE,
    onShare: () -> Unit = {},
    onFullscreenLyrics: () -> Unit = {},
    onEqualizer: () -> Unit = {},
    onMoveQueueUp: (Int) -> Unit = {},
    onMoveQueueDown: (Int) -> Unit = {},
    lyricsLines: List<LyricLine> = emptyList(),
    currentLyricIdx: Int = -1,
    sourceLabel: String = ""
) {
    if (!visible || track == null) return

    val progress = if (duration > 0) (currentPosition.toFloat() / duration).coerceIn(0f, 1f) else 0f
    var dragging by remember { mutableStateOf<Float?>(null) }
    val displayProgress = dragging ?: progress
    val art = track.album.bestCover
    var showSleep by remember { mutableStateOf(false) }

    val playRotation by animateFloatAsState(
        targetValue = if (isPlaying) 0f else -90f,
        animationSpec = spring(stiffness = Spring.StiffnessMediumLow)
    )
    val favScale by animateFloatAsState(
        targetValue = if (isFav) 1.2f else 1f,
        animationSpec = spring(stiffness = Spring.StiffnessHigh)
    )

    DraggableSheet(onClose = onClose, closePxThreshold = 80f, closeVelocityThreshold = 400f) {
        Box(Modifier.fillMaxSize().background(Bg)) {
            if (!art.isNullOrBlank())
                AsyncImage(model = art, contentDescription = null, contentScale = ContentScale.Crop,
                    modifier = Modifier.fillMaxSize().alpha(0.12f))

            Box(Modifier.fillMaxSize().background(Bg.copy(alpha = 0.85f)))

            Column(Modifier.fillMaxSize().statusBarsPadding().verticalScroll(rememberScrollState()),
                horizontalAlignment = Alignment.CenterHorizontally) {

                Spacer(Modifier.height(10.dp))
                Box(Modifier.width(40.dp).height(4.dp).clip(RoundedCornerShape(2.dp)).background(Surface3))

                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp, vertical = 14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column {
                        Text("IN RIPRODUZIONE", color = TextTertiary, fontSize = 10.sp,
                            fontWeight = FontWeight.Bold, letterSpacing = 1.5.sp)
                        Text(track.album.title, color = TextSecondary, fontSize = 12.sp,
                            maxLines = 1, overflow = TextOverflow.Ellipsis, modifier = Modifier.widthIn(max = 200.dp))
                    }
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        val dlColor = when (downloadState) {
                            DownloadState.DOWNLOADING, DownloadState.CONVERTING -> Coral
                            DownloadState.DONE -> Green
                            DownloadState.ERROR -> Red
                            else -> TextSecondary
                        }
                        SmallIconBtn({
                            if (downloadState != DownloadState.DOWNLOADING && downloadState != DownloadState.CONVERTING)
                                onDownload()
                        }, dlColor) {
                            when (downloadState) {
                                DownloadState.DOWNLOADING, DownloadState.CONVERTING -> {
                                    CircularProgressIndicator(Modifier.size(16.dp), strokeWidth = 2.dp, color = Coral)
                                }
                                DownloadState.DONE -> Icon(Icons.Default.Check, "Scaricato", Modifier.size(18.dp))
                                DownloadState.ERROR -> Icon(Icons.Default.Warning, "Errore download", Modifier.size(18.dp))
                                else -> Icon(Icons.Default.Download, "Scarica", Modifier.size(18.dp))
                            }
                        }
                        SmallIconBtn(onAddToPlaylist, TextSecondary) {
                            Text("+", fontWeight = FontWeight.Bold, fontSize = 16.sp)
                        }
                        SmallIconBtn(onToggleQueue, if (showQueue) Purple else TextSecondary) {
                            Icon(Icons.Default.QueueMusic, "Coda", Modifier.size(18.dp))
                        }
                        SmallIconBtn({ if (sleepTimerRemaining > 0) onCancelSleepTimer() else showSleep = true },
                            if (sleepTimerRemaining > 0) Coral else TextSecondary) {
                            Icon(Icons.Default.Bedtime, "Timer sonno", Modifier.size(18.dp))
                        }
                        SmallIconBtn(onEqualizer, TextSecondary) {
                            Text("EQ", fontWeight = FontWeight.Bold, fontSize = 13.sp)
                        }
                        SmallIconBtn(onShare, TextSecondary) {
                            Icon(Icons.Default.Share, "Condividi", Modifier.size(18.dp))
                        }
                        SmallIconBtn(onClose, TextSecondary) {
                            Icon(Icons.Default.Close, "Chiudi", Modifier.size(18.dp))
                        }
                    }
                }

                if (sleepTimerRemaining > 0) {
                    val s = (sleepTimerRemaining / 1000).toInt()
                    Box(Modifier.clip(RoundedCornerShape(20.dp)).background(CoralDim)
                        .padding(horizontal = 14.dp, vertical = 6.dp).clickable { onCancelSleepTimer() }) {
                        Text("\u23FE  ${s / 60}:${(s % 60).toString().padStart(2, '0')}  \u00D7",
                            color = Coral, fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                    }
                    Spacer(Modifier.height(8.dp))
                }

                Box(Modifier.padding(horizontal = 28.dp).fillMaxWidth().aspectRatio(1f).clip(RoundedCornerShape(24.dp))) {
                    if (!art.isNullOrBlank())
                        AsyncImage(model = art, contentDescription = null, contentScale = ContentScale.Crop,
                            modifier = Modifier.fillMaxSize())
                    else
                        Box(Modifier.fillMaxSize().background(Bg3), Alignment.Center) {
                            Text("\u266A", color = TextTertiary, fontSize = 72.sp) }
                }

                Spacer(Modifier.height(24.dp))

                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 28.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Column(Modifier.weight(1f)) {
                        Text(track.title, color = TextPrimary, fontWeight = FontWeight.Bold,
                            fontSize = 22.sp, maxLines = 2, overflow = TextOverflow.Ellipsis)
                        Spacer(Modifier.height(4.dp))
                        Text(track.artist.name, color = Purple, fontWeight = FontWeight.Medium,
                            fontSize = 15.sp, maxLines = 1, overflow = TextOverflow.Ellipsis,
                            modifier = Modifier.clickable(onClick = onArtistClick))
                    }
                    val haptic = LocalHapticFeedback.current
                    Box(Modifier.size(44.dp).clip(RoundedCornerShape(14.dp))
                        .background(if (isFav) CoralDim else Surface2)
                        .clickable { haptic.performHapticFeedback(HapticFeedbackType.LongPress); onFavToggle() }
                        .graphicsLayer { scaleX = favScale; scaleY = favScale },
                        Alignment.Center) {
                        Text(if (isFav) "\u2665" else "\u2661", color = if (isFav) Coral else TextTertiary, fontSize = 22.sp)
                    }
                }

                Spacer(Modifier.height(24.dp))

                Column(Modifier.fillMaxWidth().padding(horizontal = 28.dp)) {
                    val lastSeek = remember { mutableLongStateOf(0L) }
                    Slider(displayProgress,
                        onValueChange = {
                            dragging = it
                            val now = System.currentTimeMillis()
                            if (now - lastSeek.value > 100L) {
                                lastSeek.value = now
                                onSeek(it)
                            }
                        },
                        onValueChangeFinished = { dragging?.let { onSeek(it) }; dragging = null },
                        colors = SliderDefaults.colors(
                            thumbColor = TextPrimary, activeTrackColor = Purple, inactiveTrackColor = Surface3
                        ), modifier = Modifier.fillMaxWidth())
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Text(formatDurationMs(currentPosition), color = TextTertiary, fontSize = 11.sp)
                        Text(formatDurationMs(duration), color = TextTertiary, fontSize = 11.sp)
                    }
                }

                Spacer(Modifier.height(16.dp))

                Row(
                    modifier = Modifier.fillMaxWidth().padding(horizontal = 20.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    IconButton(onToggleShuffle, Modifier.size(48.dp)) {
                        Icon(Icons.Default.Shuffle, "Mescola", Modifier.size(22.dp),
                            tint = if (shuffleEnabled) Purple else TextTertiary)
                    }
                    IconButton(onPrev, Modifier.size(52.dp)) {
                        Icon(Icons.Default.SkipPrevious, "Brano precedente", Modifier.size(30.dp), tint = TextSecondary)
                    }
                    FilledIconButton(onTogglePlay, Modifier.size(72.dp),
                        colors = IconButtonDefaults.filledIconButtonColors(Purple, Color(0xFF0A0714))) {
                        Icon(if (isPlaying) Icons.Default.Pause else Icons.Default.PlayArrow, null,
                            Modifier.size(38.dp).rotate(playRotation))
                    }
                    IconButton(onNext, Modifier.size(52.dp)) {
                        Icon(Icons.Default.SkipNext, "Brano successivo", Modifier.size(30.dp), tint = TextSecondary)
                    }
                    IconButton(onCycleRepeat, Modifier.size(48.dp)) {
                        Icon(
                            when (repeatMode) { PlayMode.ONE -> Icons.Default.RepeatOne; else -> Icons.Default.Repeat },
                            null, Modifier.size(22.dp),
                            tint = if (repeatMode == PlayMode.NONE) TextTertiary else Purple
                        )
                    }
                }

                Spacer(Modifier.height(8.dp))

                Box(Modifier.fillMaxWidth().clickable { onFullscreenLyrics() }) {
                    LyricsDisplay(lyricsLines, currentLyricIdx)
                }

                Spacer(Modifier.height(12.dp))

                Row(Modifier.clip(RoundedCornerShape(8.dp)).background(PurpleDim)
                    .padding(horizontal = 12.dp, vertical = 6.dp),
                    verticalAlignment = Alignment.CenterVertically,
                    horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                    if (!sourceLabel.startsWith("Lossy")) LosslessBars()
                    Text(sourceLabel.ifBlank { "LOSSLESS \u00B7 Monochrome" }, color = Purple, fontSize = 11.sp,
                        fontWeight = FontWeight.Bold, letterSpacing = 0.5.sp)
                }

                Spacer(Modifier.height(32.dp).navigationBarsPadding())
            }

            AnimatedVisibility(showQueue,
                enter = slideInVertically { it } + fadeIn(),
                exit  = slideOutVertically { it } + fadeOut(),
                modifier = Modifier.align(Alignment.BottomCenter)) {
                QueueSheet(currentQueue, track, onPlayFromQueue, onRemoveFromQueue, onToggleQueue, onMoveQueueUp, onMoveQueueDown)
            }
        }
    }

    if (showSleep) SleepTimerDialog({ showSleep = false }, { onSetSleepTimer(it); showSleep = false })
}

@Composable
private fun QueueSheet(
    queue: List<Track>, current: Track,
    onPlay: (Track) -> Unit, onRemove: (Track) -> Unit, onClose: () -> Unit,
    onMoveUp: (Int) -> Unit = {}, onMoveDown: (Int) -> Unit = {}
) {
    DraggableSheet(onClose = onClose, closePxThreshold = 60f, closeVelocityThreshold = 300f) {
        Column(Modifier.fillMaxWidth().fillMaxHeight(0.55f)
            .clip(RoundedCornerShape(topStart = 28.dp, topEnd = 28.dp))
            .background(Bg2.copy(alpha = 0.97f))) {
            Box(Modifier.fillMaxWidth().padding(vertical = 10.dp), Alignment.Center) {
                Box(Modifier.width(40.dp).height(4.dp).clip(RoundedCornerShape(2.dp)).background(Surface3))
            }
            Text("Coda \u00B7 ${queue.size} brani", color = TextPrimary, fontWeight = FontWeight.Bold,
                fontSize = 16.sp, modifier = Modifier.padding(horizontal = 20.dp, vertical = 4.dp))
            HorizontalDivider(color = Border, thickness = 0.5.dp, modifier = Modifier.padding(horizontal = 16.dp, vertical = 8.dp))
            LazyColumn(Modifier.fillMaxSize().padding(horizontal = 8.dp).navigationBarsPadding()) {
                itemsIndexed(queue, key = { _, t -> t.id }) { idx, t ->
                    val isCur = t.id == current.id
                    Row(
                        modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp))
                            .background(if (isCur) PurpleDim else Color.Transparent)
                            .padding(horizontal = 8.dp, vertical = 6.dp),
                        verticalAlignment = Alignment.CenterVertically,
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            IconButton({ onMoveUp(idx) }, Modifier.size(24.dp), enabled = idx > 0) {
                                Icon(Icons.Default.KeyboardArrowUp, null, Modifier.size(18.dp),
                                    if (idx > 0) TextSecondary else TextTertiary)
                            }
                            IconButton({ onMoveDown(idx) }, Modifier.size(24.dp), enabled = idx < queue.size - 1) {
                                Icon(Icons.Default.KeyboardArrowDown, null, Modifier.size(18.dp),
                                    if (idx < queue.size - 1) TextSecondary else TextTertiary)
                            }
                        }
                        if (!isCur) {
                            Box(Modifier.size(40.dp).clickable { onPlay(t) }) {
                                val a = t.album.bestCover
                                if (!a.isNullOrBlank())
                                    AsyncImage(model = a, contentDescription = null, contentScale = ContentScale.Crop,
                                        modifier = Modifier.size(40.dp).clip(RoundedCornerShape(8.dp)))
                            }
                        } else {
                            Box(Modifier.size(40.dp).clip(RoundedCornerShape(8.dp)).background(PurpleDim), Alignment.Center) {
                                Icon(Icons.Default.PlayArrow, null, Modifier.size(20.dp), Purple)
                            }
                        }
                        Column(Modifier.weight(1f).clickable(enabled = !isCur) { onPlay(t) }) {
                            Text(t.title, color = if (isCur) Purple else TextPrimary,
                                fontWeight = FontWeight.SemiBold, fontSize = 13.sp,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                            Text(t.artist.name, color = TextSecondary, fontSize = 11.sp,
                                maxLines = 1, overflow = TextOverflow.Ellipsis)
                        }
                        if (!isCur) IconButton({ onRemove(t) }, Modifier.size(32.dp)) {
                            Icon(Icons.Default.Close, null, Modifier.size(16.dp), TextTertiary)
                        }
                    }
                }
            }
        }
    }
}

@Composable
private fun SleepTimerDialog(onDismiss: () -> Unit, onSet: (Int) -> Unit) {
    val opts = listOf(5 to "5 min", 10 to "10 min", 15 to "15 min", 30 to "30 min", 60 to "1 ora", 90 to "1h 30m")
    Dialog(onDismissRequest = onDismiss) {
        Column(Modifier.fillMaxWidth().clip(RoundedCornerShape(24.dp)).background(Bg2).padding(24.dp)) {
            Text("\u23FE  Sleep Timer", color = TextPrimary, fontWeight = FontWeight.Bold, fontSize = 18.sp)
            Spacer(Modifier.height(6.dp))
            Text("La musica si fermer\u00E0 automaticamente", color = TextSecondary, fontSize = 13.sp)
            Spacer(Modifier.height(16.dp))
            opts.forEach { (m, l) ->
                Row(
                    modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(12.dp)).clickable { onSet(m) }
                        .padding(horizontal = 16.dp, vertical = 14.dp),
                    horizontalArrangement = Arrangement.SpaceBetween,
                    verticalAlignment = Alignment.CenterVertically
                ) {
                    Text(l, color = TextPrimary, fontSize = 15.sp, fontWeight = FontWeight.Medium)
                    Icon(Icons.Default.ArrowForwardIos, null, Modifier.size(14.dp), TextTertiary)
                }
                HorizontalDivider(color = Border.copy(alpha = 0.5f), thickness = 0.5.dp,
                    modifier = Modifier.padding(horizontal = 16.dp))
            }
            Spacer(Modifier.height(8.dp))
            TextButton(onDismiss, Modifier.align(Alignment.CenterHorizontally)) {
                Text("Annulla", color = TextSecondary, fontSize = 14.sp)
            }
        }
    }
}

@Composable
private fun SmallIconBtn(onClick: () -> Unit, tint: Color, content: @Composable () -> Unit) {
    IconButton(onClick, Modifier.size(36.dp)) {
        CompositionLocalProvider(LocalContentColor provides tint) { content() }
    }
}

@Composable
private fun LosslessBars() {
    Row(Modifier.height(14.dp), verticalAlignment = Alignment.CenterVertically,
        horizontalArrangement = Arrangement.spacedBy(2.dp)) {
        listOf(0.4f, 0.8f, 0.6f, 1f, 0.7f).forEach { h ->
            Box(Modifier.width(2.dp).fillMaxHeight(h).clip(RoundedCornerShape(1.dp)).background(Purple.copy(alpha = 0.7f)))
        }
    }
}

fun formatDurationMs(ms: Long): String {
    val s = (ms / 1000).toInt()
    return "${s / 60}:${(s % 60).toString().padStart(2, '0')}"
}

@Composable
private fun LyricsDisplay(lyrics: List<LyricLine>, currentIdx: Int) {
    if (lyrics.isEmpty()) {
        Box(Modifier.fillMaxWidth().height(80.dp), contentAlignment = Alignment.Center) {
            Text("Nessun testo disponibile", color = TextTertiary, fontSize = 13.sp)
        }
        return
    }

    val visibleRange = 2
    val startIdx = (currentIdx - visibleRange).coerceAtLeast(0)
    val endIdx = (currentIdx + visibleRange).coerceAtMost(lyrics.size - 1)

    Column(
        Modifier.fillMaxWidth().padding(horizontal = 24.dp).heightIn(min = 60.dp),
        horizontalAlignment = Alignment.CenterHorizontally,
        verticalArrangement = Arrangement.Center
    ) {
        for (i in startIdx..endIdx) {
            val line = lyrics[i]
            val isCurrent = i == currentIdx
            val isPast = i < currentIdx

            val textColor by animateColorAsState(
                targetValue = when {
                    isCurrent -> Purple
                    isPast -> TextSecondary.copy(alpha = 0.5f)
                    else -> TextTertiary.copy(alpha = 0.4f)
                }
            )
            val textSize by animateFloatAsState(
                targetValue = if (isCurrent) 16f else 13f
            )

            AnimatedContent(
                targetState = line.text,
                transitionSpec = { fadeIn() togetherWith fadeOut() }
            ) { txt ->
                Text(
                    text = txt,
                    color = textColor,
                    fontSize = textSize.sp,
                    fontWeight = if (isCurrent) FontWeight.Bold else FontWeight.Normal,
                    maxLines = 1,
                    overflow = TextOverflow.Ellipsis,
                    textAlign = TextAlign.Center,
                    modifier = Modifier.padding(vertical = 2.dp)
                )
            }
        }
    }
}

package org.musicwavver.ui

import androidx.compose.animation.*
import androidx.compose.animation.core.*
import androidx.compose.animation.core.animate
import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectVerticalDragGestures
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBackIosNew
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.input.pointer.util.VelocityTracker
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import kotlinx.coroutines.launch
import org.musicwavver.model.Track
import org.musicwavver.ui.theme.*
import kotlin.math.roundToInt

@Composable
fun PlaylistScreen(
    state: PlaylistViewState,
    currentTrackId: Long?,
    favorites: Set<Long>,
    onTrackClick: (Track) -> Unit,
    onFavClick: (Track) -> Unit,
    onClose: () -> Unit
) {
    val visible = state != PlaylistViewState.Hidden

    AnimatedVisibility(
        visible = visible,
        enter = slideInVertically(initialOffsetY = { it }),
        exit  = slideOutVertically(targetOffsetY = { it })
    ) {
        DraggableSheet(onClose = onClose) {
            when (state) {
                is PlaylistViewState.Loading -> Box(Modifier.fillMaxSize(), Alignment.Center) {
                    CircularProgressIndicator(color = Purple, strokeWidth = 3.dp)
                }
                is PlaylistViewState.Ready  -> PlaylistContent(state, currentTrackId, favorites, onTrackClick, onFavClick, onClose)
                else -> {}
            }
        }
    }
}

@Composable
private fun PlaylistContent(
    state: PlaylistViewState.Ready,
    currentTrackId: Long?,
    favorites: Set<Long>,
    onTrackClick: (Track) -> Unit,
    onFavClick: (Track) -> Unit,
    onClose: () -> Unit
) {
    Column(modifier = Modifier.fillMaxSize().background(Bg)) {
        Box(
            modifier = Modifier.fillMaxWidth()
                .background(Brush.verticalGradient(listOf(Bg2, Bg), 0f, 120f))
                .statusBarsPadding()
                .padding(horizontal = 16.dp, vertical = 12.dp)
        ) {
            IconButton(onClick = onClose, modifier = Modifier.align(Alignment.CenterStart)) {
                Icon(Icons.Default.ArrowBackIosNew, "Indietro", tint = TextSecondary, modifier = Modifier.size(20.dp))
            }
            Column(modifier = Modifier.align(Alignment.Center), horizontalAlignment = Alignment.CenterHorizontally) {
                Text(state.emoji, fontSize = 22.sp)
                Text(state.title, color = TextPrimary, fontWeight = FontWeight.Bold,
                    fontSize = 18.sp, letterSpacing = (-0.3).sp)
                Text("${state.tracks.size} brani", color = TextTertiary, fontSize = 12.sp)
            }
        }
        HorizontalDivider(color = Border, thickness = 0.5.dp)

        if (state.tracks.isEmpty()) {
            Box(Modifier.fillMaxSize(), Alignment.Center) {
                Text("Nessun brano disponibile", color = TextTertiary, fontSize = 14.sp, textAlign = TextAlign.Center)
            }
        } else {
            LazyColumn(
                contentPadding = PaddingValues(start = 12.dp, top = 8.dp, end = 12.dp, bottom = 130.dp),
                verticalArrangement = Arrangement.spacedBy(6.dp)
            ) {
                itemsIndexed(state.tracks, key = { _, t -> t.id }) { _, track ->
                    TrackCard(
                        track = track,
                        isFav = favorites.contains(track.id),
                        isNowPlaying = track.id == currentTrackId,
                        isResolving  = false,
                        onClick      = { onTrackClick(track) },
                        onFavClick   = { onFavClick(track) }
                    )
                }
            }
        }
    }
}

@Composable
fun DraggableSheet(
    onClose: () -> Unit,
    closePxThreshold: Float = 80f,
    closeVelocityThreshold: Float = 400f,
    content: @Composable BoxScope.() -> Unit
) {
    var offsetY by remember { mutableFloatStateOf(0f) }
    val scope = rememberCoroutineScope()
    val vt = remember { VelocityTracker() }

    Box(
        modifier = Modifier
            .fillMaxSize()
            .graphicsLayer {
                translationY = offsetY
                val progress = (offsetY / 500f).coerceIn(0f, 1f)
                alpha = 1f - progress * 0.5f
                scaleX = 1f - progress * 0.08f
                scaleY = 1f - progress * 0.08f
            }
            .pointerInput(Unit) {
                detectVerticalDragGestures(
                    onDragStart = { vt.resetTracking() },
                    onDragEnd = {
                        val vel = vt.calculateVelocity().y
                        if (offsetY > closePxThreshold || vel > closeVelocityThreshold) {
                            onClose()
                            offsetY = 0f
                        } else {
                            scope.launch {
                                animate(offsetY, 0f, animationSpec = spring(stiffness = Spring.StiffnessMediumLow)) { v, _ -> offsetY = v }
                            }
                        }
                    },
                    onVerticalDrag = { change, delta ->
                        vt.addPosition(change.uptimeMillis, change.position)
                        if (delta > 0) offsetY = (offsetY + delta).coerceAtLeast(0f)
                        change.consume()
                    }
                )
            },
        content = content
    )
}

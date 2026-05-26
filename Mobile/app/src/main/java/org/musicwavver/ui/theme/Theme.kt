package org.musicwavver.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.mutableStateOf
import androidx.compose.ui.graphics.Color

data class AppColors(
    val Bg: Color, val Bg2: Color, val Bg3: Color,
    val TextPrimary: Color, val TextSecondary: Color, val TextTertiary: Color,
    val Surface1: Color, val Surface2: Color, val Surface3: Color,
    val Border: Color, val BorderHover: Color,
)

// ── Palettes ──────────────────────────────────
private val darkColors = AppColors(
    Bg = Color(0xFF080810), Bg2 = Color(0xFF0F0F1A), Bg3 = Color(0xFF16162A),
    TextPrimary = Color(0xFFF0F0FA), TextSecondary = Color(0x70F0F0FA), TextTertiary = Color(0x50F0F0FA),
    Surface1 = Color(0x0AFFFFFF), Surface2 = Color(0x12FFFFFF), Surface3 = Color(0x1EFFFFFF),
    Border = Color(0x12FFFFFF), BorderHover = Color(0x28FFFFFF),
)

private val lightColors = AppColors(
    Bg = Color(0xFFF8F8FF), Bg2 = Color(0xFFF0F0FA), Bg3 = Color(0xFFE8E8F2),
    TextPrimary = Color(0xFF0A0A14), TextSecondary = Color(0x700A0A14), TextTertiary = Color(0x500A0A14),
    Surface1 = Color(0x0A000000), Surface2 = Color(0x12000000), Surface3 = Color(0x1E000000),
    Border = Color(0x12000000), BorderHover = Color(0x28000000),
)

val ActiveColors = mutableStateOf(darkColors)

// Convenience getters — read from the mutable state; Compose tracks them automatically
val Bg: Color get() = ActiveColors.value.Bg
val Bg2: Color get() = ActiveColors.value.Bg2
val Bg3: Color get() = ActiveColors.value.Bg3
val TextPrimary: Color get() = ActiveColors.value.TextPrimary
val TextSecondary: Color get() = ActiveColors.value.TextSecondary
val TextTertiary: Color get() = ActiveColors.value.TextTertiary
val Surface1: Color get() = ActiveColors.value.Surface1
val Surface2: Color get() = ActiveColors.value.Surface2
val Surface3: Color get() = ActiveColors.value.Surface3
val Border: Color get() = ActiveColors.value.Border
val BorderHover: Color get() = ActiveColors.value.BorderHover

// ── Shared Accents ────────────────────────────
val Purple    = Color(0xFF7C3AED)
val PurpleMid = Color(0xFF6D28D9)
val PurpleDim = Color(0x1F7C3AED)
val PurpleGlow= Color(0x407C3AED)
val Magenta   = Color(0xFFD946EF)
val MagentaDim= Color(0x1FD946EF)
val MagentaGlow= Color(0x40D946EF)
val Coral     = Color(0xFFE05D5D)
val CoralDim  = Color(0x1FE05D5D)
val Green     = Color(0xFF4ADE80)
val Red       = Color(0xFFEF4444)
val GradStart = PurpleMid
val GradMid   = Color(0xFF9333EA)
val GradEnd   = Magenta

// Static overlays (always dark-based)
val BgAlpha96 = Color(0xF5080810)
val BgAlpha97 = Color(0xF7080810)
val BgAlpha55 = Color(0x8C080810)
val BgAlpha50 = Color(0x80080810)
val BgAlpha60 = Color(0x99080810)

private val DarkScheme = darkColorScheme(
    primary = Purple, secondary = Coral,
    background = Color(0xFF080810), surface = Color(0x0AFFFFFF), surfaceVariant = Color(0x12FFFFFF),
    onPrimary = Color(0xFF0A0714), onSecondary = Color(0xFF0A0714),
    onBackground = Color(0xFFF0F0FA), onSurface = Color(0xFFF0F0FA),
    outline = Color(0x12FFFFFF), outlineVariant = Color(0x28FFFFFF),
)

private val LightScheme = lightColorScheme(
    primary = Purple, secondary = Coral,
    background = Color(0xFFF8F8FF), surface = Color(0xFFF0F0FA), surfaceVariant = Color(0xFFE8E8F2),
    onPrimary = Color.White, onSecondary = Color.White,
    onBackground = Color(0xFF0A0A14), onSurface = Color(0xFF0A0A14),
    outline = Color(0x12000000), outlineVariant = Color(0x28000000),
)

@Composable
fun MusicWavverTheme(darkMode: Boolean = true, content: @Composable () -> Unit) {
    ActiveColors.value = if (darkMode) darkColors else lightColors
    MaterialTheme(
        colorScheme = if (darkMode) DarkScheme else LightScheme,
        content = content
    )
}

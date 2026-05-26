package org.musicwavver.player

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.media.AudioManager
import android.net.Uri
import android.os.Binder
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import androidx.media.app.NotificationCompat.MediaStyle
import androidx.media3.common.*
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.session.MediaSession
import org.musicwavver.MainActivity
import org.musicwavver.MusicWavverApp
import androidx.media3.exoplayer.source.DefaultMediaSourceFactory

class PlaybackService : Service() {

    companion object {
        const val CHANNEL_ID = "music_wavver_playback"
        const val NOTIFICATION_ID = 1
        const val ACTION_PLAY = "org.musicwavver.action.PLAY"
        const val ACTION_PAUSE = "org.musicwavver.action.PAUSE"
        const val ACTION_TOGGLE = "org.musicwavver.action.TOGGLE"
        const val ACTION_NEXT = "org.musicwavver.action.NEXT"
        const val ACTION_PREV = "org.musicwavver.action.PREV"
        const val ACTION_STOP = "org.musicwavver.action.STOP"
    }

    inner class LocalBinder : Binder() {
        fun getService(): PlaybackService = this@PlaybackService
    }

    private val binder = LocalBinder()
    private lateinit var player: ExoPlayer
    private lateinit var mediaSession: MediaSession
    private lateinit var audioManager: AudioManager

    private var audioFocusRequest: Any? = null
    private val becomingNoisyReceiver = BecomingNoisyReceiver()

    var onPlayStateChanged: ((Boolean) -> Unit)? = null
    var onTrackEnded: (() -> Unit)? = null

    private val audioFocusChangeListener = AudioManager.OnAudioFocusChangeListener { focusChange ->
        when (focusChange) {
            AudioManager.AUDIOFOCUS_LOSS -> pause()
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT -> pause()
            AudioManager.AUDIOFOCUS_LOSS_TRANSIENT_CAN_DUCK -> player.volume = 0.2f
            AudioManager.AUDIOFOCUS_GAIN -> player.volume = 1.0f
        }
    }

    private inner class BecomingNoisyReceiver : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            if (intent.action == AudioManager.ACTION_AUDIO_BECOMING_NOISY && player.isPlaying) {
                pause()
            }
        }
    }

    override fun onCreate() {
        super.onCreate()
        createNotificationChannel()
        audioManager = getSystemService(AUDIO_SERVICE) as AudioManager

        val app = application as MusicWavverApp
        player = ExoPlayer.Builder(this)
            .setMediaSourceFactory(DefaultMediaSourceFactory(app.cacheDataSourceFactory))
            .build()

        mediaSession = MediaSession.Builder(this, player).build()

        player.addListener(object : Player.Listener {
            override fun onIsPlayingChanged(isPlaying: Boolean) {
                onPlayStateChanged?.invoke(isPlaying)
                try { startForeground(NOTIFICATION_ID, buildNotification()) } catch (_: Exception) { }
            }

            override fun onMediaItemTransition(mediaItem: MediaItem?, reason: Int) {
                if (reason == Player.MEDIA_ITEM_TRANSITION_REASON_AUTO) {
                    onTrackEnded?.invoke()
                }
            }
        })

        registerReceiver(becomingNoisyReceiver, IntentFilter(AudioManager.ACTION_AUDIO_BECOMING_NOISY))
    }

    override fun onBind(intent: Intent?): IBinder = binder

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        when (intent?.action) {
            ACTION_TOGGLE -> togglePlay()
            ACTION_PLAY -> { if (!player.isPlaying && player.mediaItemCount > 0 && requestAudioFocus()) player.play() }
            ACTION_PAUSE -> pause()
            ACTION_NEXT -> { player.stop(); onTrackEnded?.invoke() }
            ACTION_PREV -> { player.stop(); onTrackEnded?.invoke() }
            ACTION_STOP -> {
                player.stop()
                if (Build.VERSION.SDK_INT >= 33) {
                    stopForeground(STOP_FOREGROUND_REMOVE)
                } else {
                    @Suppress("DEPRECATION")
                    stopForeground(true)
                }
                stopSelf()
            }
            else -> {
                startForeground(NOTIFICATION_ID, idleNotification())
            }
        }
        return START_STICKY
    }

    private fun requestAudioFocus(): Boolean {
        return if (Build.VERSION.SDK_INT >= 26) {
            requestAudioFocus26()
        } else {
            @Suppress("DEPRECATION")
            audioManager.requestAudioFocus(audioFocusChangeListener,
                AudioManager.STREAM_MUSIC, AudioManager.AUDIOFOCUS_GAIN) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
        }
    }

    @android.annotation.TargetApi(26)
    private fun requestAudioFocus26(): Boolean {
        var req = audioFocusRequest as? android.media.AudioFocusRequest
        if (req == null) {
            req = android.media.AudioFocusRequest.Builder(android.media.AudioManager.AUDIOFOCUS_GAIN)
                .setAudioAttributes(android.media.AudioAttributes.Builder()
                    .setUsage(android.media.AudioAttributes.USAGE_MEDIA)
                    .setContentType(android.media.AudioAttributes.CONTENT_TYPE_MUSIC)
                    .build())
                .setOnAudioFocusChangeListener(audioFocusChangeListener)
                .build()
            audioFocusRequest = req
        }
        return audioManager.requestAudioFocus(req) == AudioManager.AUDIOFOCUS_REQUEST_GRANTED
    }

    private fun abandonAudioFocus() {
        if (Build.VERSION.SDK_INT >= 26) {
            val req = audioFocusRequest as? android.media.AudioFocusRequest ?: return
            audioManager.abandonAudioFocusRequest(req)
        } else {
            @Suppress("DEPRECATION")
            audioManager.abandonAudioFocus(audioFocusChangeListener)
        }
    }

    fun play(url: String, title: String, artist: String, artUrl: String?) {
        if (!requestAudioFocus()) return
        val metadata = MediaMetadata.Builder()
            .setTitle(title)
            .setArtist(artist)
            .apply {
                if (!artUrl.isNullOrBlank()) setArtworkUri(Uri.parse(artUrl))
            }
            .build()

        player.stop()
        player.clearMediaItems()
        player.setMediaItem(MediaItem.Builder().setUri(url).setMediaMetadata(metadata).build())
        player.prepare()
        player.play()

        try { startForeground(NOTIFICATION_ID, buildNotification()) } catch (_: Exception) { }
    }

    fun togglePlay() {
        if (player.isPlaying) {
            player.pause()
            abandonAudioFocus()
        } else {
            if (requestAudioFocus()) player.play()
        }
    }

    fun pause() {
        if (player.isPlaying) player.pause()
        abandonAudioFocus()
    }

    val isPlaying: Boolean get() = player.isPlaying
    val currentPosition: Long get() = player.currentPosition
    val duration: Long get() = player.duration
    val audioSessionId: Int get() = player.audioSessionId

    fun seekTo(positionMs: Long) { player.seekTo(positionMs) }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= 26) {
            val channel = android.app.NotificationChannel(
                CHANNEL_ID,
                "Playback",
                android.app.NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "Music playback controls"
                setShowBadge(false)
            }
            val manager = getSystemService(android.app.NotificationManager::class.java)
            manager.createNotificationChannel(channel)
        }
    }

    private fun idleNotification(): Notification = NotificationCompat.Builder(this, CHANNEL_ID).apply {
        setSmallIcon(android.R.drawable.ic_media_play)
        setContentTitle("Music Wavver")
        setContentText("Ready to play")
        setContentIntent(PendingIntent.getActivity(this@PlaybackService, 0,
            Intent(this@PlaybackService, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }, PendingIntent.FLAG_IMMUTABLE))
        setOngoing(true)
        if (Build.VERSION.SDK_INT >= 26) setSilent(true)
        setStyle(MediaStyle().setMediaSession(mediaSession.sessionCompatToken))
    }.build()

    private fun buildNotification(): Notification {
        val meta = player.mediaMetadata
        val title = meta.title?.toString() ?: "Music Wavver"
        val artist = meta.artist?.toString() ?: ""

        return NotificationCompat.Builder(this, CHANNEL_ID).apply {
            setSmallIcon(android.R.drawable.ic_media_play)
            setContentTitle(title)
            setContentText(artist)
            setContentIntent(PendingIntent.getActivity(this@PlaybackService, 0,
                Intent(this@PlaybackService, MainActivity::class.java).apply {
                    flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
                }, PendingIntent.FLAG_IMMUTABLE))
            setVisibility(NotificationCompat.VISIBILITY_PUBLIC)
            setOngoing(player.isPlaying)
            if (Build.VERSION.SDK_INT >= 26) setSilent(true)

            addAction(android.R.drawable.ic_media_previous, "Previous",
                PendingIntent.getService(this@PlaybackService, 1,
                    Intent(this@PlaybackService, PlaybackService::class.java).setAction(ACTION_PREV),
                    PendingIntent.FLAG_IMMUTABLE))

            val playAction = if (player.isPlaying) {
                Pair(android.R.drawable.ic_media_pause, "Pause")
            } else {
                Pair(android.R.drawable.ic_media_play, "Play")
            }
            addAction(playAction.first, playAction.second,
                PendingIntent.getService(this@PlaybackService, 2,
                    Intent(this@PlaybackService, PlaybackService::class.java)
                        .setAction(if (player.isPlaying) ACTION_PAUSE else ACTION_PLAY),
                    PendingIntent.FLAG_IMMUTABLE))

            addAction(android.R.drawable.ic_media_next, "Next",
                PendingIntent.getService(this@PlaybackService, 3,
                    Intent(this@PlaybackService, PlaybackService::class.java).setAction(ACTION_NEXT),
                    PendingIntent.FLAG_IMMUTABLE))

            setStyle(MediaStyle()
                .setMediaSession(mediaSession.sessionCompatToken)
                .setShowActionsInCompactView(0, 1, 2))

            setDeleteIntent(PendingIntent.getService(this@PlaybackService, 4,
                Intent(this@PlaybackService, PlaybackService::class.java).setAction(ACTION_STOP),
                PendingIntent.FLAG_IMMUTABLE))
        }.build()
    }

    override fun onDestroy() {
        abandonAudioFocus()
        unregisterReceiver(becomingNoisyReceiver)
        mediaSession.release()
        player.release()
        super.onDestroy()
    }
}

package org.musicwavver

import android.app.Application
import android.content.ComponentCallbacks2
import android.app.NotificationChannel
import android.app.NotificationManager
import androidx.media3.common.util.UnstableApi
import androidx.media3.database.StandaloneDatabaseProvider
import androidx.media3.datasource.cache.CacheDataSource
import androidx.media3.datasource.cache.LeastRecentlyUsedCacheEvictor
import androidx.media3.datasource.cache.SimpleCache
import coil.Coil
import coil.ImageLoader
import coil.disk.DiskCache
import coil.memory.MemoryCache
import org.musicwavver.data.FavoritesRepository
import org.musicwavver.data.PersistenceManager
import org.musicwavver.player.PlaybackService
import java.io.File

class MusicWavverApp : Application() {
    lateinit var persistence: PersistenceManager
        private set
    lateinit var favoritesRepository: FavoritesRepository
        private set
    lateinit var playCache: SimpleCache
        private set
    lateinit var cacheDataSourceFactory: CacheDataSource.Factory
        private set

    override fun onCreate() {
        super.onCreate()
        persistence = PersistenceManager(this)
        favoritesRepository = FavoritesRepository(this)
        createNotificationChannel()

        val dbProvider = StandaloneDatabaseProvider(this)
        playCache = SimpleCache(
            File(cacheDir, "exoplayer_cache"),
            LeastRecentlyUsedCacheEvictor(200L * 1024 * 1024), // 200 MB
            dbProvider
        )
        cacheDataSourceFactory = CacheDataSource.Factory()
            .setCache(playCache)
            .setUpstreamDataSourceFactory(androidx.media3.datasource.DefaultHttpDataSource.Factory())

        val imageLoader = ImageLoader.Builder(this)
            .memoryCache(MemoryCache.Builder(this).maxSizePercent(0.25).build())
            .diskCache(DiskCache.Builder().directory(cacheDir.resolve("coil")).maxSizeBytes(150_000_000).build())
            .crossfade(true)
            .build()
        Coil.setImageLoader(imageLoader)
    }

    override fun onTrimMemory(level: Int) {
        super.onTrimMemory(level)
        if (level >= ComponentCallbacks2.TRIM_MEMORY_MODERATE) playCache.release()
    }

    private fun createNotificationChannel() {
        val channel = NotificationChannel(
            PlaybackService.CHANNEL_ID,
            "Playback",
            NotificationManager.IMPORTANCE_LOW
        ).apply {
            description = "Music playback controls"
            setShowBadge(false)
        }
        val nm = getSystemService(NotificationManager::class.java)
        nm.createNotificationChannel(channel)
    }
}

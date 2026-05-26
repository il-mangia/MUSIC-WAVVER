package org.musicwavver.player

import android.content.ContentValues
import android.content.Context
import android.os.Build
import android.os.Environment
import android.provider.MediaStore
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

object MediaStoreFileManager {

    suspend fun saveMp3(
        context: Context,
        source: File,
        title: String,
        artist: String,
        album: String?
    ): Result<File> = withContext(Dispatchers.IO) {
        try {
            val fileName = "${artist} - ${title}.mp3"
            val relativePath = "Music/MusicWavver"

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.Q) {
                val values = ContentValues().apply {
                    put(MediaStore.Audio.Media.DISPLAY_NAME, fileName)
                    put(MediaStore.Audio.Media.ARTIST, artist)
                    put(MediaStore.Audio.Media.TITLE, title)
                    put(MediaStore.Audio.Media.MIME_TYPE, "audio/mpeg")
                    put(MediaStore.Audio.Media.RELATIVE_PATH, relativePath)
                    album?.let { put(MediaStore.Audio.Media.ALBUM, it) }
                    put(MediaStore.Audio.Media.IS_MUSIC, 1)
                }
                val uri = context.contentResolver.insert(
                    MediaStore.Audio.Media.EXTERNAL_CONTENT_URI, values
                ) ?: throw Exception("Failed to create MediaStore entry")

                context.contentResolver.openOutputStream(uri)?.use { os ->
                    source.inputStream().use { input -> input.copyTo(os) }
                } ?: throw Exception("Failed to open output stream")
                Result.success(File(source.absolutePath))
            } else {
                val musicDir = Environment.getExternalStoragePublicDirectory(Environment.DIRECTORY_MUSIC)
                val targetDir = File(musicDir, "MusicWavver")
                targetDir.mkdirs()
                val target = File(targetDir, fileName)
                source.inputStream().use { input -> target.outputStream().use { output -> input.copyTo(output) } }
                Result.success(target)
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

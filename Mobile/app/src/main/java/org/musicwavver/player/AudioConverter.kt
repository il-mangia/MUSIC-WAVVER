package org.musicwavver.player

import com.antonkarpenko.ffmpegkit.FFmpegKit
import com.antonkarpenko.ffmpegkit.ReturnCode
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import java.io.File

object AudioConverter {

    suspend fun flacToMp3(
        input: File,
        output: File,
        title: String,
        artist: String,
        album: String?,
        genre: String?,
        year: Int?,
        coverArt: File?
    ): Result<File> = withContext(Dispatchers.IO) {
        try {
            val args = mutableListOf(
                "-i", input.absolutePath,
                "-vn",
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "320k",
                "-id3v2_version", "3",
                "-metadata", "title=$title",
                "-metadata", "artist=$artist",
                "-y",
                output.absolutePath
            )
            if (album != null) { args.add("-metadata"); args.add("album=$album") }
            if (genre != null) { args.add("-metadata"); args.add("genre=$genre") }
            if (year != null) { args.add("-metadata"); args.add("date=$year") }

            if (coverArt != null && coverArt.exists()) {
                args.addAll(listOf("-i", coverArt.absolutePath, "-map", "0:a", "-map", "1:0", "-disposition:v", "attached_pic"))
            }

            val session = FFmpegKit.executeWithArguments(args.toTypedArray())
            val rc = session.returnCode

            if (ReturnCode.isSuccess(rc)) {
                Result.success(output)
            } else {
                Result.failure(Exception("FFmpeg error: ${session.failStackTrace ?: rc}"))
            }
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
}

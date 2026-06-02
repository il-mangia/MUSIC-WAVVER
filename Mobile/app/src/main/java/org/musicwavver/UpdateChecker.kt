package org.musicwavver

import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject

object UpdateChecker {

    private const val CURRENT_VERSION = "6.6"
    private const val URL =
        "https://api.github.com/repos/il-mangia/MUSIC-WAVVER/releases/latest"

    private val client = OkHttpClient()

    fun checkForUpdate(onResult: (String?) -> Unit) {
        Thread {
            try {
                val request = Request.Builder()
                    .url(URL)
                    .header("User-Agent", "MUSIC-WAVVER")
                    .build()

                val response = client.newCall(request).execute()
                val body = response.body?.string()

                if (body != null) {
                    val json = JSONObject(body)
                    val latestVersion = json.getString("tag_name")

                    if (latestVersion != CURRENT_VERSION) {
                        onResult(latestVersion)
                    } else {
                        onResult(null)
                    }
                } else {
                    onResult(null)
                }
            } catch (e: Exception) {
                e.printStackTrace()
                onResult(null)
            }
        }.start()
    }
}

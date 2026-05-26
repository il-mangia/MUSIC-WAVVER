package org.musicwavver.network

object SpotifyConfig {
    var clientId = ""
    var clientSecret = ""
    val isConfigured get() = clientId.isNotBlank() && clientSecret.isNotBlank()

    fun isConfiguredWith(id: String, secret: String) = id.isNotBlank() && secret.isNotBlank()
}

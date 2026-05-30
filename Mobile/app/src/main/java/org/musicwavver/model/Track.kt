package org.musicwavver.model

import com.google.gson.annotations.SerializedName

data class Track(
    val id: Long,
    val title: String,
    val artist: Artist,
    val album: Album,
    val duration: Int = 0,
    val type: String = "track"
)

data class Artist(
    val id: Long = 0,
    val name: String
)

data class Album(
    val title: String,
    val cover: String? = null,
    @SerializedName("cover_small")  val coverSmall: String? = null,
    @SerializedName("cover_medium") val coverMedium: String? = null,
    @SerializedName("cover_big")    val coverBig: String? = null,
    @SerializedName("cover_xl")     val coverXl: String? = null,
    val image: QobuzImage? = null
) {
    val bestCover: String? get() = image?.large ?: coverXl ?: coverBig ?: coverMedium ?: cover
}

data class QobuzImage(
    val small: String?,
    val thumbnail: String?,
    val large: String?
)

data class DeezerSearchResponse(val data: List<Track>?)
data class DeezerTrackResponse(val id: Long, val isrc: String?)

data class DeezerPlaylist(
    val id: Long,
    val title: String,
    @SerializedName("picture_medium") val pictureMedium: String?,
    @SerializedName("picture_xl")     val pictureXl: String?,
    @SerializedName("nb_tracks")      val nbTracks: Int = 0
)

data class PlaylistTracksResponse(val data: List<Track>?)
data class PlaylistsResponse(val data: List<DeezerPlaylist>?)

data class EditorialChartResponse(
    val tracks: TrackListWrapper?,
    val playlists: PlaylistListWrapper?
)
data class TrackListWrapper(val data: List<Track>?)
data class PlaylistListWrapper(val data: List<DeezerPlaylist>?)

data class ArtistSearchItem(
    val id: Long,
    val name: String,
    @SerializedName("picture_medium") val pictureMedium: String?,
    @SerializedName("picture_xl")     val pictureXl: String?,
    @SerializedName("nb_fan")         val nbFan: Int = 0,
    val type: String = "artist"
)
data class ArtistSearchResponse(val data: List<ArtistSearchItem>?)
data class ArtistTopTracksResponse(val data: List<Track>?)

data class DeezerArtist(
    val id: Long,
    val name: String,
    @SerializedName("picture_xl") val pictureXl: String?,
    @SerializedName("picture_big") val pictureBig: String?,
    @SerializedName("nb_fan") val nbFan: Int = 0
)

data class DeezerArtistAlbum(
    val id: Long,
    val title: String,
    val cover: String?,
    @SerializedName("cover_medium") val coverMedium: String?,
    @SerializedName("cover_big") val coverBig: String?,
    @SerializedName("cover_xl") val coverXl: String?,
    @SerializedName("release_date") val releaseDate: String?,
    @SerializedName("nb_tracks") val nbTracks: Int = 0
) {
    val bestCover: String? get() = coverXl ?: coverBig ?: coverMedium ?: cover
}
data class DeezerArtistAlbumsResponse(val data: List<DeezerArtistAlbum>?)
data class AlbumTracksResponse(val data: List<Track>?)

data class AlbumSearchItem(
    val id: Long,
    val title: String,
    val artist: Artist,
    @SerializedName("cover_medium") val coverMedium: String?,
    @SerializedName("cover_big") val coverBig: String?,
    @SerializedName("nb_tracks") val nbTracks: Int = 0,
    val type: String = "album"
) {
    val bestCover: String? get() = coverBig ?: coverMedium
}
data class AlbumSearchResponse(val data: List<AlbumSearchItem>?)

data class MonoResponse(val success: Boolean, val data: MonoData? = null)
data class MonoData(val tracks: MonoDataTracks? = null)
data class MonoDataTracks(val items: List<MonoTrackItem>?)
data class MonoTrackItem(val id: String)
data class MonoDownloadResponse(val success: Boolean, val data: MonoDownloadData? = null)
data class MonoDownloadData(val url: String?)

data class UserPlaylist(val id: Long, val name: String, val trackIds: MutableSet<Long> = mutableSetOf())

data class LrcResponse(
    val trackName: String?,
    val artistName: String?,
    val syncedLyrics: String?,
    val plainLyrics: String?
)

data class LyricLine(
    val timeMs: Long,
    val text: String
)

// ── SPOTIFY ──────────────────────────────────────────────────
data class SpotifyTokenResponse(
    val access_token: String,
    val token_type: String,
    val expires_in: Int
)

data class SpotifyPlaylistTracksResponse(
    val items: List<SpotifyPlaylistTrackItem>
)

data class SpotifyPlaylistTrackItem(
    val track: SpotifyTrackItem
)

data class SpotifyTrackItem(
    val name: String,
    val artists: List<SpotifyArtistItem>,
    val external_ids: SpotifyExternalIds?
)

data class SpotifyArtistItem(
    val name: String
)

data class SpotifyExternalIds(
    val isrc: String?
)

// ── SEARCH ──────────────────────────────────────────────────
data class SearchHistoryItem(val query: String, val timestamp: Long)

data class DeezerPlaylistSearchResponse(val data: List<DeezerPlaylistSearchItem>?)

data class DeezerPlaylistSearchItem(
    val id: Long,
    val title: String,
    @SerializedName("picture_medium") val pictureMedium: String?,
    @SerializedName("picture_big") val pictureBig: String?,
    @SerializedName("nb_tracks") val nbTracks: Int = 0
) {
    val bestCover: String? get() = pictureBig ?: pictureMedium
}

sealed class SearchResult {
    data class TrackResult(val track: org.musicwavver.model.Track) : SearchResult()
    data class ArtistResult(val artist: ArtistSearchItem) : SearchResult()
    data class AlbumResult(val album: AlbumSearchItem) : SearchResult()
    data class PlaylistResult(val playlist: DeezerPlaylistSearchItem) : SearchResult()
}

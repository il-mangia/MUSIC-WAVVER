package org.musicwavver.network

import org.musicwavver.model.*
import org.musicwavver.model.LrcResponse
import retrofit2.http.*

interface DeezerApi {
    @GET("search")
    suspend fun search(@Query("q") q: String, @Query("limit") limit: Int = 50): DeezerSearchResponse

    @GET("search/album")
    suspend fun searchAlbums(@Query("q") q: String, @Query("limit") limit: Int = 20): AlbumSearchResponse

    @GET("search/artist")
    suspend fun searchArtists(@Query("q") q: String, @Query("limit") limit: Int = 20): ArtistSearchResponse

    @GET("track/{id}")
    suspend fun getTrack(@Path("id") id: Long): DeezerTrackResponse

    @GET("track/isrc:{isrc}")
    suspend fun getTrackByIsrc(@Path("isrc") isrc: String): Track

    @GET("chart/0/tracks")
    suspend fun getChartTracks(@Query("limit") limit: Int = 20): DeezerSearchResponse

    @GET("chart/0/playlists")
    suspend fun getChartPlaylists(@Query("limit") limit: Int = 8): PlaylistsResponse

    @GET("editorial/{genreId}/charts")
    suspend fun getGenreChart(@Path("genreId") genreId: Int): EditorialChartResponse

    @GET("playlist/{id}/tracks")
    suspend fun getPlaylistTracks(@Path("id") id: Long, @Query("limit") limit: Int = 50): PlaylistTracksResponse

    @GET("artist/{id}")
    suspend fun getArtist(@Path("id") id: Long): DeezerArtist

    @GET("artist/{id}/top")
    suspend fun getArtistTopTracks(@Path("id") id: Long, @Query("limit") limit: Int = 30): ArtistTopTracksResponse

    @GET("artist/{id}/albums")
    suspend fun getArtistAlbums(@Path("id") id: Long): DeezerArtistAlbumsResponse

    @GET("album/{id}/tracks")
    suspend fun getAlbumTracks(@Path("id") id: Long, @Query("limit") limit: Int = 50): AlbumTracksResponse
}

interface SpotifyApi {
    @GET("v1/playlists/{playlist_id}/tracks")
    suspend fun getPlaylistTracks(
        @Path("playlist_id") playlistId: String,
        @Header("Authorization") auth: String
    ): SpotifyPlaylistTracksResponse
}

interface MonoApi {
    @GET("get-music")
    suspend fun getMusic(@Query("q") isrc: String, @Query("offset") offset: Int = 0): MonoResponse

    @GET("download-music")
    suspend fun downloadMusic(@Query("track_id") trackId: String, @Query("quality") quality: Int = 6): MonoDownloadResponse
}

interface LrcApi {
    @GET("api/get")
    suspend fun getLyrics(
        @Query("track_name") track: String,
        @Query("artist_name") artist: String,
        @Query("album_name") album: String?,
        @Query("duration") duration: Int
    ): LrcResponse
}

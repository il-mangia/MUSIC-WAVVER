package org.musicwavver.data

import android.content.Context
import androidx.datastore.preferences.core.*
import androidx.datastore.preferences.preferencesDataStore
import com.google.gson.Gson
import com.google.gson.JsonSyntaxException
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import org.musicwavver.model.SearchHistoryItem
import org.musicwavver.model.Track
import org.musicwavver.model.UserPlaylist

val Context.appDataStore by preferencesDataStore(name = "music_wavver")

class PersistenceManager(private val context: Context) {

    private val gson = Gson()

    companion object {
        private val KEY_SEARCH_HISTORY  = stringPreferencesKey("search_history")
        private val KEY_RECENTLY_PLAYED = stringPreferencesKey("recently_played")
        private val KEY_USER_PLAYLISTS  = stringPreferencesKey("user_playlists")
        private val KEY_IS_DARK_MODE    = booleanPreferencesKey("is_dark_mode")
    }

    // ── Search History ──────────────────────────────────────────
    fun searchHistory(): Flow<List<SearchHistoryItem>> =
        context.appDataStore.data.map { prefs ->
            val raw = prefs[KEY_SEARCH_HISTORY]
            if (raw.isNullOrBlank()) return@map emptyList()
            try {
                gson.fromJson(raw, object : TypeToken<List<SearchHistoryItem>>() {}.type)
            } catch (_: JsonSyntaxException) {
                // migrate from old List<String> format
                val old: List<String> = try {
                    gson.fromJson(raw, object : TypeToken<List<String>>() {}.type)
                } catch (_: Exception) { emptyList() }
                old.map { SearchHistoryItem(it, System.currentTimeMillis()) }
            }
        }

    suspend fun saveSearchHistory(list: List<SearchHistoryItem>) {
        context.appDataStore.edit { it[KEY_SEARCH_HISTORY] = toJson(list) }
    }

    // ── Recently Played ─────────────────────────────────────────
    fun recentlyPlayed(): Flow<List<Track>> =
        context.appDataStore.data.map { prefs ->
            fromJson(prefs[KEY_RECENTLY_PLAYED], object : TypeToken<List<Track>>() {})
        }

    suspend fun saveRecentlyPlayed(list: List<Track>) {
        context.appDataStore.edit { it[KEY_RECENTLY_PLAYED] = toJson(list) }
    }

    // ── User Playlists ──────────────────────────────────────────
    fun userPlaylists(): Flow<List<UserPlaylist>> =
        context.appDataStore.data.map { prefs ->
            fromJson(prefs[KEY_USER_PLAYLISTS], object : TypeToken<List<UserPlaylist>>() {})
        }

    suspend fun saveUserPlaylists(list: List<UserPlaylist>) {
        context.appDataStore.edit { it[KEY_USER_PLAYLISTS] = toJson(list) }
    }

    // ── Dark Mode ───────────────────────────────────────────────
    fun isDarkMode(): Flow<Boolean> =
        context.appDataStore.data.map { prefs -> prefs[KEY_IS_DARK_MODE] ?: true }

    suspend fun saveDarkMode(v: Boolean) {
        context.appDataStore.edit { it[KEY_IS_DARK_MODE] = v }
    }

    // ── JSON helpers ────────────────────────────────────────────
    private inline fun <reified T> fromJson(raw: String?, type: TypeToken<T>): T =
        if (raw.isNullOrBlank()) gson.fromJson("[]", type.type)
        else try { gson.fromJson(raw, type.type) } catch (_: Exception) { gson.fromJson("[]", type.type) }

    private fun toJson(obj: Any): String = gson.toJson(obj)
}

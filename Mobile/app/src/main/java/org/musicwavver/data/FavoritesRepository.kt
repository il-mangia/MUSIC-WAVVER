package org.musicwavver.data

import android.content.Context
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.stringPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map

val Context.favDataStore by preferencesDataStore(name = "favorites")

data class FavoriteTrack(
    val deezerId: Long,
    val title: String,
    val artist: String,
    val album: String,
    val art: String?,
    val duration: Int = 0
)

class FavoritesRepository(private val context: Context) {

    private val gson = Gson()
    private val key = stringPreferencesKey("fav_list")

    fun getAll(): Flow<List<FavoriteTrack>> {
        return context.favDataStore.data.map { prefs ->
            val json = prefs[key] ?: return@map emptyList()
            val type = object : TypeToken<List<FavoriteTrack>>() {}.type
            gson.fromJson(json, type) ?: emptyList()
        }
    }

    suspend fun toggle(fav: FavoriteTrack) {
        context.favDataStore.edit { prefs ->
            val current = getAllFromJson(prefs[key])
            val updated = if (current.any { it.deezerId == fav.deezerId }) {
                current.filter { it.deezerId != fav.deezerId }
            } else {
                current + fav
            }
            prefs[key] = gson.toJson(updated)
        }
    }

    suspend fun isFavorite(deezerId: Long): Boolean {
        var result = false
        context.favDataStore.data.collect { prefs ->
            val list = getAllFromJson(prefs[key])
            result = list.any { it.deezerId == deezerId }
            return@collect
        }
        return result
    }

    private fun getAllFromJson(json: String?): List<FavoriteTrack> {
        if (json.isNullOrBlank()) return emptyList()
        val type = object : TypeToken<List<FavoriteTrack>>() {}.type
        return gson.fromJson(json, type) ?: emptyList()
    }
}

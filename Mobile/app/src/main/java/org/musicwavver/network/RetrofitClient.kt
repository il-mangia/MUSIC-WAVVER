package org.musicwavver.network

import okhttp3.FormBody
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.Request
import org.json.JSONObject
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

data class MonoApiConfig(val api: MonoApi, val quality: Int, val name: String)

object RetrofitClient {
    private val okHttp = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .writeTimeout(15, TimeUnit.SECONDS)
        .build()

    val deezerApi: DeezerApi by lazy {
        Retrofit.Builder()
            .baseUrl("https://api.deezer.com/")
            .client(okHttp)
            .addConverterFactory(GsonConverterFactory.create())
            .build().create(DeezerApi::class.java)
    }

    private val cookieInterceptor = Interceptor { chain ->
        val req = chain.request().newBuilder()
            .addHeader("Cookie", "captcha_verified_at=${System.currentTimeMillis()}")
            .build()
        chain.proceed(req)
    }

    private val okHttpWithCookie = okHttp.newBuilder()
        .addInterceptor(cookieInterceptor)
        .build()

    val monoInstances: List<MonoApiConfig> = listOf(
        MonoApiConfig(
            Retrofit.Builder().baseUrl("https://qobuz.squid.wtf/api/")
                .client(okHttpWithCookie)
                .addConverterFactory(GsonConverterFactory.create())
                .build().create(MonoApi::class.java),
            27, "squid.wtf"
        ),
        MonoApiConfig(
            Retrofit.Builder().baseUrl("https://qobuz.kennyy.com.br/api/")
                .client(okHttpWithCookie)
                .addConverterFactory(GsonConverterFactory.create())
                .build().create(MonoApi::class.java),
            27, "kennyy"
        ),
        MonoApiConfig(
            Retrofit.Builder().baseUrl("https://qdl-api.monochrome.tf/api/")
                .client(okHttp)
                .addConverterFactory(GsonConverterFactory.create())
                .build().create(MonoApi::class.java),
            6, "monochrome"
        )
    )

    val lrcApi: LrcApi by lazy {
        Retrofit.Builder()
            .baseUrl("https://lrclib.net/")
            .client(okHttp)
            .addConverterFactory(GsonConverterFactory.create())
            .build().create(LrcApi::class.java)
    }

    val spotifyApi: SpotifyApi by lazy {
        Retrofit.Builder()
            .baseUrl("https://api.spotify.com/")
            .client(okHttp)
            .addConverterFactory(GsonConverterFactory.create())
            .build().create(SpotifyApi::class.java)
    }

    private val tokenClient = OkHttpClient.Builder()
        .connectTimeout(15, TimeUnit.SECONDS)
        .readTimeout(15, TimeUnit.SECONDS)
        .build()

    fun getSpotifyToken(clientId: String, clientSecret: String): String {
        val body = FormBody.Builder()
            .add("grant_type", "client_credentials")
            .add("client_id", clientId)
            .add("client_secret", clientSecret)
            .build()
        val request = Request.Builder()
            .url("https://accounts.spotify.com/api/token")
            .post(body)
            .build()
        val response = tokenClient.newCall(request).execute()
        val json = JSONObject(response.body!!.string())
        return json.getString("access_token")
    }
}

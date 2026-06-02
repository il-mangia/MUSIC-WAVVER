package org.musicwavver.network

import android.annotation.SuppressLint
import android.view.ViewGroup
import android.webkit.JavascriptInterface
import android.webkit.WebChromeClient
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.viewinterop.AndroidView
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.receiveAsFlow

class YouTubePlayerHandle {
    private var webView: WebView? = null

    internal fun attach(wv: WebView) { webView = wv }

    fun loadVideo(videoId: String) { webView?.evaluateJavascript("player.loadVideoById('$videoId');", null) }
    fun play() { webView?.evaluateJavascript("player.playVideo();", null) }
    fun pause() { webView?.evaluateJavascript("player.pauseVideo();", null) }
    fun seekTo(seconds: Float) { webView?.evaluateJavascript("player.seekTo($seconds);", null) }
}

@SuppressLint("SetJavaScriptEnabled")
@Composable
fun YouTubePlayerView(
    modifier: Modifier = Modifier,
    handle: YouTubePlayerHandle = remember { YouTubePlayerHandle() }
): YouTubePlayerHandle {
    AndroidView(
        factory = { ctx ->
            WebView(ctx).apply {
                layoutParams = ViewGroup.LayoutParams(
                    ViewGroup.LayoutParams.MATCH_PARENT,
                    ViewGroup.LayoutParams.MATCH_PARENT
                )
                settings.javaScriptEnabled = true
                settings.domStorageEnabled = true
                settings.mediaPlaybackRequiresUserGesture = false
                webChromeClient = WebChromeClient()
                webViewClient = WebViewClient()
                addJavascriptInterface(object {
                    @JavascriptInterface
                    fun onReady() { }

                    @JavascriptInterface
                    fun onStateChange(state: Int) { }
                }, "AndroidBridge")
                loadDataWithBaseURL(
                    "https://www.youtube.com",
                    PLAYER_HTML, "text/html", "UTF-8", null
                )
                handle.attach(this)
            }
        },
        modifier = modifier
    )
    return handle
}

private const val PLAYER_HTML = """
<!DOCTYPE html><html><body style="margin:0;background:#000">
<div id="player"></div>
<script src="https://www.youtube.com/iframe_api"></script>
<script>
  var player;
  function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
      height:'100%', width:'100%',
      playerVars: { controls:1, autoplay:1, modestbranding:1, rel:0 },
      events: {
        'onReady': function() { AndroidBridge.onReady(); },
        'onStateChange': function(e) { AndroidBridge.onStateChange(e.data); }
      }
    });
  }
</script></body></html>
"""

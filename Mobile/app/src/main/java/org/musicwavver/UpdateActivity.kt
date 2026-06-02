package org.musicwavver

import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.activity.ComponentActivity

class UpdateActivity : ComponentActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_update)

        val version = intent.getStringExtra("version") ?: "?"

        findViewById<TextView>(R.id.title).text =
            "MUSIC WAVVER $version"

        findViewById<Button>(R.id.btnLater).setOnClickListener {
            finish()
        }

        findViewById<Button>(R.id.btnGithub).setOnClickListener {
            val intent = Intent(
                Intent.ACTION_VIEW,
                Uri.parse("https://github.com/il-mangia/MUSIC-WAVVER/releases/latest/")
            )
            startActivity(intent)
        }
    }
}

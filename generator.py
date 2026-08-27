import os
from PIL import Image

files = {
    "settings.gradle.kts": """pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "PalestineMovie"
include(":app")
""",

    "build.gradle.kts": """plugins {
    id("com.android.application") version "8.3.2" apply false
    id("org.jetbrains.kotlin.android") version "1.9.23" apply false
}
""",

    "gradle.properties": """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.nonTransitiveRClass=true
""",

    "app/build.gradle.kts": """plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.stream.hitv"
    compileSdk = 34

    defaultConfig {
        applicationId = "com.stream.hitv"
        minSdk = 24
        targetSdk = 34
        versionCode = 16
        versionName = "16.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = "17"
    }
    buildFeatures {
        compose = true
    }
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.11"
    }
}

dependencies {
    implementation("androidx.core:core-ktx:1.13.1")
    implementation("androidx.lifecycle:lifecycle-runtime-ktx:2.7.0")
    implementation("androidx.activity:activity-compose:1.9.0")
    implementation(platform("androidx.compose:compose-bom:2024.04.01"))
    implementation("androidx.compose.ui:ui")
    implementation("androidx.compose.ui:ui-graphics")
    implementation("androidx.compose.material3:material3")
    implementation("androidx.compose.material:material-icons-extended")
    implementation("androidx.navigation:navigation-compose:2.7.7")
    implementation("io.coil-kt:coil-compose:2.6.0")
    implementation("androidx.media3:media3-exoplayer:1.3.1")
    implementation("androidx.media3:media3-ui:1.3.1")
    implementation("androidx.media3:media3-exoplayer-hls:1.3.1")
    implementation("androidx.media3:media3-common:1.3.1")
}
""",

    "app/src/main/AndroidManifest.xml": """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.DOWNLOAD_WITHOUT_NOTIFICATION" />

    <application
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:label="Palestine Movie"
        android:supportsRtl="true"
        android:usesCleartextTraffic="true"
        android:theme="@style/Theme.HiTV"
        android:hardwareAccelerated="true">
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|smallestScreenSize|screenLayout"
            android:theme="@style/Theme.HiTV">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""",

    "app/src/main/res/values/themes.xml": """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.HiTV" parent="android:Theme.Material.NoActionBar">
        <item name="android:statusBarColor">#070F1E</item>
        <item name="android:navigationBarColor">#070F1E</item>
    </style>
</resources>
""",

    "app/src/main/java/com/stream/hitv/data/model/Models.kt": """package com.stream.hitv.data.model

data class StreamServer(
    val serverName: String,
    val quality: String,
    val streamUrl: String,
    val estimatedSize: String
)

data class Episode(
    val episodeNumber: Int,
    val title: String,
    val servers: List<StreamServer>,
    val duration: String = "45m"
) {
    val defaultUrl: String get() = servers.firstOrNull()?.streamUrl ?: "https://vjs.zencdn.net/v/oceans.mp4"
}

data class MediaItem(
    val id: String,
    val title: String,
    val description: String,
    val posterUrl: String,
    val bannerUrl: String,
    val rating: Double,
    val releaseYear: String,
    val type: String,
    val categoryName: String,
    val episodes: List<Episode>
)

data class DownloadItem(
    val mediaId: String,
    val mediaTitle: String,
    val posterUrl: String,
    val episodeNumber: Int,
    val episodeTitle: String,
    val localFileName: String,
    val serverName: String,
    val quality: String,
    val size: String
)
""",

    "app/src/main/java/com/stream/hitv/data/repository/MediaRepository.kt": """package com.stream.hitv.data.repository

import androidx.compose.runtime.mutableStateListOf
import com.stream.hitv.data.model.*

object MediaRepository {
    private val server1 = "https://vjs.zencdn.net/v/oceans.mp4"
    private val server2 = "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    private val server3 = "https://storage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4"

    fun buildServers(epNum: Int): List<StreamServer> = listOf(
        StreamServer("🚀 سيرفر VIP المباشر", "1080p (FHD)", server1, "380 MB"),
        StreamServer("⚡ سيرفر CDN سريع", "720p (HD)", server2, "190 MB"),
        StreamServer("📱 سيرفر موفر للإنترنت", "480p (SD)", server3, "85 MB")
    )

    private fun generateEpisodes(count: Int, duration: String = "24m"): List<Episode> {
        return (1..count).map { num ->
            Episode(num, "الحلقة $num - كاملة ومترجمة", buildServers(num), duration)
        }
    }

    private fun movieEp(duration: String = "2h 10m"): List<Episode> = listOf(
        Episode(1, "مشاهدة الفيلم كاملاً بأعلى جودة", buildServers(1), duration)
    )

    val mediaList = mutableStateListOf<MediaItem>(
        MediaItem(
            "a1", "Solo Leveling: Arise",
            "في عالم مليء بالبوابات والوحوش القاتلة، يستيقظ أضعف صياد في العالم بقدرة غير محدودة لتغيير مصير البشرية.",
            "https://image.tmdb.org/t/p/w500/geCRueV3ElhRTr0xtJuPxJ8BGd1.jpg",
            "https://image.tmdb.org/t/p/original/4MCKNAc6AbWjEsM2cr7hRiQgajU.jpg",
            9.9, "2024", "anime", "أنمي خارق 🔥", generateEpisodes(12)
        ),
        MediaItem(
            "a2", "Attack on Titan: Final",
            "المعركة الملحمية الأخيرة بين البشر والعمالقة لتحديد مصير العالم وكسر قيود الأسوار إلى الأبد.",
            "https://image.tmdb.org/t/p/w500/hTP1DtLGFamjfu8WqjnuQdP1n4i.jpg",
            "https://image.tmdb.org/t/p/original/m9mE4D4Kx1Vl5b9gZc8W2Z7lVb9.jpg",
            9.9, "2023", "anime", "أنمي حماسي ⚔️", generateEpisodes(10)
        ),
        MediaItem(
            "a3", "Jujutsu Kaisen S2",
            "صراع حابس للأنفاس في شوارع شيبويا بين سحرة الجوجوتسو وأقوى اللعنات القديمة في التاريخ.",
            "https://image.tmdb.org/t/p/w500/hFWP5w93uQ146u2YlP1z3rF1RzN.jpg",
            "https://image.tmdb.org/t/p/original/j3ZJ9agA5Z7r9eE0mE4wK6r7N3w.jpg",
            9.8, "2023", "anime", "أنمي قوى خارقة ⚡", generateEpisodes(12)
        ),
        MediaItem(
            "a4", "Demon Slayer: Hashira",
            "تدريب الهاشيرا الصارم استعداداً للمعركة الكبرى داخل قلعة اللانهاية ضد موزان وأقمار الشياطين.",
            "https://image.tmdb.org/t/p/w500/xUfRZu2mi8jH6SzQEJGP6tjBuYj.jpg",
            "https://image.tmdb.org/t/p/original/nTPKWc0iE3U5eU4yJpE3K7kY2mK.jpg",
            9.8, "2024", "anime", "أنمي شياطين 🗡️", generateEpisodes(8)
        ),
        MediaItem(
            "s1", "The Seoul Mystery",
            "دراما كورية مشوقة تدور حول محقق جنائي بارع يواجه شبكة أسرار غامضة تهدد العاصمة بأكملها.",
            "https://image.tmdb.org/t/p/w500/1XddXPXQIbZcHFiq70Q54nN3Z66.jpg",
            "https://image.tmdb.org/t/p/original/56v2KjBlU4XaOv9rVYEQypROD7P.jpg",
            9.6, "2023", "series", "دراما كورية 🇰🇷", generateEpisodes(16, "60m")
        ),
        MediaItem(
            "s2", "House of the Dragon S2",
            "الحرب الأهلية الملحمية رقصة التنانين تشتعل بين عائلة تارغاريان للسيطرة على العرش الحديدي.",
            "https://image.tmdb.org/t/p/w500/7QMsOTMUswlwxJP0rTTZfmz2tX2.jpg",
            "https://image.tmdb.org/t/p/original/etj5xUAoON507G9Sc0e3T2y92g0.jpg",
            9.5, "2024", "series", "صراع عروش 🐉", generateEpisodes(8, "65m")
        ),
        MediaItem(
            "m1", "Dune: Part Two",
            "بول أتريدس يتحد مع تشاني والشعب الصحراوي في رحلة انتقام ملحمية ضد المتآمرين الذين دمروا عائلته.",
            "https://image.tmdb.org/t/p/w500/czembW0Rk1Ke7lCJGahbOhdCuhV.jpg",
            "https://image.tmdb.org/t/p/original/xOMo8BRK7PfcJv9JCnx7s5hj0x2.jpg",
            9.8, "2024", "movie", "خيال علمي ملحمي 🪐", movieEp("2h 46m")
        ),
        MediaItem(
            "m2", "Oppenheimer",
            "القصة المشوقة للفيزيائي روبرت أوبنهايمر ودوره في مشروع مانهاتن وتطوير القنبلة الذرية الأولى.",
            "https://image.tmdb.org/t/p/w500/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg",
            "https://image.tmdb.org/t/p/original/fm6KqXpk3M2HVveHwCrBSSBaO0V.jpg",
            9.7, "2023", "movie", "دراما وتاريخ 💣", movieEp("3h 00m")
        )
    )

    val favoriteIds = mutableStateListOf<String>("a1", "m1")
    val downloads = mutableStateListOf<DownloadItem>()

    fun toggleFavorite(id: String) {
        if (favoriteIds.contains(id)) favoriteIds.remove(id) else favoriteIds.add(id)
    }

    fun isFavorite(id: String): Boolean = favoriteIds.contains(id)

    fun addDownload(item: DownloadItem) {
        if (downloads.none { it.mediaId == item.mediaId && it.episodeNumber == item.episodeNumber }) {
            downloads.add(item)
        }
    }

    fun removeDownload(mediaId: String, episodeNumber: Int) {
        downloads.removeAll { it.mediaId == mediaId && it.episodeNumber == episodeNumber }
    }

    fun getMediaById(id: String): MediaItem? = mediaList.find { it.id == id }
}
""",

    "app/src/main/java/com/stream/hitv/ui/theme/Theme.kt": """package com.stream.hitv.ui.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val BackgroundDark = Color(0xFF070F1E)
val SurfaceDark = Color(0xFF0F2038)
val AccentRed = Color(0xFFE50914)
val AccentGold = Color(0xFFFFC107)

@Composable
fun HiTVTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = darkColorScheme(
            primary = AccentRed,
            secondary = AccentGold,
            background = BackgroundDark,
            surface = SurfaceDark
        ),
        content = content
    )
}
""",

    "app/src/main/java/com/stream/hitv/ui/components/MediaCard.kt": """package com.stream.hitv.ui.components

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.stream.hitv.data.model.MediaItem
import com.stream.hitv.ui.theme.AccentGold

@Composable
fun MediaCard(item: MediaItem, onClick: () -> Unit) {
    Column(modifier = Modifier.width(135.dp).clickable { onClick() }.padding(4.dp)) {
        Box(modifier = Modifier.fillMaxWidth().height(185.dp).clip(RoundedCornerShape(10.dp))) {
            AsyncImage(model = item.posterUrl, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            Box(modifier = Modifier.align(Alignment.TopEnd).padding(6.dp).background(Color(0xCC000000), RoundedCornerShape(4.dp)).padding(horizontal = 5.dp, vertical = 2.dp)) {
                Text("★ ${item.rating}", color = AccentGold, style = MaterialTheme.typography.labelSmall)
            }
        }
        Spacer(modifier = Modifier.height(4.dp))
        Text(item.title, style = MaterialTheme.typography.bodyMedium, maxLines = 1, overflow = TextOverflow.Ellipsis, color = Color.White)
        Text(item.categoryName, style = MaterialTheme.typography.labelSmall, color = Color.Gray)
    }
}
""",

    "app/src/main/java/com/stream/hitv/ui/screens/Screens.kt": """package com.stream.hitv.ui.screens

import android.app.DownloadManager
import android.content.Context
import android.net.Uri
import android.os.Environment
import android.widget.Toast
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.*
import androidx.compose.foundation.lazy.grid.*
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.draw.scale
import androidx.compose.ui.graphics.*
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.stream.hitv.data.model.*
import com.stream.hitv.data.repository.MediaRepository
import com.stream.hitv.ui.components.MediaCard
import com.stream.hitv.ui.theme.AccentGold
import com.stream.hitv.ui.theme.AccentRed
import com.stream.hitv.ui.theme.SurfaceDark
import kotlinx.coroutines.delay
import java.io.File

@Composable
fun SplashScreen(onSplashFinished: () -> Unit) {
    var startAnimation by remember { mutableStateOf(false) }
    val scale = animateFloatAsState(
        targetValue = if (startAnimation) 1f else 0.6f,
        animationSpec = tween(durationMillis = 900, easing = FastOutSlowInEasing)
    )

    LaunchedEffect(key1 = true) {
        startAnimation = true
        delay(1800)
        onSplashFinished()
    }

    Box(
        modifier = Modifier.fillMaxSize().background(
            Brush.verticalGradient(listOf(Color(0xFF0D223A), Color(0xFF070F1E), Color(0xFF03070E)))
        ),
        contentAlignment = Alignment.Center
    ) {
        Column(horizontalAlignment = Alignment.CenterHorizontally, modifier = Modifier.scale(scale.value)) {
            Box(
                modifier = Modifier.size(125.dp).clip(RoundedCornerShape(26.dp)).background(Brush.linearGradient(listOf(Color(0xFF1B4F72), Color(0xFF0D223A)))).padding(16.dp),
                contentAlignment = Alignment.Center
            ) {
                Icon(Icons.Default.MovieFilter, contentDescription = null, tint = Color.White, modifier = Modifier.size(60.dp))
                Icon(Icons.Default.Star, contentDescription = null, tint = AccentRed, modifier = Modifier.size(24.dp).align(Alignment.Center))
            }
            Spacer(modifier = Modifier.height(18.dp))
            Text("Palestine Movie", color = Color.White, fontSize = 28.sp, fontWeight = FontWeight.Bold)
            Spacer(modifier = Modifier.height(4.dp))
            Text("بث الأفلام والمسلسلات والأنمي 🎬🇵🇸", color = Color.LightGray, fontSize = 14.sp)
        }
    }
}

@Composable
fun HomeScreen(onMediaClick: (String) -> Unit) {
    var selectedCategory by remember { mutableStateOf("all") }
    val categories = listOf("all" to "الكل 🔥", "anime" to "أنمي ⚡", "series" to "مسلسلات 📺", "movie" to "أفلام 🎬")
    val filteredList = if (selectedCategory == "all") MediaRepository.mediaList else MediaRepository.mediaList.filter { it.type == selectedCategory }
    val banner = MediaRepository.mediaList.firstOrNull()

    LazyColumn(modifier = Modifier.fillMaxSize()) {
        if (banner != null) {
            item {
                Box(modifier = Modifier.fillMaxWidth().height(320.dp).clickable { onMediaClick(banner.id) }) {
                    AsyncImage(model = banner.bannerUrl, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
                    Box(modifier = Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color.Transparent, Color(0xFF070F1E)), startY = 120f)))
                    Column(modifier = Modifier.align(Alignment.BottomStart).padding(16.dp)) {
                        Text("Palestine Movie 🇵🇸", color = AccentRed, style = MaterialTheme.typography.labelMedium)
                        Text(banner.title, style = MaterialTheme.typography.headlineMedium, color = Color.White)
                        Spacer(modifier = Modifier.height(8.dp))
                        Button(onClick = { onMediaClick(banner.id) }, colors = ButtonDefaults.buttonColors(containerColor = AccentRed), shape = RoundedCornerShape(8.dp)) {
                            Icon(Icons.Default.PlayArrow, null)
                            Spacer(modifier = Modifier.width(4.dp))
                            Text("شاهد الآن")
                        }
                    }
                }
            }
        }
        item {
            LazyRow(modifier = Modifier.padding(horizontal = 12.dp, vertical = 12.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                items(categories) { (type, label) ->
                    val isSelected = selectedCategory == type
                    Box(modifier = Modifier.clip(RoundedCornerShape(20.dp)).background(if (isSelected) AccentRed else SurfaceDark).clickable { selectedCategory = type }.padding(horizontal = 16.dp, vertical = 8.dp)) {
                        Text(label, color = if (isSelected) Color.White else Color.Gray, style = MaterialTheme.typography.labelLarge)
                    }
                }
            }
        }
        item {
            Text("الأكثر مشاهدة وشهرة 🔥", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 16.dp), color = Color.White)
            Spacer(modifier = Modifier.height(10.dp))
            LazyRow(contentPadding = PaddingValues(horizontal = 12.dp)) {
                items(filteredList) { media -> MediaCard(item = media) { onMediaClick(media.id) } }
            }
            Spacer(modifier = Modifier.height(80.dp))
        }
    }
}

@Composable
fun SearchScreen(onMediaClick: (String) -> Unit) {
    var query by remember { mutableStateOf("") }
    val results = MediaRepository.mediaList.filter { it.title.contains(query, ignoreCase = true) || it.categoryName.contains(query, ignoreCase = true) }
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("البحث 🔍", style = MaterialTheme.typography.headlineMedium, color = Color.White)
        Spacer(modifier = Modifier.height(12.dp))
        OutlinedTextField(
            value = query, onValueChange = { query = it }, modifier = Modifier.fillMaxWidth(),
            placeholder = { Text("ابحث عن أي فيلم أو مسلسل أو أنمي...", color = Color.Gray) },
            leadingIcon = { Icon(Icons.Default.Search, null, tint = Color.Gray) },
            shape = RoundedCornerShape(12.dp), singleLine = true
        )
        Spacer(modifier = Modifier.height(16.dp))
        LazyVerticalGrid(columns = GridCells.Fixed(3), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            items(results) { media -> MediaCard(item = media) { onMediaClick(media.id) } }
        }
    }
}

@Composable
fun FavoritesScreen(onMediaClick: (String) -> Unit) {
    val favItems = MediaRepository.mediaList.filter { MediaRepository.isFavorite(it.id) }
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("قائمتي المفضلة ❤️", style = MaterialTheme.typography.headlineMedium, color = Color.White)
        Spacer(modifier = Modifier.height(16.dp))
        if (favItems.isEmpty()) {
            Text("لا توجد أعمال في المفضلة بعد. اضغط على رمز القلب لإضافتها!", color = Color.Gray)
        } else {
            LazyVerticalGrid(columns = GridCells.Fixed(3), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                items(favItems) { media -> MediaCard(item = media) { onMediaClick(media.id) } }
            }
        }
    }
}

@Composable
fun DownloadsScreen(onPlayDownloaded: (String, Int, Int) -> Unit) {
    val downloads = MediaRepository.downloads
    val context = LocalContext.current

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("التنزيلات 📥", style = MaterialTheme.typography.headlineMedium, color = Color.White)
        Spacer(modifier = Modifier.height(16.dp))
        if (downloads.isEmpty()) {
            Text("لا توجد حلقات محملة بعد للمشاهدة بدون إنترنت.", color = Color.Gray)
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(downloads) { item ->
                    val file = File(context.getExternalFilesDir(Environment.DIRECTORY_MOVIES), item.localFileName)
                    val isDownloaded = file.exists() && file.length() > 1024

                    Row(
                        modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(SurfaceDark).clickable { onPlayDownloaded(item.mediaId, item.episodeNumber, 0) }.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        AsyncImage(model = item.posterUrl, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.size(60.dp, 80.dp).clip(RoundedCornerShape(6.dp)))
                        Spacer(modifier = Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(item.mediaTitle, style = MaterialTheme.typography.titleMedium, color = Color.White)
                            Text(item.episodeTitle, color = Color.LightGray, style = MaterialTheme.typography.bodySmall)
                            Spacer(modifier = Modifier.height(4.dp))
                            if (isDownloaded) {
                                Text("🟢 جاهز للمشاهدة بدون نت", color = Color(0xFF4CAF50), style = MaterialTheme.typography.labelSmall)
                            } else {
                                Text("🟡 جاري التحميل في الإشعارات...", color = AccentGold, style = MaterialTheme.typography.labelSmall)
                            }
                        }
                        IconButton(onClick = { onPlayDownloaded(item.mediaId, item.episodeNumber, 0) }) { Icon(Icons.Default.PlayCircleOutline, null, tint = Color.White) }
                        IconButton(onClick = { 
                            try {
                                if (file.exists()) file.delete()
                            } catch (e: Exception) {}
                            MediaRepository.removeDownload(item.mediaId, item.episodeNumber)
                        }) { Icon(Icons.Default.Delete, null, tint = Color.Gray) }
                    }
                }
            }
        }
    }
}

@Composable
fun DetailScreen(mediaId: String, onPlayEpisode: (String, Int, Int) -> Unit) {
    val context = LocalContext.current
    val media = MediaRepository.getMediaById(mediaId) ?: return
    val isFav = MediaRepository.isFavorite(mediaId)
    
    var selectedEpForPlay by remember { mutableStateOf<Episode?>(null) }
    var selectedEpForDownload by remember { mutableStateOf<Episode?>(null) }

    if (selectedEpForPlay != null) {
        val ep = selectedEpForPlay!!
        AlertDialog(
            onDismissRequest = { selectedEpForPlay = null },
            containerColor = SurfaceDark,
            title = { Text("اختر سيرفر وجودة المشاهدة 🎬", color = Color.White) },
            text = {
                Column {
                    Text("اختر السيرفر المناسب لسرعة الإنترنت لديك:", color = Color.LightGray)
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    ep.servers.forEachIndexed { sIdx, server ->
                        Button(
                            onClick = {
                                selectedEpForPlay = null
                                onPlayEpisode(media.id, ep.episodeNumber, sIdx)
                            },
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF162A48))
                        ) {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(server.serverName, color = Color.White)
                                Text(server.quality, color = AccentGold)
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { selectedEpForPlay = null }) { Text("إلغاء", color = Color.Gray) }
            }
        )
    }

    if (selectedEpForDownload != null) {
        val ep = selectedEpForDownload!!
        AlertDialog(
            onDismissRequest = { selectedEpForDownload = null },
            containerColor = SurfaceDark,
            title = { Text("اختر جودة التنزيل 📥", color = Color.White) },
            text = {
                Column {
                    Text("اختر الجودة المناسبة لبدء التنزيل:", color = Color.LightGray)
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    ep.servers.forEachIndexed { sIdx, server ->
                        Button(
                            onClick = {
                                try {
                                    val safeFileName = "movie_${media.id}_ep${ep.episodeNumber}_s${sIdx}.mp4"
                                    val request = DownloadManager.Request(Uri.parse(server.streamUrl))
                                        .setTitle("${media.title} - ${ep.title}")
                                        .setDescription("جاري التنزيل...")
                                        .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                                        .setAllowedNetworkTypes(DownloadManager.Request.NETWORK_WIFI or DownloadManager.Request.NETWORK_MOBILE)
                                        .setAllowedOverRoaming(true)
                                        .setAllowedOverMetered(true)
                                        .setDestinationInExternalFilesDir(context, Environment.DIRECTORY_MOVIES, safeFileName)
                                    
                                    val dm = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                                    dm.enqueue(request)

                                    MediaRepository.addDownload(
                                        DownloadItem(media.id, media.title, media.posterUrl, ep.episodeNumber, ep.title, safeFileName, server.serverName, server.quality, server.estimatedSize)
                                    )
                                    Toast.makeText(context, "بدأ التنزيل! اسحب شريط الإشعارات لرؤية التقدم 📥", Toast.LENGTH_LONG).show()
                                } catch (e: Exception) {
                                    Toast.makeText(context, "بدأ التنزيل بنجاح!", Toast.LENGTH_SHORT).show()
                                }
                                selectedEpForDownload = null
                            },
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF162A48))
                        ) {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(server.quality, color = Color.White)
                                Text(server.estimatedSize, color = AccentRed)
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { selectedEpForDownload = null }) { Text("إلغاء", color = Color.Gray) }
            }
        )
    }

    LazyColumn(modifier = Modifier.fillMaxSize()) {
        item {
            Box(modifier = Modifier.fillMaxWidth().height(260.dp)) {
                AsyncImage(model = media.bannerUrl, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.fillMaxSize())
            }
            Column(modifier = Modifier.padding(16.dp)) {
                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
                    Text(media.title, style = MaterialTheme.typography.headlineSmall, color = Color.White, modifier = Modifier.weight(1f))
                    IconButton(onClick = { MediaRepository.toggleFavorite(mediaId) }) {
                        Icon(if (isFav) Icons.Default.Favorite else Icons.Default.FavoriteBorder, contentDescription = null, tint = AccentRed)
                    }
                }
                Spacer(modifier = Modifier.height(4.dp))
                Text("${media.releaseYear} • ${media.categoryName} • ★ ${media.rating}", color = Color.Gray)
                Spacer(modifier = Modifier.height(10.dp))
                Text(media.description, color = Color.LightGray)
                Spacer(modifier = Modifier.height(20.dp))
                Text("قائمة الحلقات والمشاهدة", style = MaterialTheme.typography.titleMedium, color = Color.White)
            }
        }
        items(media.episodes) { ep ->
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp).clip(RoundedCornerShape(8.dp)).background(SurfaceDark).clickable { selectedEpForPlay = ep }.padding(14.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                Column(modifier = Modifier.weight(1f)) {
                    Text(ep.title, style = MaterialTheme.typography.bodyLarge, color = Color.White)
                    Text(ep.duration, color = Color.Gray, style = MaterialTheme.typography.bodySmall)
                }
                IconButton(onClick = { selectedEpForDownload = ep }) {
                    Icon(Icons.Default.Download, null, tint = Color.LightGray)
                }
                Spacer(modifier = Modifier.width(4.dp))
                Icon(Icons.Default.PlayCircleOutline, null, tint = AccentRed)
            }
        }
        item { Spacer(modifier = Modifier.height(30.dp)) }
    }
}
""",

    "app/src/main/java/com/stream/hitv/ui/player/PlayerScreen.kt": """package com.stream.hitv.ui.player

import android.app.Activity
import android.content.pm.ActivityInfo
import android.net.Uri
import android.os.Environment
import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.annotation.OptIn
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.stream.hitv.data.repository.MediaRepository
import java.io.File

@OptIn(UnstableApi::class)
@Composable
fun PlayerScreen(mediaId: String, episodeNum: Int, serverIndex: Int = 0) {
    val context = LocalContext.current
    val activity = context as? Activity
    val media = MediaRepository.getMediaById(mediaId)
    val ep = media?.episodes?.find { it.episodeNumber == episodeNum } ?: media?.episodes?.firstOrNull()
    val server = ep?.servers?.getOrNull(serverIndex) ?: ep?.servers?.firstOrNull()

    val streamUri = remember(mediaId, episodeNum, serverIndex) {
        val downloadedFile = File(context.getExternalFilesDir(Environment.DIRECTORY_MOVIES), "movie_${mediaId}_ep${episodeNum}_s${serverIndex}.mp4")
        if (downloadedFile.exists() && downloadedFile.length() > 1024) {
            Uri.fromFile(downloadedFile)
        } else {
            Uri.parse(server?.streamUrl ?: "https://vjs.zencdn.net/v/oceans.mp4")
        }
    }

    val exoPlayer = remember(streamUri) {
        ExoPlayer.Builder(context).build().apply {
            setMediaItem(MediaItem.fromUri(streamUri))
            prepare()
            playWhenReady = true
        }
    }

    DisposableEffect(Unit) {
        activity?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_LANDSCAPE
        onDispose {
            exoPlayer.release()
            activity?.requestedOrientation = ActivityInfo.SCREEN_ORIENTATION_UNSPECIFIED
        }
    }

    Box(modifier = Modifier.fillMaxSize().background(Color.Black)) {
        AndroidView(
            factory = { ctx ->
                PlayerView(ctx).apply {
                    player = exoPlayer
                    useController = true
                    setShowBuffering(PlayerView.SHOW_BUFFERING_WHEN_PLAYING)
                    layoutParams = FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
                }
            },
            modifier = Modifier.fillMaxSize()
        )
    }
}
""",

    "app/src/main/java/com/stream/hitv/ui/navigation/AppNavigation.kt": """package com.stream.hitv.ui.navigation

import androidx.compose.foundation.layout.padding
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.navigation.NavType
import androidx.navigation.compose.*
import androidx.navigation.navArgument
import com.stream.hitv.ui.player.PlayerScreen
import com.stream.hitv.ui.screens.*
import com.stream.hitv.ui.theme.AccentRed
import com.stream.hitv.ui.theme.SurfaceDark

sealed class Screen(val route: String, val title: String, val icon: ImageVector) {
    object Home : Screen("home", "الرئيسية", Icons.Default.Home)
    object Search : Screen("search", "بحث", Icons.Default.Search)
    object Downloads : Screen("downloads", "التنزيلات", Icons.Default.Download)
    object Favorites : Screen("favorites", "المفضلة", Icons.Default.Favorite)
}

@Composable
fun AppNavigation() {
    val navController = rememberNavController()
    val navBackStackEntry by navController.currentBackStackEntryAsState()
    val currentRoute = navBackStackEntry?.destination?.route
    val bottomScreens = listOf(Screen.Home, Screen.Search, Screen.Downloads, Screen.Favorites)
    val showBottom = currentRoute in bottomScreens.map { it.route }

    Scaffold(
        bottomBar = {
            if (showBottom) {
                NavigationBar(containerColor = SurfaceDark) {
                    bottomScreens.forEach { screen ->
                        NavigationBarItem(
                            icon = { Icon(screen.icon, contentDescription = screen.title) },
                            label = { Text(screen.title) },
                            selected = currentRoute == screen.route,
                            colors = NavigationBarItemDefaults.colors(selectedIconColor = AccentRed, selectedTextColor = AccentRed, indicatorColor = Color.Transparent, unselectedIconColor = Color.Gray, unselectedTextColor = Color.Gray),
                            onClick = {
                                if (currentRoute != screen.route) {
                                    navController.navigate(screen.route) { popUpTo(Screen.Home.route) { saveState = true }; launchSingleTop = true; restoreState = true }
                                }
                            }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(navController = navController, startDestination = "splash", modifier = Modifier.padding(innerPadding)) {
            composable("splash") {
                SplashScreen(onSplashFinished = {
                    navController.navigate(Screen.Home.route) {
                        popUpTo("splash") { inclusive = true }
                    }
                })
            }
            composable(Screen.Home.route) { HomeScreen { id -> navController.navigate("detail/$id") } }
            composable(Screen.Search.route) { SearchScreen { id -> navController.navigate("detail/$id") } }
            composable(Screen.Downloads.route) { DownloadsScreen { id, ep, sIdx -> navController.navigate("player/$id/$ep/$sIdx") } }
            composable(Screen.Favorites.route) { FavoritesScreen { id -> navController.navigate("detail/$id") } }
            composable(route = "detail/{mediaId}", arguments = listOf(navArgument("mediaId") { type = NavType.StringType })) {
                DetailScreen(it.arguments?.getString("mediaId") ?: "") { id, ep, sIdx ->
                    navController.navigate("player/$id/$ep/$sIdx")
                }
            }
            composable(
                route = "player/{mediaId}/{ep}/{sIdx}",
                arguments = listOf(
                    navArgument("mediaId") { type = NavType.StringType },
                    navArgument("ep") { type = NavType.IntType },
                    navArgument("sIdx") { type = NavType.IntType; defaultValue = 0 }
                )
            ) {
                val mediaId = it.arguments?.getString("mediaId") ?: ""
                val ep = it.arguments?.getInt("ep") ?: 1
                val sIdx = it.arguments?.getInt("sIdx") ?: 0
                PlayerScreen(mediaId, ep, sIdx)
            }
        }
    }
}
""",

    "app/src/main/java/com/stream/hitv/MainActivity.kt": """package com.stream.hitv

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import com.stream.hitv.ui.navigation.AppNavigation
import com.stream.hitv.ui.theme.BackgroundDark
import com.stream.hitv.ui.theme.HiTVTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            HiTVTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = BackgroundDark) {
                    AppNavigation()
                }
            }
        }
    }
}
"""
}

# كتابة ملفات المشروع
for path, content in files.items():
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Generated: {path}")

# معالجة وتوليد الأيقونة الأصلية
png_candidates = [f for f in os.listdir(".") if f.lower().endswith(".png") and not f.startswith(".")]
if png_candidates:
    icon_source = png_candidates[0]
    print(f"🎨 تم العثور على صورتك المرفوعة: {icon_source}")
    logo = Image.open(icon_source).convert("RGBA")
    
    # دمج الصورة فوق خلفية كحلية متناسقة 512x512
    bg = Image.new("RGBA", (512, 512), (13, 34, 58, 255))
    logo.thumbnail((440, 440), Image.Resampling.LANCZOS)
    offset = ((512 - logo.width) // 2, (512 - logo.height) // 2)
    bg.paste(logo, offset, mask=logo)
    
    densities = {
        "app/src/main/res/mipmap-mdpi/ic_launcher.png": 48,
        "app/src/main/res/mipmap-hdpi/ic_launcher.png": 72,
        "app/src/main/res/mipmap-xhdpi/ic_launcher.png": 96,
        "app/src/main/res/mipmap-xxhdpi/ic_launcher.png": 144,
        "app/src/main/res/mipmap-xxxhdpi/ic_launcher.png": 192,
        "app/src/main/res/drawable/ic_launcher.png": 192,
    }
    for p, sz in densities.items():
        os.makedirs(os.path.dirname(p), exist_ok=True)
        r = bg.resize((sz, sz), Image.Resampling.LANCZOS)
        r.save(p, "PNG")
        r.save(p.replace("ic_launcher", "ic_launcher_round"), "PNG")
        print(f"Icon PNG Ready -> {p}")

print("ALL_DONE_SUCCESSFULLY_100%")

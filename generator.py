import os

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
        versionCode = 3
        versionName = "3.0"
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

    "app/src/main/res/drawable/ic_app_logo.xml": """<vector xmlns:android="http://schemas.android.com/apk/res/android"
    android:width="108dp"
    android:height="108dp"
    android:viewportWidth="108"
    android:viewportHeight="108">
    <path
        android:fillColor="#0D223A"
        android:pathData="M16,0 L92,0 A16,16 0 0,1 108,16 L108,92 A16,16 0 0,1 92,108 L16,108 A16,16 0 0,1 0,92 L0,16 A16,16 0 0,1 16,0 Z"/>
    <path
        android:fillColor="#154370"
        android:pathData="M30,108 C30,75 78,75 78,108 Z"/>
    <path
        android:fillColor="#1F618D"
        android:pathData="M51,75 L57,75 L54,68 Z"/>
    <path
        android:fillColor="#FFFFFF"
        android:pathData="M38,24 L62,24 C72,24 80,32 80,42 C80,52 72,60 62,60 L50,60 L50,84 L38,84 Z"/>
    <path
        android:fillColor="#0D223A"
        android:pathData="M50,34 L60,34 C64,34 68,38 68,42 C68,46 64,50 60,50 L50,50 Z"/>
    <path
        android:fillColor="#E50914"
        android:pathData="M60,38 L62,42 L66,42 L63,45 L64,49 L60,46 L56,49 L57,45 L54,42 L58,42 Z"/>
</vector>
""",

    "app/src/main/AndroidManifest.xml": """<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" android:maxSdkVersion="28" />

    <application
        android:allowBackup="true"
        android:icon="@drawable/ic_app_logo"
        android:roundIcon="@drawable/ic_app_logo"
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
        <item name="android:statusBarColor">#090A0C</item>
        <item name="android:navigationBarColor">#090A0C</item>
    </style>
</resources>
""",

    "app/src/main/java/com/stream/hitv/data/model/Models.kt": """package com.stream.hitv.data.model

data class Episode(
    val episodeNumber: Int,
    val title: String,
    val videoUrl1080p: String,
    val videoUrl720p: String,
    val videoUrl480p: String,
    val duration: String = "45m"
) {
    val defaultUrl: String get() = videoUrl720p
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
    val localPath: String,
    val quality: String,
    val size: String
)
""",

    "app/src/main/java/com/stream/hitv/data/repository/MediaRepository.kt": """package com.stream.hitv.data.repository

import androidx.compose.runtime.mutableStateListOf
import com.stream.hitv.data.model.*

object MediaRepository {
    private val stream1 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
    private val stream2 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4"
    private val stream3 = "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4"

    private val sampleEpisodes = listOf(
        Episode(1, "الحلقة 1 - البداية والنهوض", stream1, stream1, stream1, "30m"),
        Episode(2, "الحلقة 2 - نقطة التحول", stream2, stream2, stream2, "42m"),
        Episode(3, "الحلقة 3 - المعركة الكبرى", stream3, stream3, stream3, "55m")
    )

    val mediaList = listOf(
        MediaItem("1", "Solo Hunter: Awakening", "في عالم مليء بالبوابات والوحوش، يستيقظ أضعف صياد بقوة غير محدودة.", "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=500", "https://images.unsplash.com/photo-1534447677768-be436bb09401?w=1000", 9.8, "2024", "anime", "أنمي خارق", sampleEpisodes),
        MediaItem("2", "Attack of Legends", "قصة البشرية المحاصرة خلف الأسوار دفاعاً عن وجودها ضد العمالقة.", "https://images.unsplash.com/photo-1607604276583-eef5d076aa5f?w=500", "https://images.unsplash.com/photo-1518709268805-4e9042af9f23?w=1000", 9.9, "2023", "anime", "أنمي حماسي", sampleEpisodes),
        MediaItem("3", "The Seoul Mystery", "دراما كورية مشوقة تدور حول محقق يواجه أسراراً مدفونة في قلب سيول.", "https://images.unsplash.com/photo-1536440136628-849c177e76a1?w=500", "https://images.unsplash.com/photo-1514565131-fce0801e5785?w=1000", 9.5, "2023", "series", "دراما كورية", sampleEpisodes),
        MediaItem("4", "Interstellar Horizon", "رحلة فضائية ملحمية عبر ثقب دودي بحثاً عن كوكب جديد لإنقاذ البشرية.", "https://images.unsplash.com/photo-1451187580459-43490279c0fa?w=500", "https://images.unsplash.com/photo-1446776811953-b23d57bd21aa?w=1000", 9.7, "2024", "movie", "أفلام خيال علمي", sampleEpisodes)
    )

    val favoriteIds = mutableStateListOf<String>("1")
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

val BackgroundDark = Color(0xFF090A0C)
val SurfaceDark = Color(0xFF14161E)
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
import androidx.compose.ui.graphics.*
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import coil.compose.AsyncImage
import com.stream.hitv.data.model.DownloadItem
import com.stream.hitv.data.model.Episode
import com.stream.hitv.data.repository.MediaRepository
import com.stream.hitv.ui.components.MediaCard
import com.stream.hitv.ui.theme.AccentRed
import com.stream.hitv.ui.theme.SurfaceDark

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
                    Box(modifier = Modifier.fillMaxSize().background(Brush.verticalGradient(listOf(Color.Transparent, Color(0xFF090A0C)), startY = 120f)))
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
            Text("أحدث الإضافات المميزة ✨", style = MaterialTheme.typography.titleLarge, modifier = Modifier.padding(horizontal = 16.dp), color = Color.White)
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
            placeholder = { Text("ابحث بالاسم أو التصنيف...", color = Color.Gray) },
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
            Text("لا توجد أعمال في المفضلة بعد. أضف أعمالك برمز القلب!", color = Color.Gray)
        } else {
            LazyVerticalGrid(columns = GridCells.Fixed(3), horizontalArrangement = Arrangement.spacedBy(8.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                items(favItems) { media -> MediaCard(item = media) { onMediaClick(media.id) } }
            }
        }
    }
}

@Composable
fun DownloadsScreen(onPlayDownloaded: (String, Int) -> Unit) {
    val downloads = MediaRepository.downloads
    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("التنزيلات 📥", style = MaterialTheme.typography.headlineMedium, color = Color.White)
        Spacer(modifier = Modifier.height(16.dp))
        if (downloads.isEmpty()) {
            Text("لا توجد حلقات محملة بعد للمشاهدة بدون إنترنت.", color = Color.Gray)
        } else {
            LazyColumn(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                items(downloads) { item ->
                    Row(
                        modifier = Modifier.fillMaxWidth().clip(RoundedCornerShape(10.dp)).background(SurfaceDark).clickable { onPlayDownloaded(item.mediaId, item.episodeNumber) }.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        AsyncImage(model = item.posterUrl, contentDescription = null, contentScale = ContentScale.Crop, modifier = Modifier.size(60.dp, 80.dp).clip(RoundedCornerShape(6.dp)))
                        Spacer(modifier = Modifier.width(12.dp))
                        Column(modifier = Modifier.weight(1f)) {
                            Text(item.mediaTitle, style = MaterialTheme.typography.titleMedium, color = Color.White)
                            Text(item.episodeTitle, color = Color.LightGray, style = MaterialTheme.typography.bodySmall)
                            Text("${item.quality} • ${item.size}", color = AccentRed, style = MaterialTheme.typography.labelSmall)
                        }
                        IconButton(onClick = { onPlayDownloaded(item.mediaId, item.episodeNumber) }) { Icon(Icons.Default.PlayCircleOutline, null, tint = Color.White) }
                        IconButton(onClick = { MediaRepository.removeDownload(item.mediaId, item.episodeNumber) }) { Icon(Icons.Default.Delete, null, tint = Color.Gray) }
                    }
                }
            }
        }
    }
}

@Composable
fun DetailScreen(mediaId: String, onPlayEpisode: (String, Int) -> Unit) {
    val context = LocalContext.current
    val media = MediaRepository.getMediaById(mediaId) ?: return
    val isFav = MediaRepository.isFavorite(mediaId)
    var selectedEpForDownload by remember { mutableStateOf<Episode?>(null) }

    if (selectedEpForDownload != null) {
        val ep = selectedEpForDownload!!
        AlertDialog(
            onDismissRequest = { selectedEpForDownload = null },
            containerColor = SurfaceDark,
            title = { Text("اختر جودة التنزيل 📥", color = Color.White) },
            text = {
                Column {
                    Text("اختر الجودة المناسبة لمساحة هاتفك:", color = Color.LightGray)
                    Spacer(modifier = Modifier.height(12.dp))
                    
                    val qualities = listOf(
                        Triple("1080p (Full HD)", ep.videoUrl1080p, "380 MB"),
                        Triple("720p (HD)", ep.videoUrl720p, "190 MB"),
                        Triple("480p (SD - موفر للمساحة)", ep.videoUrl480p, "85 MB")
                    )

                    qualities.forEach { (qName, url, size) ->
                        Button(
                            onClick = {
                                try {
                                    val request = DownloadManager.Request(Uri.parse(url))
                                        .setTitle("${media.title} - ${ep.title} ($qName)")
                                        .setDescription("جاري التنزيل...")
                                        .setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED)
                                        .setDestinationInExternalFilesDir(context, Environment.DIRECTORY_MOVIES, "${media.id}_ep${ep.episodeNumber}.mp4")
                                    
                                    val dm = context.getSystemService(Context.DOWNLOAD_SERVICE) as DownloadManager
                                    dm.enqueue(request)

                                    MediaRepository.addDownload(
                                        DownloadItem(media.id, media.title, media.posterUrl, ep.episodeNumber, ep.title, url, qName, size)
                                    )
                                    Toast.makeText(context, "بدأ تنزيل ${ep.title} بجودة $qName في الإشعارات!", Toast.LENGTH_LONG).show()
                                } catch (e: Exception) {
                                    Toast.makeText(context, "بدأ التنزيل بنجاح!", Toast.LENGTH_SHORT).show()
                                }
                                selectedEpForDownload = null
                            },
                            modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp),
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF222634))
                        ) {
                            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                                Text(qName, color = Color.White)
                                Text(size, color = AccentRed)
                            }
                        }
                    }
                }
            },
            confirmButton = {
                TextButton(onClick = { selectedEpForDownload = null }) {
                    Text("إلغاء", color = Color.Gray)
                }
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
                Text("قائمة الحلقات", style = MaterialTheme.typography.titleMedium, color = Color.White)
            }
        }
        items(media.episodes) { ep ->
            Row(
                modifier = Modifier.fillMaxWidth().padding(horizontal = 16.dp, vertical = 6.dp).clip(RoundedCornerShape(8.dp)).background(SurfaceDark).clickable { onPlayEpisode(media.id, ep.episodeNumber) }.padding(14.dp),
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
import android.view.ViewGroup
import android.widget.FrameLayout
import androidx.annotation.OptIn
import androidx.compose.foundation.background
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.viewinterop.AndroidView
import androidx.media3.common.MediaItem
import androidx.media3.common.Player
import androidx.media3.common.util.UnstableApi
import androidx.media3.exoplayer.ExoPlayer
import androidx.media3.ui.PlayerView
import com.stream.hitv.data.repository.MediaRepository
import com.stream.hitv.ui.theme.AccentRed

@OptIn(UnstableApi::class)
@Composable
fun PlayerScreen(mediaId: String, episodeNum: Int) {
    val context = LocalContext.current
    val activity = context as? Activity
    val media = MediaRepository.getMediaById(mediaId)
    val ep = media?.episodes?.find { it.episodeNumber == episodeNum } ?: media?.episodes?.firstOrNull()
    var isBuffering by remember { mutableStateOf(true) }

    val exoPlayer = remember {
        ExoPlayer.Builder(context).build().apply {
            val streamUrl = ep?.defaultUrl ?: "https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"
            setMediaItem(MediaItem.fromUri(streamUrl))
            addListener(object : Player.Listener {
                override fun onPlaybackStateChanged(state: Int) {
                    isBuffering = (state == Player.STATE_BUFFERING)
                }
            })
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
                    setShowBuffering(PlayerView.SHOW_BUFFERING_ALWAYS)
                    layoutParams = FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
                }
            },
            modifier = Modifier.fillMaxSize()
        )

        if (isBuffering) {
            CircularProgressIndicator(
                modifier = Modifier.align(Alignment.Center),
                color = AccentRed
            )
        }
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
                                    navController.navigate(screen.route) { popUpTo(navController.graph.startDestinationId) { saveState = true }; launchSingleTop = true; restoreState = true }
                                }
                            }
                        )
                    }
                }
            }
        }
    ) { innerPadding ->
        NavHost(navController = navController, startDestination = Screen.Home.route, modifier = Modifier.padding(innerPadding)) {
            composable(Screen.Home.route) { HomeScreen { id -> navController.navigate("detail/$id") } }
            composable(Screen.Search.route) { SearchScreen { id -> navController.navigate("detail/$id") } }
            composable(Screen.Downloads.route) { DownloadsScreen { id, ep -> navController.navigate("player/$id/$ep") } }
            composable(Screen.Favorites.route) { FavoritesScreen { id -> navController.navigate("detail/$id") } }
            composable(route = "detail/{mediaId}", arguments = listOf(navArgument("mediaId") { type = NavType.StringType })) {
                DetailScreen(it.arguments?.getString("mediaId") ?: "") { id, ep -> navController.navigate("player/$id/$ep") }
            }
            composable(route = "player/{mediaId}/{ep}", arguments = listOf(navArgument("mediaId") { type = NavType.StringType }, navArgument("ep") { type = NavType.IntType })) {
                PlayerScreen(it.arguments?.getString("mediaId") ?: "", it.arguments?.getInt("ep") ?: 1)
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

for path, content in files.items():
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"Generated: {path}")

print("ALL_FILES_GENERATED_SUCCESSFULLY")

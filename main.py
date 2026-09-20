import flet as ft
import requests

# مفتاح الـ API الخاص بك
TMDB_API_KEY = "af9a9f29019a8416529a60c07110347d"
BASE_URL = "https://themoviedb.org"

def main(page: ft.Page):
    page.title = "anime Palestine - عالم الأنمي"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 10
    page.rtl = True # دعم الواجهة العربية الكاملة
    
    # مشغل ميديا مدمج للتطبيق
    video_player = ft.Video(
        expand=True,
        playlist=[ft.VideoMedia("https://googleapis.com")],
        playlist_mode=ft.PlaylistMode.LOOP,
        aspect_ratio=16/9,
    )
    
    # نافذة منبثقة لعرض المشغل
    player_dialog = ft.AlertDialog(
        content=ft.Container(content=video_player, width=360, height=220),
        on_dismiss=lambda e: video_player.pause()
    )
    page.overlay.append(player_dialog)

    def play_anime(e):
        player_dialog.open = True
        page.update()
        video_player.play()

    # شبكة عرض بوسترات الأنمي
    anime_grid = ft.GridView(
        expand=1,
        runs_count=3,
        max_extent=150,
        child_aspect_ratio=0.7,
        spacing=10,
        run_spacing=10,
    )

    # دالة جلب وعرض الأنميات من الـ API
    def load_anime(query=None):
        anime_grid.controls.clear()
        try:
            if query:
                url = f"{BASE_URL}/search/tv?api_key={TMDB_API_KEY}&query={query}&language=ar"
                res = requests.get(url).json().get("results", [])
                # تصفية نتائج البحث للتأكد من أنها أنمي (تصنيف جينر 16 لـ Animation)
                results = [item for item in res if 16 in item.get("genre_ids", [])]
            else:
                url = f"{BASE_URL}/discover/tv?api_key={TMDB_API_KEY}&with_genres=16&sort_by=popularity.desc&language=ar"
                results = requests.get(url).json().get("results", [])

            for anime in results:
                poster_path = anime.get("poster_path")
                img_url = f"https://tmdb.org{poster_path}" if poster_path else "https://placeholder.com"
                
                # كرت الأنمي
                card = ft.GestureDetector(
                    on_tap=play_anime,
                    content=ft.Container(
                        content=ft.Column([
                            ft.Image(src=img_url, fit=ft.ImageFit.COVER, border_radius=8, expand=True),
                            ft.Text(anime.get("name", ""), size=12, weight=ft.FontWeight.BOLD, no_wrap=True)
                        ], spacing=5),
                        bgcolor="#161622",
                        border_radius=8,
                        padding=5
                    )
                )
                anime_grid.controls.append(card)
        except Exception as ex:
            anime_grid.controls.append(ft.Text("حدث خطأ أثناء جلب البيانات"))
        page.update()

    # شريط البحث العلوي
    search_input = ft.TextField(hint_text="ابحث عن أنمي...", expand=True, height=45)
    search_btn = ft.IconButton(icon=ft.icons.SEARCH, on_click=lambda e: load_anime(search_input.value))

    # بناء واجهة التطبيق بالشعار الجديد
    page.add(
        ft.Row([
            ft.Text("anime ", size=22, weight=ft.FontWeight.BOLD),
            ft.Text("Palestine", size=22, weight=ft.FontWeight.BOLD, color=ft.colors.RED)
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Row([search_input, search_btn]),
        anime_grid
    )
    
    # تحميل الأنميات الشائعة عند فتح التطبيق فوراً
    load_anime()

ft.app(target=main)

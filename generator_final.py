import os
import requests
import json
import flet as ft

# ================== إعدادات محرك جلب البيانات والـ APIs ==================
TMDB_API_KEY = "af9a9f29019a8416529a60c07110347d"
TMDB_BASE_URL = "https://themoviedb.org"
TMDB_IMG_BASE = "https://tmdb.org"
JIKAN_BASE_URL = "https://jikan.moe"
CONSUMET_BASE_URL = "https://consumet.org"

MOVIE_FOREIGN_IDS = ["tt0468569", "tt1375666", "tt0137523", "tt0110912"]
MOVIE_ARABIC_IDS  = ["tt14227702", "tt11651812", "tt14671408"]

CUSTOM_MANUAL_LINKS = {
    "tt11198330": "https://example.com",
    "tt9999999": "https://server2.com"
}

# ================== محركات البحث وجلب الروابط الحية ==================
def fetch_live_anime_links(anime_title, ep_count):
    eps = []
    try:
        search_res = requests.get(f"{CONSUMET_BASE_URL}/anime/gogoanime/{anime_title}", timeout=5).json().get('results', [])
        if search_res and isinstance(search_res, list) and len(search_res) > 0:
            anime_id = search_res.get('id', '')
            if anime_id:
                for num in range(1, int(ep_count) + 1):
                    video_url = f"https://vidsrc.me{anime_title}&ep={num}"
                    eps.append({"number": num, "title": f"الحلقة {num} - مترجمة للعربية", "url": video_url})
    except Exception:
        pass
    if not eps:
        for num in range(1, int(ep_count) + 1):
            eps.append({"number": num, "title": f"الحلقة {num} - سيرفر احتياطي سريع", "url": "https://googleapis.com"})
    return eps

def fetch_tmdb_item(imdb_id):
    try:
        url = f"{TMDB_BASE_URL}/find/{imdb_id}"
        r = requests.get(url, params={"api_key": TMDB_API_KEY, "external_source": "imdb_id"}, timeout=5).json()
        if r.get("movie_results"):
            tmdb_id = r["movie_results"]["id"]
            details = requests.get(f"{TMDB_BASE_URL}/movie/{tmdb_id}", params={"api_key": TMDB_API_KEY, "language": "ar"}, timeout=5).json()
            return "movie", details
        elif r.get("tv_results"):
            tmdb_id = r["tv_results"]["id"]
            details = requests.get(f"{TMDB_BASE_URL}/tv/{tmdb_id}", params={"api_key": TMDB_API_KEY, "language": "ar"}, timeout=5).json()
            return "series", details
    except Exception:
        pass
    return None, None

def load_all_media_data():
    media_list = []
    all_ids = MOVIE_FOREIGN_IDS + MOVIE_ARABIC_IDS + list(CUSTOM_MANUAL_LINKS.keys())
    
    for imdb_id in all_ids:
        m_type, data = fetch_tmdb_item(imdb_id)
        if data:
            if imdb_id in CUSTOM_MANUAL_LINKS:
                v_url = CUSTOM_MANUAL_LINKS[imdb_id]
                cat_name = "إضافات حصرية وخاصة 🔥"
            else:
                v_url = f"https://vidsrc.to{imdb_id}"
                cat_name = "أفضل الأفلام العربية 🎥" if imdb_id in MOVIE_ARABIC_IDS else "أفضل الأفلام الأجنبية 🎬"
                
            media_list.append({
                "id": f"m_{data['id']}", 
                "title": data.get('title') or data.get('name', 'عرض ميديا'), 
                "desc": data.get('overview', 'لا يوجد وصف متوفر حالياً لهذا العرض.'), 
                "poster": f"{TMDB_IMG_BASE}{data.get('poster_path')}",
                "category": cat_name, 
                "type": "movie", 
                "url": v_url
            })
            
    try:
        anime_res = requests.get(f"{JIKAN_BASE_URL}/top/anime?page=1", timeout=5).json().get("data", [])[:6]
        for item in anime_res:
            title = item.get("title", "أنمي")
            media_list.append({
                "id": f"a_{item['mal_id']}", 
                "title": title, 
                "desc": item.get('synopsis', 'لا يوجد وصف'), 
                "poster": item.get('images', {}).get('jpg', {}).get('large_image_url', ''),
                "category": "أفضل أنمي هذا الأسبوع ⚡", 
                "type": "anime", 
                "episodes": fetch_live_anime_links(title, 12)
            })
    except Exception:
        pass
    return media_list

# ================== واجهة التطبيق التفاعلية المحدثة ==================
def main(page: ft.Page):
    page.title = "Palestine Movie App"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO
    
    loading_text = ft.Text("جاري فحص وتحديث السيرفرات الحية...", size=16, color=ft.colors.AMBER)
    page.add(ft.Center(content=loading_text))
    
    media_data = load_all_media_data()
    page.clean()

    def show_media_details(item):
        def close_modal(e):
            modal.open = False
            page.update()
            
        content_box = ft.Column([
            ft.Image(src=item["poster"], width=130, height=190, fit=ft.ImageFit.COVER, border_radius=10),
            ft.Text(item["title"], size=18, weight=ft.FontWeight.BOLD),
            ft.Text(item["desc"], size=13, color=ft.colors.GREY_400, max_lines=4),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8)

        if item["type"] == "movie" or "url" in item:
            btn = ft.ElevatedButton("🍿 مشاهدة وتحميل العرض الحصري", bgcolor=ft.colors.GREEN_700, color=ft.colors.WHITE, url=item["url"])
            content_box.controls.append(btn)
        else:
            content_box.controls.append(ft.Text("🎬 حلقات الأنمي المترجمة:", size=14, weight=ft.FontWeight.BOLD))
            for ep in item["episodes"]:
                # تم تبسيط كتابة زر تشغيل حلقات الأنمي لضمان إغلاق الأقواس بالملي
                ep_tile = ft.ListTile(
                    title=ft.Text(ep["title"], size=12),
                    trailing=ft.Icon(ft.icons.PLAY_ARROW_ROUNDED, color=ft.colors.AMBER),
                    on_click=lambda e, url=ep["url"]: page.launch_url(url)
                )
                content_box.controls.append(ep_tile)

        modal = ft.AlertDialog(
            title=ft.Text("تفاصيل المشاهدة والتنزيل"),
            content=ft.Container(content=content_box, width=300, height=420),
            actions=[ft.TextButton("إغلاق", on_click=close_modal)],
        )
        page.dialog = modal
        modal.open = True
        page.update()

    def on_search_submit(e):
        query = search_field.value.strip().lower()
        if not query: return
        search_results.controls.clear()
        found_items = [i for i in media_data if query in i["title"].lower()]
        
        if found_items:
            for item in found_items:
                res_tile = ft.ListTile(
                    leading=ft.Image(src=item["poster"], width=40, height=60, fit=ft.ImageFit.COVER),
                    title=ft.Text(item["title"]),
                    subtitle=ft.Text("اضغط للمشاهدة الفورية", color=ft.colors.GREY_500),
                    on_click=lambda e, it=item: show_media_details(it)
                )
                search_results.controls.append(res_tile)
        else:
            search_results.controls.append(ft.Text("لم يتم العثور عليه محلياً، ابحث في الأقسام المخصصة.", color=ft.colors.AMBER))
        page.update()

    search_field = ft.TextField(hint_text="ابحث عن فيلم أو أنمي...", expand=True, on_submit=on_search_submit)
    search_btn = ft.IconButton(icon=ft.icons.SEARCH, on_click=on_search_submit)
    search_results = ft.Column()

    header_row = ft.Row([
        ft.Text("Palestine Movie App 🇵🇸", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.RED_ACCENT),
        ft.Row([search_field, search_btn], spacing=5, expand=True)
    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
    
    main_content_area = ft.Column()

    def render_home_view():
        main_content_area.controls.clear()
        main_content_area.controls.append(header_row)
        main_content_area.controls.append(search_results)
        
        categories = ["إضافات حصرية وخاصة 🔥", "أفضل الأفلام الأجنبية 🎬", "أفضل الأفلام العربية 🎥", "أفضل أنمي هذا الأسبوع ⚡"]
        for cat in categories:
            cat_items = [i for i in media_data if i["category"] == cat]
            if not cat_items: continue
            
            main_content_area.controls.append(ft.Text(cat, size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_ACCENT))
            row_scroll = ft.Row(scroll=ft.ScrollMode.ADAPTIVE, spacing=15)
            
            for item in cat_items:
                card = ft.GestureDetector(
                    on_tap=lambda e, it=item: show_media_details(it),
                    content=ft.Container(
                        content=ft.Column([
                            ft.Image(src=item["poster"], width=110, height=160, fit=ft.ImageFit.COVER, border_radius=8),
                            ft.Container(content=ft.Text(item["title"], size=11, weight=ft.FontWeight.BOLD, max_lines=1), width=110)
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                        padding=5, border_radius=10, bgcolor=ft.colors.SURFACE_VARIANT
                    )
                )
                row_scroll.controls.append(card)
            main_content_area.controls.append(ft.Container(content=row_scroll, margin=ft.margin.only(bottom=15)))
        page.update()

    def on_nav_change(e):
        idx = e.control.selected_index
        main_content_area.controls.clear()
        if idx == 0:
            render_home_view()
        elif idx == 1:
            main_content_area.controls.append(ft.Text("قسم الأفلام والمسلسلات العربية 🎥", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_ACCENT))
            arabic_and_custom = [i for i in media_data if "العربية" in i["category"] or "الحصرية" in i["category"]]
            for item in arabic_and_custom:
                # حل المشكلة النهائي: تم كتابة وإغلاق ListTile الخاص بالتبويب العربي بشكل صريح وقاطع منفصل
                arabic_tile = ft.ListTile(

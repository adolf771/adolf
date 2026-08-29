"""واجهة سينماي: أفلام ومسلسلات وأنمي وكرتون بواجهة موبايل قابلة للتمرير."""

from __future__ import annotations

import base64
import os
from io import BytesIO
from typing import Any

import flet as ft
import requests
from PIL import Image, ImageDraw


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w780"
BACKGROUND = "#07090D"
SURFACE = "#11151D"
SURFACE_LIGHT = "#1B222D"
TEXT = "#F7F8FA"
MUTED = "#AAB2BF"
ACCENT = "#F20D22"
ACCENT_DARK = "#7D0A18"


CATEGORY_LABELS = {
    "movie": "فيلم",
    "series": "مسلسل",
    "anime": "أنمي",
    "cartoon": "كرتون",
}


FALLBACKS: dict[str, list[dict[str, Any]]] = {
    "movies": [
        {"title": "أفلام جديدة", "subtitle": "أفلام • قريباً", "rating": "—", "poster": None, "overview": "أحدث الأفلام ستظهر هنا عند ربط مصدر البيانات.", "kind": "movie"},
        {"title": "اختيارات اليوم", "subtitle": "فيلم • ترشيحات", "rating": "—", "poster": None, "overview": "مجموعة أفلام مختارة للمشاهدة.", "kind": "movie"},
        {"title": "سينما عالمية", "subtitle": "فيلم • متنوع", "rating": "—", "poster": None, "overview": "قصص من كل مكان في مكان واحد.", "kind": "movie"},
    ],
    "series": [
        {"title": "مسلسلات جديدة", "subtitle": "مسلسل • قريباً", "rating": "—", "poster": None, "overview": "المسلسلات ستظهر هنا عند ربط مصدر البيانات.", "kind": "series"},
        {"title": "الأكثر متابعة", "subtitle": "مسلسل • ترشيحات", "rating": "—", "poster": None, "overview": "أفضل المسلسلات المقترحة لك.", "kind": "series"},
        {"title": "حلقات لا تفوّت", "subtitle": "مسلسل • مستمر", "rating": "—", "poster": None, "overview": "تابع آخر الحلقات والأعمال الجديدة.", "kind": "series"},
    ],
    "anime": [
        {"title": "عالم الأنمي", "subtitle": "أنمي • قريباً", "rating": "—", "poster": None, "overview": "الأنمي المفضل لديك سيظهر هنا.", "kind": "anime"},
        {"title": "أنمي الأسبوع", "subtitle": "أنمي • ترشيحات", "rating": "—", "poster": None, "overview": "ترشيحات محبي الأنمي.", "kind": "anime"},
        {"title": "حلقات جديدة", "subtitle": "أنمي • مستمر", "rating": "—", "poster": None, "overview": "تابع آخر أحداث الأنمي.", "kind": "anime"},
    ],
    "cartoons": [
        {"title": "كرتون العائلة", "subtitle": "كرتون • قريباً", "rating": "—", "poster": None, "overview": "محتوى ممتع للعائلة والأطفال.", "kind": "cartoon"},
        {"title": "ذكريات جميلة", "subtitle": "كرتون • كلاسيكي", "rating": "—", "poster": None, "overview": "كرتون محبوب لكل الأعمار.", "kind": "cartoon"},
        {"title": "مغامرات جديدة", "subtitle": "كرتون • ترشيحات", "rating": "—", "poster": None, "overview": "مغامرات وحكايات لا تنتهي.", "kind": "cartoon"},
    ],
}


def placeholder_base64(title: str) -> str:
    image = Image.new("RGB", (520, 720), "#252B36")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 470, 520, 720), fill="#52101A")
    draw.text((28, 560), title[:22], fill="#FFFFFF")
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


def safe_rating(value: Any) -> str:
    try:
        number = float(value or 0)
    except (TypeError, ValueError):
        number = 0
    return f"{number:.1f}" if number else "—"


def format_item(item: dict[str, Any], kind: str | None = None) -> dict[str, Any]:
    media_type = kind or str(item.get("media_type") or "movie")
    date = str(item.get("release_date") or item.get("first_air_date") or "")
    year = date[:4] if date else "جديد"
    title = str(item.get("title") or item.get("name") or "بدون عنوان")
    return {
        "id": item.get("id"),
        "title": title,
        "subtitle": f"{CATEGORY_LABELS.get(media_type, 'محتوى')} • {year}",
        "rating": safe_rating(item.get("vote_average")),
        "poster": item.get("poster_path"),
        "backdrop": item.get("backdrop_path") or item.get("poster_path"),
        "overview": str(item.get("overview") or "لا يوجد وصف متوفر حالياً."),
        "kind": media_type,
    }


class CinemaData:
    def __init__(self) -> None:
        self.api_key = os.getenv("TMDB_API_KEY", "").strip()
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Cinema-App/2.0"})

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def fetch(self, endpoint: str, extra_params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        if not self.configured:
            return []
        params: dict[str, Any] = {
            "api_key": self.api_key,
            "language": "ar-SA",
            "page": 1,
        }
        if extra_params:
            params.update(extra_params)
        response = self.session.get(f"{TMDB_BASE_URL}/{endpoint}", params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()
        return payload.get("results", [])

    def load_catalog(self) -> dict[str, list[dict[str, Any]]]:
        movies = [format_item(item, "movie") for item in self.fetch("movie/popular")]
        series = [format_item(item, "series") for item in self.fetch("tv/popular")]
        anime = [
            format_item(item, "anime")
            for item in self.fetch("discover/tv", {"with_genres": 16, "with_original_language": "ja", "sort_by": "popularity.desc"})
        ]
        cartoons = [
            format_item(item, "cartoon")
            for item in self.fetch("discover/tv", {"with_genres": 16, "without_original_language": "ja", "sort_by": "popularity.desc"})
        ]
        return {"movies": movies, "series": series, "anime": anime, "cartoons": cartoons}

    def search(self, query: str) -> list[dict[str, Any]]:
        results = self.fetch("search/multi", {"query": query, "include_adult": False})
        items: list[dict[str, Any]] = []
        for item in results:
            if item.get("media_type") == "movie":
                items.append(format_item(item, "movie"))
            elif item.get("media_type") == "tv":
                original_language = item.get("original_language")
                items.append(format_item(item, "anime" if original_language == "ja" else "series"))
        return items


def main(page: ft.Page) -> None:
    page.title = "سينماي — أفلام ومسلسلات وأنمي"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.AUTO

    data_source = CinemaData()
    catalogs = {key: list(items) for key, items in FALLBACKS.items()}
    current_view = "home"
    search_results: list[dict[str, Any]] = []

    content = ft.Column(
        expand=True,
        spacing=24,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
    status = ft.Text("", color=MUTED, size=12, text_align=ft.TextAlign.RIGHT)

    def item_image(item: dict[str, Any], width: int, height: int) -> ft.Image:
        poster = item.get("poster")
        source = f"{TMDB_IMAGE_URL}{poster}" if poster else f"data:image/png;base64,{placeholder_base64(str(item.get('title', 'سينماي')))}"
        return ft.Image(src=source, width=width, height=height, fit=ft.BoxFit.COVER, border_radius=14)

    def poster_card(item: dict[str, Any]) -> ft.Container:
        return ft.Container(
            width=154,
            bgcolor=SURFACE,
            border_radius=17,
            padding=7,
            on_click=lambda _event, selected=item: open_details(selected),
            content=ft.Column(
                spacing=7,
                controls=[
                    ft.Stack(
                        width=140,
                        height=190,
                        controls=[
                            item_image(item, 140, 190),
                            ft.Container(
                                alignment=ft.Alignment.TOP_LEFT,
                                padding=ft.Padding.all(7),
                                content=ft.Container(
                                    bgcolor="#D9000000",
                                    border_radius=7,
                                    padding=ft.Padding.symmetric(horizontal=7, vertical=4),
                                    content=ft.Text(f"★ {item.get('rating', '—')}", color="#FFD54A", size=11, weight=ft.FontWeight.BOLD),
                                ),
                            ),
                        ],
                    ),
                    ft.Text(str(item.get("title", "بدون عنوان")), color=TEXT, size=13, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, text_align=ft.TextAlign.RIGHT),
                    ft.Text(str(item.get("subtitle", "")), color=MUTED, size=11, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, text_align=ft.TextAlign.RIGHT),
                ],
            ),
        )

    def open_details(item: dict[str, Any]) -> None:
        nonlocal current_view
        current_view = "details"
        content.controls.clear()
        content.controls.extend([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT, tooltip="رجوع", on_click=lambda _event: render_home()),
                    ft.Text("تفاصيل العمل", color=TEXT, size=22, weight=ft.FontWeight.BOLD),
                ],
            ),
            ft.Container(
                bgcolor=SURFACE,
                border_radius=22,
                padding=ft.Padding.all(14),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                    spacing=15,
                    controls=[
                        ft.Container(content=item_image(item, 260, 340), alignment=ft.Alignment.CENTER),
                        ft.Text(str(item.get("title", "بدون عنوان")), color=TEXT, size=26, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
                        ft.Text(f"{item.get('rating', '—')} ★  •  {item.get('subtitle', '')}", color="#FFD54A", size=14, text_align=ft.TextAlign.RIGHT),
                        ft.Text(str(item.get("overview", "لا يوجد وصف متوفر حالياً.")), color="#D5D9E0", size=15, text_align=ft.TextAlign.RIGHT),
                        ft.FilledButton(
                            "شاهد الآن",
                            icon=ft.Icons.PLAY_ARROW,
                            on_click=lambda _event: show_message("تم فتح صفحة المشاهدة — أضف روابط الحلقات من مصدر المحتوى."),
                            style=ft.ButtonStyle(bgcolor=ACCENT, color=TEXT),
                        ),
                    ],
                ),
            ),
        ])
        page.update()

    def show_message(message: str) -> None:
        status.value = message
        page.update()

    def category_section(title: str, emoji: str, key: str) -> ft.Column:
        items = catalogs.get(key, [])
        return ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.TextButton("عرض الكل", on_click=lambda _event, category=key: open_category(category), style=ft.ButtonStyle(color=ACCENT)),
                        ft.Text(f"{emoji}  {title}", color=TEXT, size=21, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
                    ],
                ),
                ft.Row(controls=[poster_card(item) for item in items[:10]], spacing=12, scroll=ft.ScrollMode.AUTO),
            ],
        )

    def hero() -> ft.Container:
        featured = (catalogs.get("anime") or catalogs.get("movies") or [])[0]
        background = featured.get("backdrop") or featured.get("poster")
        source = f"{TMDB_IMAGE_URL}{background}" if background else f"data:image/png;base64,{placeholder_base64(str(featured.get('title', 'سينماي')))}"
        return ft.Container(
            height=300,
            border_radius=24,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Image(src=source, expand=True, fit=ft.BoxFit.COVER),
                    ft.Container(expand=True, bgcolor="#C407090D"),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.only(left=20, right=20, top=30, bottom=22),
                        alignment=ft.Alignment.BOTTOM_RIGHT,
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.END,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=9,
                            controls=[
                                ft.Text(str(featured.get("title", "اكتشف عالمك القادم")), color=TEXT, size=26, weight=ft.FontWeight.BOLD, max_lines=2, text_align=ft.TextAlign.RIGHT),
                                ft.Text(f"{featured.get('rating', '—')} ★  •  {featured.get('subtitle', 'أفلام وأنمي')}", color="#E4E7EC", size=14, text_align=ft.TextAlign.RIGHT),
                                ft.FilledButton("شاهد الآن", icon=ft.Icons.PLAY_ARROW, on_click=lambda _event: open_details(featured), style=ft.ButtonStyle(bgcolor=ACCENT, color=TEXT)),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def render_home() -> None:
        nonlocal current_view, search_results
        current_view = "home"
        search_results = []
        content.controls.clear()
        content.controls.extend([
            hero(),
            category_section("الأكثر مشاهدة", "🔥", "movies"),
            category_section("أفضل المسلسلات", "📺", "series"),
            category_section("أفضل أنمي", "⚡", "anime"),
            category_section("أفضل كرتون", "🎨", "cartoons"),
        ])
        page.update()

    def open_category(key: str) -> None:
        nonlocal current_view
        current_view = key
        labels = {"movies": "الأفلام", "series": "المسلسلات", "anime": "الأنمي", "cartoons": "الكرتون"}
        content.controls.clear()
        content.controls.extend([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT, tooltip="رجوع", on_click=lambda _event: render_home()),
                    ft.Text(labels.get(key, "المحتوى"), color=TEXT, size=26, weight=ft.FontWeight.BOLD),
                ],
            ),
            ft.Row(wrap=True, spacing=12, run_spacing=14, controls=[poster_card(item) for item in catalogs.get(key, [])]),
        ])
        page.update()

    def search_local(query: str) -> list[dict[str, Any]]:
        query_lower = query.lower()
        all_items = [item for items in catalogs.values() for item in items]
        return [item for item in all_items if query_lower in str(item.get("title", "")).lower()]

    def perform_search(_event: ft.ControlEvent | None = None) -> None:
        nonlocal search_results, current_view
        query = (search_field.value or "").strip()
        if not query:
            render_home()
            return
        current_view = "search"
        try:
            search_results = data_source.search(query) if data_source.configured else search_local(query)
            status.value = f"نتائج البحث عن: {query}"
        except requests.RequestException as error:
            search_results = search_local(query)
            status.value = f"تعذر البحث الآن، هذه النتائج المحلية: {error}"
        content.controls.clear()
        content.controls.extend([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT, tooltip="رجوع", on_click=lambda _event: render_home()),
                    ft.Text("نتائج البحث", color=TEXT, size=25, weight=ft.FontWeight.BOLD),
                ],
            ),
            ft.Text(f"{len(search_results)} نتيجة", color=MUTED, size=13, text_align=ft.TextAlign.RIGHT),
            ft.Row(wrap=True, spacing=12, run_spacing=14, controls=[poster_card(item) for item in search_results] or [ft.Text("لم نجد نتائج بهذا الاسم.", color=MUTED, size=16)]),
        ])
        page.update()

    def load_from_tmdb(_event: ft.ControlEvent | None = None) -> None:
        if not data_source.configured:
            show_message("أضف TMDB_API_KEY إلى Secrets لجلب الأفلام والمسلسلات والأنمي الحقيقية.")
            return
        status.value = "جارٍ تحديث المحتوى..."
        page.update()
        try:
            fresh = data_source.load_catalog()
            for key, items in fresh.items():
                if items:
                    catalogs[key] = items
            status.value = "تم تحديث الأفلام والمسلسلات والأنمي والكرتون."
            render_home()
        except (requests.RequestException, ValueError, KeyError) as error:
            status.value = f"تعذر تحديث المحتوى، تم إبقاء البيانات الحالية: {error}"
            page.update()

    search_field = ft.TextField(
        hint_text="ابحث عن فيلم أو مسلسل أو أنمي",
        prefix_icon=ft.Icons.SEARCH,
        filled=True,
        bgcolor=SURFACE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ACCENT,
        color=TEXT,
        hint_style=ft.TextStyle(color=MUTED),
        border_radius=24,
        height=48,
        expand=True,
        on_submit=perform_search,
    )

    top_bar = ft.Row(
        spacing=10,
        controls=[
            ft.IconButton(icon=ft.Icons.REFRESH, tooltip="تحديث المحتوى", icon_color=MUTED, on_click=load_from_tmdb),
            ft.Container(expand=True, content=search_field),
            ft.Text("سينماي", color=ACCENT, size=24, weight=ft.FontWeight.BOLD),
        ],
    )

    page.add(
        ft.Container(
            expand=True,
            padding=ft.Padding.only(left=16, right=16, top=18, bottom=20),
            content=ft.Column(expand=True, spacing=10, controls=[top_bar, status, content]),
        )
    )
    render_home()


if __name__ == "__main__":
    ft.run(main, host="0.0.0.0", port=5000, view=ft.AppView.WEB_BROWSER)

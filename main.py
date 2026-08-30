"""واجهة أفلام ومسلسلات وأنمي بواجهة موبايل قابلة للتمرير."""

from __future__ import annotations

import base64
import os
from io import BytesIO
from typing import Any

import flet as ft
import requests
from PIL import Image, ImageDraw

try:
    from app_config import TMDB_API_KEY as BUNDLED_TMDB_API_KEY
except ImportError:
    BUNDLED_TMDB_API_KEY = ""

try:
    import flet_video as ftv
except ImportError:
    ftv = None


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w780"
BACKGROUND = "#07090D"
SURFACE = "#11151D"
SURFACE_LIGHT = "#1B222D"
TEXT = "#F7F8FA"
MUTED = "#AAB2BF"
ACCENT = "#F20D22"
ACCENT_DARK = "#7D0A18"
MAX_CATEGORY_PAGES = 3
MAX_SEARCH_PAGES = 5


CATEGORY_LABELS = {
    "movie": "فيلم",
    "series": "مسلسل",
    "anime": "أنمي",
    "cartoon": "كرتون",
}


FALLBACKS: dict[str, list[dict[str, Any]]] = {
    "movies": [
        {"title": "بين النجوم", "subtitle": "فيلم • 2014", "rating": "8.7", "poster": "/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg", "overview": "رحلة فضائية ملحمية لإنقاذ مستقبل البشرية.", "kind": "movie"},
        {"title": "فارس الظلام", "subtitle": "فيلم • 2008", "rating": "9.0", "poster": "/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "overview": "مواجهة أسطورية بين باتمان وأخطر أعدائه.", "kind": "movie"},
        {"title": "استهلال", "subtitle": "فيلم • 2010", "rating": "8.8", "poster": "/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg", "overview": "لص محترف يدخل إلى أحلام الآخرين.", "kind": "movie"},
        {"title": "أوبنهايمر", "subtitle": "فيلم • 2023", "rating": "8.6", "poster": "/8Gxv8gSFCU0XGDykEGv7zR1n2ua.jpg", "overview": "قصة العالم الذي غيّر مسار التاريخ.", "kind": "movie"},
        {"title": "المصفوفة", "subtitle": "فيلم • 1999", "rating": "8.7", "poster": "/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg", "overview": "اكتشاف الحقيقة خلف العالم الذي نعيش فيه.", "kind": "movie"},
    ],
    "series": [
        {"title": "صراع العروش", "subtitle": "مسلسل • 2011", "rating": "8.5", "poster": "/1XS1oqL89opfnbLl8WnZlJg1Z1e.jpg", "overview": "صراع عائلات وممالك على العرش الحديدي.", "kind": "series"},
        {"title": "بريكنغ باد", "subtitle": "مسلسل • 2008", "rating": "9.5", "poster": "/ztkUQFLlC19CCMYHW9o1zWhJRN2.jpg", "overview": "مدرس كيمياء يدخل عالم الجريمة.", "kind": "series"},
        {"title": "بيكي بلايندرز", "subtitle": "مسلسل • 2013", "rating": "8.6", "poster": "/vUUqzWa2LnHIVqkaKVlVGkVcZIW.jpg", "overview": "عائلة نافذة تبني إمبراطوريتها في برمنغهام.", "kind": "series"},
        {"title": "دارك", "subtitle": "مسلسل • 2017", "rating": "8.7", "poster": "/apbrbWs8M9lyOpJYU5WXrpFbk1Z.jpg", "overview": "اختفاء طفل يكشف أسرارًا تمتد عبر الزمن.", "kind": "series"},
    ],
    "anime": [
        {"title": "هجوم العمالقة", "subtitle": "أنمي • 2013", "rating": "9.1", "poster": "/hTP1DtLGHm8hJni3l2pC6dH1YxF.jpg", "overview": "البشرية تقاتل من أجل البقاء خلف الأسوار.", "kind": "anime"},
        {"title": "قاتل الشياطين", "subtitle": "أنمي • 2019", "rating": "8.6", "poster": "/xUfRZu2mi8jH6SzfH7wYdM7kZ0A.jpg", "overview": "رحلة تانجيرو لإنقاذ أخته ومواجهة الشياطين.", "kind": "anime"},
        {"title": "ون بيس", "subtitle": "أنمي • 1999", "rating": "8.7", "poster": "/fcXdJlbSdUEeMSJFsXKsznGwwok.jpg", "overview": "مغامرة القراصنة بحثًا عن الكنز الأسطوري.", "kind": "anime"},
    ],
    "cartoons": [
        {"title": "حكاية لعبة", "subtitle": "كرتون • 1995", "rating": "8.3", "poster": "/uXDfjJbdP4ijW5hWSBrPrlKpxab.jpg", "overview": "لعب الأطفال تعيش مغامراتها عندما يغيب أصحابها.", "kind": "cartoon"},
        {"title": "شرِك", "subtitle": "كرتون • 2001", "rating": "7.9", "poster": "/iB64vpL3dIObOtMZgX3RqdVdQDc.jpg", "overview": "غول طيب يخوض مغامرة غير متوقعة.", "kind": "cartoon"},
        {"title": "البحث عن نيمو", "subtitle": "كرتون • 2003", "rating": "8.2", "poster": "/eHuGQ10FUzK1mdOY69wF5pGgEf5.jpg", "overview": "رحلة أب عبر المحيط للعثور على ابنه.", "kind": "cartoon"},
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
        "streams": list(item.get("streams") or []),
    }


class CinemaData:
    def __init__(self) -> None:
        # The APK receives app_config.py during CI; local/web runs can use an env var.
        self.api_key = (os.getenv("TMDB_API_KEY", "").strip() or BUNDLED_TMDB_API_KEY.strip())
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Cinema-App/2.0"})

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def fetch(self, endpoint: str, extra_params: dict[str, Any] | None = None, page: int = 1) -> list[dict[str, Any]]:
        if not self.configured:
            return []
        params: dict[str, Any] = {
            "api_key": self.api_key,
            "language": "ar-SA",
            "page": page,
        }
        if extra_params:
            params.update(extra_params)
        response = self.session.get(f"{TMDB_BASE_URL}/{endpoint}", params=params, timeout=12)
        response.raise_for_status()
        payload = response.json()
        return payload.get("results", [])

    def fetch_category(self, key: str, page: int = 1) -> list[dict[str, Any]]:
        if key == "movies":
            return [format_item(item, "movie") for item in self.fetch("movie/popular", page=page)]
        if key == "series":
            return [format_item(item, "series") for item in self.fetch("tv/popular", page=page)]
        if key == "anime":
            return [
                format_item(item, "anime")
                for item in self.fetch(
                    "discover/tv",
                    {"with_genres": 16, "with_original_language": "ja", "sort_by": "popularity.desc"},
                    page=page,
                )
            ]
        if key == "cartoons":
            return [
                format_item(item, "cartoon")
                for item in self.fetch(
                    "discover/tv",
                    {"with_genres": 16, "without_original_language": "ja", "sort_by": "popularity.desc"},
                    page=page,
                )
            ]
        return []

    def load_catalog(self) -> dict[str, list[dict[str, Any]]]:
        return {key: self.fetch_category(key, page=1) for key in ("movies", "series", "anime", "cartoons")}

    def search(self, query: str, page: int = 1) -> list[dict[str, Any]]:
        results = self.fetch("search/multi", {"query": query, "include_adult": False}, page=page)
        items: list[dict[str, Any]] = []
        for item in results:
            if item.get("media_type") == "movie":
                items.append(format_item(item, "movie"))
            elif item.get("media_type") == "tv":
                original_language = item.get("original_language")
                items.append(format_item(item, "anime" if original_language == "ja" else "series"))
        return items


def main(page: ft.Page) -> None:
    page.title = "Palestine Movie — أفلام ومسلسلات وأنمي"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.spacing = 0
    page.scroll = ft.ScrollMode.AUTO

    data_source = CinemaData()
    catalogs = {key: list(items) for key, items in FALLBACKS.items()}
    category_pages = {key: 1 for key in FALLBACKS}
    category_loading: set[str] = set()
    current_view = "home"
    search_results: list[dict[str, Any]] = []
    search_query = ""
    search_page = 1
    search_loading = False
    search_has_more = False

    content = ft.Column(
        expand=True,
        spacing=24,
        scroll=ft.ScrollMode.AUTO,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
    )
    status = ft.Text("", color=MUTED, size=12, text_align=ft.TextAlign.RIGHT)

    def item_image(item: dict[str, Any], width: int, height: int) -> ft.Image:
        poster = item.get("poster")
        if poster and str(poster).startswith(("http://", "https://")):
            source = str(poster)
        elif poster:
            source = f"{TMDB_IMAGE_URL}{poster}"
        else:
            source = f"data:image/png;base64,{placeholder_base64(str(item.get('title', 'محتوى')))}"
        return ft.Image(src=source, width=width, height=height, fit=ft.BoxFit.COVER, border_radius=14)

    def poster_card(item: dict[str, Any]) -> ft.Container:
        return ft.Container(
            width=168,
            bgcolor=SURFACE,
            border_radius=17,
            padding=7,
            on_click=lambda _event, selected=item: open_details(selected),
            content=ft.Column(
                spacing=7,
                controls=[
                    ft.Stack(
                        width=154,
                        height=212,
                        controls=[
                            item_image(item, 154, 212),
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

    def category_chip(label: str, key: str | None = None, emoji: str = "") -> ft.Container:
        is_active = (key is None and current_view == "home") or key == current_view
        return ft.Container(
            bgcolor=ACCENT if is_active else SURFACE,
            border_radius=24,
            padding=ft.Padding.symmetric(horizontal=18, vertical=10),
            on_click=(lambda _event, category=key: open_category(category)) if key else (lambda _event: render_home()),
            content=ft.Text(
                f"{emoji}  {label}".strip(),
                color=TEXT,
                size=14,
                weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                text_align=ft.TextAlign.CENTER,
            ),
        )

    def category_tabs() -> ft.Row:
        return ft.Row(
            spacing=10,
            scroll=ft.ScrollMode.AUTO,
            controls=[
                category_chip("الكل"),
                category_chip("أنمي", "anime", "⚡"),
                category_chip("مسلسلات", "series", "📺"),
                category_chip("أفلام", "movies", "🎬"),
                category_chip("كرتون", "cartoons", "🎨"),
            ],
        )

    def valid_stream_url(value: str) -> bool:
        url = value.strip().lower()
        return url.startswith(("https://", "http://")) and len(url) > 12

    def open_download_link(stream: dict[str, Any]) -> None:
        url = str(stream.get("url") or "").strip()
        if not valid_stream_url(url):
            show_message("رابط التنزيل غير صالح.")
            return
        page.launch_url(url)
        show_message("تم فتح رابط التنزيل المرخّص.")

    def show_player(item: dict[str, Any], stream: dict[str, Any]) -> None:
        url = str(stream.get("url") or "").strip()
        if not valid_stream_url(url):
            show_message("أضف رابط بث مرخّص بصيغة MP4 أو M3U8.")
            return

        if ftv is not None:
            player: ft.Control = ftv.Video(
                expand=True,
                autoplay=True,
                playlist=[ftv.VideoMedia(url)],
            )
        else:
            player = ft.Container(
                expand=True,
                alignment=ft.Alignment.CENTER,
                bgcolor="#050608",
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.Icons.PLAY_CIRCLE_OUTLINE, color=ACCENT, size=52),
                        ft.Text("ثبّت flet-video لتفعيل المشغل داخل التطبيق.", color=TEXT, text_align=ft.TextAlign.CENTER),
                        ft.Text("الرابط محفوظ كمصدر مرخّص ويمكن فتحه خارجيًا.", color=MUTED, size=12, text_align=ft.TextAlign.CENTER),
                    ],
                ),
            )

        content.controls.clear()
        content.controls.extend([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT, tooltip="رجوع", on_click=lambda _event: open_details(item)),
                    ft.Text("المشغل", color=TEXT, size=24, weight=ft.FontWeight.BOLD),
                ],
            ),
            ft.Container(
                height=310,
                bgcolor="#050608",
                border_radius=20,
                clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                content=player,
            ),
            ft.Text(
                f"{item.get('title', 'المحتوى')}  •  {stream.get('quality', 'جودة تلقائية')}  •  {stream.get('server', 'مصدر مرخّص')}",
                color=TEXT,
                size=16,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.RIGHT,
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.FilledButton(
                        "📥 تنزيل",
                        on_click=lambda _event, selected=stream: open_download_link(selected),
                        style=ft.ButtonStyle(bgcolor=ACCENT, color=TEXT),
                    ),
                    ft.OutlinedButton(
                        "اختيار جودة أخرى",
                        on_click=lambda _event: open_details(item),
                    ),
                ],
            ),
        ])
        page.update()

    def stream_panel(item: dict[str, Any]) -> ft.Column:
        streams = [
            stream for stream in item.get("streams", [])
            if isinstance(stream, dict) and valid_stream_url(str(stream.get("url") or ""))
        ]
        rows: list[ft.Control] = []
        if streams:
            rows.append(ft.Text("اختر السيرفر والجودة", color=TEXT, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT))
            for stream in streams:
                rows.append(
                    ft.Container(
                        bgcolor=SURFACE_LIGHT,
                        border_radius=14,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                        content=ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Column(
                                    spacing=3,
                                    controls=[
                                        ft.Text(str(stream.get("quality") or "جودة تلقائية"), color="#FFD54A", weight=ft.FontWeight.BOLD),
                                        ft.Text(str(stream.get("server") or "مصدر مرخّص"), color=MUTED, size=12),
                                    ],
                                ),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.FilledButton(
                                            "▶️ مشاهدة",
                                            on_click=lambda _event, selected=stream: show_player(item, selected),
                                            style=ft.ButtonStyle(bgcolor=ACCENT, color=TEXT),
                                        ),
                                        ft.OutlinedButton(
                                            "📥 تنزيل",
                                            on_click=lambda _event, selected=stream: open_download_link(selected),
                                        ),
                                    ],
                                ),
                            ],
                        ),
                    )
                )
        else:
            rows.append(ft.Text("لا يوجد مصدر بث مرخّص لهذا العمل بعد.", color=MUTED, text_align=ft.TextAlign.RIGHT))

        custom_url = ft.TextField(
            label="رابط بث مرخّص MP4 أو M3U8",
            hint_text="https://example.com/video.m3u8",
            text_align=ft.TextAlign.RIGHT,
            border_radius=12,
            border_color=SURFACE_LIGHT,
            focused_border_color=ACCENT,
        )
        custom_quality = ft.TextField(
            label="الجودة",
            hint_text="مثال: 720p",
            width=130,
            text_align=ft.TextAlign.CENTER,
            border_radius=12,
            border_color=SURFACE_LIGHT,
            focused_border_color=ACCENT,
        )

        def add_custom_stream(_event: ft.ControlEvent) -> None:
            url = (custom_url.value or "").strip()
            if not valid_stream_url(url):
                show_message("أدخل رابط بث مرخّص يبدأ بـ https:// أو http://")
                return
            item.setdefault("streams", []).append({
                "server": "مصدر مخصص",
                "quality": (custom_quality.value or "Auto").strip(),
                "url": url,
                "format": "m3u8" if ".m3u8" in url.lower() else "mp4",
            })
            open_details(item)

        rows.extend([
            ft.Divider(color=SURFACE_LIGHT, height=18),
            ft.Text("إضافة مصدر مخصص مرخّص", color=TEXT, size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
            ft.Row(
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    custom_quality,
                    ft.Container(expand=True, content=custom_url),
                ],
            ),
            ft.FilledButton(
                "إضافة المصدر",
                icon=ft.Icons.ADD_LINK,
                on_click=add_custom_stream,
                style=ft.ButtonStyle(bgcolor=ACCENT_DARK, color=TEXT),
            ),
        ])
        return ft.Column(spacing=10, controls=rows)

    def load_more_category(key: str, event: ft.OnScrollEvent) -> None:
        if (
            not data_source.configured
            or key in category_loading
            or category_pages.get(key, 1) >= MAX_CATEGORY_PAGES
        ):
            return
        pixels = float(getattr(event, "pixels", 0) or 0)
        max_extent = float(getattr(event, "max_scroll_extent", 0) or 0)
        if max_extent <= 0 or pixels < max_extent - 100:
            return

        category_loading.add(key)
        next_page = category_pages.get(key, 1) + 1
        try:
            more_items = data_source.fetch_category(key, page=next_page)
            existing_ids = {str(item.get("id")) for item in catalogs.get(key, [])}
            new_items = [item for item in more_items if str(item.get("id")) not in existing_ids]
            if new_items:
                catalogs[key].extend(new_items)
                category_pages[key] = next_page
                row = getattr(event, "control", None)
                if row is not None and hasattr(row, "controls"):
                    row.controls.extend(poster_card(item) for item in new_items)
                    row.update()
                else:
                    render_home()
            elif next_page >= MAX_CATEGORY_PAGES:
                category_pages[key] = next_page
        except (requests.RequestException, ValueError, KeyError) as error:
            status.value = f"تعذر تحميل المزيد: {error}"
            page.update()
        finally:
            category_loading.discard(key)

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
                        stream_panel(item),
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
                ft.Row(
                    controls=[poster_card(item) for item in items],
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    on_scroll=lambda event, category=key: load_more_category(category, event),
                ),
            ],
        )

    def hero() -> ft.Container:
        featured = (catalogs.get("movies") or catalogs.get("series") or catalogs.get("anime") or [])[0]
        background = featured.get("backdrop") or featured.get("poster")
        source = f"{TMDB_IMAGE_URL}{background}" if background else f"data:image/png;base64,{placeholder_base64(str(featured.get('title', 'محتوى')))}"
        return ft.Container(
            height=350,
            border_radius=24,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack(
                expand=True,
                controls=[
                    ft.Image(src=source, expand=True, fit=ft.BoxFit.COVER),
                    ft.Container(expand=True, bgcolor="#C407090D"),
                    ft.Container(
                        expand=True,
                        padding=ft.Padding.only(left=20, right=20, top=28, bottom=24),
                        alignment=ft.Alignment.BOTTOM_RIGHT,
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.END,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=9,
                            controls=[
                                 ft.Text("Palestine Movie 🇵🇸", color=ACCENT, size=14, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
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
            category_tabs(),
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

    def render_search_results() -> None:
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
            ft.Row(
                wrap=True,
                spacing=12,
                run_spacing=14,
                controls=[poster_card(item) for item in search_results]
                or [ft.Text("لم نجد نتائج بهذا الاسم.", color=MUTED, size=16)],
            ),
            ft.Text(
                "مرر للأسفل لتحميل المزيد" if search_has_more else "تم عرض النتائج المتاحة",
                color=MUTED,
                size=12,
                text_align=ft.TextAlign.CENTER,
            ),
        ])
        page.update()

    def load_more_search(event: ft.OnScrollEvent) -> None:
        nonlocal search_page, search_loading, search_has_more, search_results
        if (
            current_view != "search"
            or not data_source.configured
            or search_loading
            or not search_has_more
            or search_page >= MAX_SEARCH_PAGES
        ):
            return
        pixels = float(getattr(event, "pixels", 0) or 0)
        max_extent = float(getattr(event, "max_scroll_extent", 0) or 0)
        if max_extent <= 0 or pixels < max_extent - 120:
            return

        search_loading = True
        next_page = search_page + 1
        try:
            more_results = data_source.search(search_query, page=next_page)
            existing_ids = {str(item.get("id")) for item in search_results}
            search_results.extend(
                item for item in more_results if str(item.get("id")) not in existing_ids
            )
            search_page = next_page
            search_has_more = len(more_results) >= 20 and search_page < MAX_SEARCH_PAGES
            render_search_results()
        except (requests.RequestException, ValueError, KeyError) as error:
            status.value = f"تعذر تحميل نتائج إضافية: {error}"
            page.update()
        finally:
            search_loading = False

    def perform_search(_event: ft.ControlEvent | None = None) -> None:
        nonlocal search_results, current_view, search_query, search_page, search_has_more
        query = (search_field.value or "").strip()
        if not query:
            render_home()
            return
        current_view = "search"
        search_query = query
        search_page = 1
        try:
            search_results = data_source.search(query, page=1) if data_source.configured else search_local(query)
            search_has_more = data_source.configured and len(search_results) >= 20
            status.value = f"نتائج البحث عن: {query}"
        except requests.RequestException as error:
            search_results = search_local(query)
            search_has_more = False
            status.value = f"تعذر البحث الآن، هذه النتائج المحلية: {error}"
        render_search_results()

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
                    category_pages[key] = 1
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
            ft.Text("Palestine Movie", color=ACCENT, size=22, weight=ft.FontWeight.BOLD),
        ],
    )

    page.navigation_bar = ft.NavigationBar(
        bgcolor="#21151D",
        indicator_color=ACCENT_DARK,
        selected_index=0,
        on_change=lambda event: (
            render_home()
            if event.control.selected_index == 0
            else show_message("القسم قيد التجهيز — ستتم إضافة هذه الصفحة قريباً.")
        ),
        destinations=[
            ft.NavigationBarDestination(icon=ft.Icons.HOME_OUTLINED, selected_icon=ft.Icons.HOME, label="الرئيسية"),
            ft.NavigationBarDestination(icon=ft.Icons.SEARCH, label="بحث"),
            ft.NavigationBarDestination(icon=ft.Icons.DOWNLOAD_OUTLINED, label="التنزيلات"),
            ft.NavigationBarDestination(icon=ft.Icons.FAVORITE_BORDER, label="المفضلة"),
        ],
    )

    page.add(
        ft.Container(
            expand=True,
            padding=ft.Padding.only(left=16, right=16, top=18, bottom=20),
            content=ft.Column(expand=True, spacing=10, controls=[top_bar, status, content]),
        )
    )
    content.on_scroll = load_more_search
    render_home()


if __name__ == "__main__":
    ft.run(main, host="0.0.0.0", port=5000, view=ft.AppView.WEB_BROWSER)

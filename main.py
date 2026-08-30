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
MAX_CATEGORY_PAGES = 100
MAX_SEARCH_PAGES = 100
PAGE_SIZE = 20
EPISODE_BATCH_SIZE = 20
MOCK_VIDEO_URL = "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4"


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


def get_content_episodes(media_title: str) -> list[dict[str, str | int]]:
    """Mock hook for the user's authorized episode catalog.

    Replace only this function with the legal service that owns the episodes.
    The UI expects an episode_id and a display title for every returned item.
    """
    title_key = str(media_title or "content").strip().replace(" ", "-")[:48] or "content"
    return [
        {
            "episode_id": f"demo-{title_key}-episode-{number}",
            "episode_number": number,
            "title": f"الحلقة {number}",
            "subtitle": "حلقة تجريبية • 42 دقيقة",
        }
        for number in range(1, 7)
    ]


def get_episode_stream_sources(episode_id: str, quality: str) -> dict[str, str]:
    """Mock hook for authorized playback/download sources.

    Replace the demo URL with a signed URL from the user's legal cloud
    provider. The frontend never scrapes, proxies, or bypasses source rules.
    """
    quality_details = {
        "1080p": ("FHD", "380 MB"),
        "720p": ("HD", "190 MB"),
        "480p": ("SD", "85 MB"),
    }
    normalized_quality = quality if quality in quality_details else "720p"
    label, size = quality_details[normalized_quality]
    return {
        "episode_id": str(episode_id),
        "quality": normalized_quality,
        "label": label,
        "size": size,
        "watch_url": MOCK_VIDEO_URL,
        "download_url": MOCK_VIDEO_URL,
        "format": "mp4",
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

    def fetch_details(self, item: dict[str, Any]) -> dict[str, Any]:
        """Fetch the selected title's full TMDB record, including seasons."""
        media_id = item.get("id")
        if not media_id or not self.configured:
            return {}
        endpoint = f"movie/{media_id}" if item.get("kind") == "movie" else f"tv/{media_id}"
        response = self.session.get(
            f"{TMDB_BASE_URL}/{endpoint}",
            params={"api_key": self.api_key, "language": "ar-SA"},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        return payload if isinstance(payload, dict) else {}

    def fetch_season_episodes(self, media_id: Any, season_number: int) -> list[dict[str, Any]]:
        """Fetch one TV season from TMDB; the UI reveals it in batches."""
        if not media_id or not self.configured:
            return []
        response = self.session.get(
            f"{TMDB_BASE_URL}/tv/{media_id}/season/{season_number}",
            params={"api_key": self.api_key, "language": "ar-SA"},
            timeout=12,
        )
        response.raise_for_status()
        payload = response.json()
        raw_episodes = payload.get("episodes", []) if isinstance(payload, dict) else []
        entries: list[dict[str, Any]] = []
        for episode in raw_episodes:
            number = episode.get("episode_number")
            if number is None:
                continue
            entries.append({
                "episode_id": str(episode.get("id") or f"{media_id}-s{season_number}-e{number}"),
                "episode_number": number,
                "title": str(episode.get("name") or f"الحلقة {number}"),
                "subtitle": f"الموسم {season_number} • الحلقة {number} • {episode.get('runtime') or 42} دقيقة",
            })
        return entries


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

    def open_download_link(source: dict[str, Any]) -> None:
        url = str(source.get("download_url") or "").strip()
        if not valid_stream_url(url):
            show_message("رابط التنزيل غير صالح.")
            return
        page.launch_url(url)
        show_message(f"بدأ تنزيل {source.get('quality', 'الجودة المختارة')}.")

    def show_player(item: dict[str, Any], source: dict[str, Any], entry: dict[str, Any]) -> None:
        url = str(source.get("watch_url") or "").strip()
        if not valid_stream_url(url):
            show_message("مصدر التشغيل غير متاح حاليًا.")
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
                f"{item.get('title', 'المحتوى')}  •  {entry.get('title', 'الحلقة')}  •  {source.get('quality', 'جودة تلقائية')}",
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
                        on_click=lambda _event, selected=source: open_download_link(selected),
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

    def show_quality_dialog(item: dict[str, Any], entry: dict[str, Any], action: str) -> None:
        def choose_quality(quality: str) -> None:
            page.pop_dialog()
            source = get_episode_stream_sources(str(entry.get("episode_id", "demo")), quality)
            if action == "watch":
                show_player(item, source, entry)
            else:
                open_download_link(source)

        quality_buttons: list[ft.Control] = []
        for quality, label, size in (
            ("1080p", "FHD", "380 MB"),
            ("720p", "HD", "190 MB"),
            ("480p", "SD", "85 MB"),
        ):
            quality_buttons.append(
                ft.Container(
                    bgcolor=SURFACE_LIGHT,
                    border_radius=16,
                    padding=ft.Padding.symmetric(horizontal=14, vertical=12),
                    on_click=lambda _event, selected=quality: choose_quality(selected),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(size, color=MUTED, size=13),
                            ft.Column(
                                spacing=2,
                                horizontal_alignment=ft.CrossAxisAlignment.END,
                                controls=[
                                    ft.Text(f"{quality} ({label})", color=TEXT, size=16, weight=ft.FontWeight.BOLD),
                                    ft.Text("جودة متاحة للمشاهدة والتنزيل", color=MUTED, size=11),
                                ],
                            ),
                        ],
                    ),
                )
            )

        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=SURFACE,
            title=ft.Text(
                "اختر الجودة",
                color=TEXT,
                text_align=ft.TextAlign.RIGHT,
                weight=ft.FontWeight.BOLD,
            ),
            content=ft.Column(
                tight=True,
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
                controls=[
                    ft.Text(
                        f"{'مشاهدة' if action == 'watch' else 'تحميل'} • {entry.get('title', 'المحتوى')}",
                        color=MUTED,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                    *quality_buttons,
                ],
            ),
            actions=[
                ft.TextButton("إلغاء", on_click=lambda _event: page.pop_dialog()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.show_dialog(dialog)

    def content_panel(
        item: dict[str, Any],
        initial_entries: list[dict[str, Any]],
        season_numbers: list[int] | None = None,
    ) -> ft.Column:
        is_serial = str(item.get("kind")) in {"series", "anime"}
        episode_entries = list(initial_entries)
        visible_count = min(EPISODE_BATCH_SIZE, len(episode_entries))
        season_numbers = season_numbers or []
        season_dropdown: ft.Dropdown | None = None

        def content_row(entry: dict[str, Any]) -> ft.Container:
            return ft.Container(
                bgcolor=SURFACE_LIGHT,
                border_radius=14,
                padding=ft.Padding.symmetric(horizontal=12, vertical=10),
                content=ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=3,
                            expand=True,
                            controls=[
                                ft.Text(
                                    str(entry.get("title", "المحتوى")),
                                    color=TEXT,
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                                ft.Text(
                                    str(entry.get("subtitle", "")),
                                    color=MUTED,
                                    size=12,
                                    text_align=ft.TextAlign.RIGHT,
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.PLAY_CIRCLE_FILLED,
                                    icon_color=ACCENT,
                                    icon_size=30,
                                    tooltip="▶️ المشاهدة",
                                    on_click=lambda _event, selected=entry: show_quality_dialog(item, selected, "watch"),
                                ),
                                ft.IconButton(
                                    icon=ft.Icons.DOWNLOAD_ROUNDED,
                                    icon_color=TEXT,
                                    icon_size=28,
                                    tooltip="📥 التحميل",
                                    on_click=lambda _event, selected=entry: show_quality_dialog(item, selected, "download"),
                                ),
                            ],
                        ),
                    ],
                ),
            )

        episode_list = ft.ListView(
            height=520,
            spacing=10,
            padding=ft.Padding.only(top=4, bottom=8),
        )

        def render_episode_batch(
            _event: ft.OnScrollEvent | None = None,
            update_control: bool = True,
        ) -> None:
            nonlocal visible_count
            if _event is not None:
                pixels = float(getattr(_event, "pixels", 0) or 0)
                extent = float(getattr(_event, "max_scroll_extent", 0) or 0)
                if extent > 0 and pixels < extent - 100:
                    return
                if visible_count < len(episode_entries):
                    visible_count = min(visible_count + EPISODE_BATCH_SIZE, len(episode_entries))
            episode_list.controls = [content_row(entry) for entry in episode_entries[:visible_count]]
            if visible_count < len(episode_entries):
                episode_list.controls.append(
                    ft.Text("مرر للأسفل لتحميل حلقات إضافية…", color=MUTED, size=12, text_align=ft.TextAlign.CENTER)
                )
            if update_control:
                episode_list.update()

        def change_season(event: ft.ControlEvent) -> None:
            nonlocal episode_entries, visible_count
            if not season_dropdown or not season_dropdown.value:
                return
            try:
                status.value = "جارٍ تحميل حلقات الموسم..."
                page.update()
                episode_entries = data_source.fetch_season_episodes(item.get("id"), int(season_dropdown.value))
                if not episode_entries:
                    status.value = "لا توجد حلقات متاحة لهذا الموسم."
                else:
                    status.value = f"تم تحميل {len(episode_entries)} حلقة — مرر للأسفل للمزيد."
                visible_count = min(EPISODE_BATCH_SIZE, len(episode_entries))
                render_episode_batch()
                page.update()
            except (requests.RequestException, ValueError, KeyError) as error:
                status.value = f"تعذر تحميل حلقات الموسم: {error}"
                page.update()

        controls: list[ft.Control] = []
        if is_serial and season_numbers:
            season_dropdown = ft.Dropdown(
                label="اختر الموسم",
                value=str(season_numbers[0]),
                options=[ft.DropdownOption(key=str(number), text=f"الموسم {number}") for number in season_numbers],
                text_align=ft.TextAlign.RIGHT,
                border_radius=12,
                border_color=SURFACE_LIGHT,
                focused_border_color=ACCENT,
                on_change=change_season,
            )
            controls.append(season_dropdown)

        episode_list.on_scroll = render_episode_batch
        render_episode_batch(update_control=False)
        controls.extend([
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text(
                        f"{len(episode_entries)} {'حلقة' if is_serial else 'فيلم'}",
                        color=MUTED,
                        size=12,
                    ),
                    ft.Text(
                        "الحلقات" if is_serial else "الفيلم",
                        color=TEXT,
                        size=18,
                        weight=ft.FontWeight.BOLD,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
            ),
            episode_list,
        ])
        return ft.Column(spacing=10, controls=controls)

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
        is_serial = str(item.get("kind")) in {"series", "anime"}
        detail_entries: list[dict[str, Any]] = []
        season_numbers: list[int] = []

        if is_serial and data_source.configured and item.get("id"):
            try:
                details = data_source.fetch_details(item)
                season_numbers = [
                    int(season.get("season_number"))
                    for season in details.get("seasons", [])
                    if season.get("season_number") is not None and int(season.get("season_number")) > 0
                ]
                if season_numbers:
                    detail_entries = data_source.fetch_season_episodes(item.get("id"), season_numbers[0])
                if details.get("overview"):
                    item["overview"] = details["overview"]
            except (requests.RequestException, ValueError, KeyError) as error:
                status.value = f"تعذر تحميل الحلقات من TMDB: {error}"

        if not detail_entries:
            if is_serial:
                detail_entries = [dict(entry) for entry in get_content_episodes(str(item.get("title", "المحتوى")))]
            else:
                detail_entries = [{
                    "episode_id": f"demo-{item.get('id') or item.get('title') or 'movie'}-movie",
                    "episode_number": 1,
                    "title": "الفيلم الكامل",
                    "subtitle": "فيلم • تشغيل مباشر",
                }]

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
                        content_panel(item, detail_entries, season_numbers),
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
            search_has_more = len(more_results) >= PAGE_SIZE and search_page < MAX_SEARCH_PAGES
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
            search_has_more = data_source.configured and len(search_results) >= PAGE_SIZE
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
    if data_source.configured:
        status.value = "جارٍ تحميل المحتوى من TMDB..."
        page.update()
        page.run_thread(load_from_tmdb)
    else:
        status.value = "أضف TMDB_API_KEY إلى Secrets لعرض الكتالوج الحقيقي."


if __name__ == "__main__":
    ft.run(main, host="0.0.0.0", port=5000, view=ft.AppView.WEB_BROWSER)

"""تطبيق أفلام وأنمي عربي بواجهة Flet داكنة."""

from __future__ import annotations

import base64
import os
from io import BytesIO
from typing import Any

import flet as ft
import requests
from PIL import Image, ImageDraw


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
BACKGROUND = "#090909"
SURFACE = "#151515"
SURFACE_LIGHT = "#222222"
TEXT = "#F5F5F5"
MUTED = "#A6A6A6"
ACCENT = "#E50914"

FALLBACK_MOVIES = [
    {
        "title": "أفلام جديدة",
        "subtitle": "اكتشف أحدث الإصدارات",
        "rating": "—",
        "poster": None,
    },
    {
        "title": "اختيارات اليوم",
        "subtitle": "أعمال تستحق المشاهدة",
        "rating": "—",
        "poster": None,
    },
    {
        "title": "سينما عالمية",
        "subtitle": "قصص من كل مكان",
        "rating": "—",
        "poster": None,
    },
    {
        "title": "ليلة الأفلام",
        "subtitle": "اختر فيلمك التالي",
        "rating": "—",
        "poster": None,
    },
]

FALLBACK_ANIME = [
    {
        "title": "عالم الأنمي",
        "subtitle": "مغامرات لا تنتهي",
        "rating": "—",
        "poster": None,
    },
    {
        "title": "أنمي الأسبوع",
        "subtitle": "ترشيحات محبي الأنمي",
        "rating": "—",
        "poster": None,
    },
    {
        "title": "حلقات جديدة",
        "subtitle": "تابع آخر الأحداث",
        "rating": "—",
        "poster": None,
    },
    {
        "title": "كلاسيكيات الأنمي",
        "subtitle": "قصص لا تُنسى",
        "rating": "—",
        "poster": None,
    },
]


def placeholder_base64(title: str) -> str:
    """ينشئ ملصقاً محلياً بسيطاً كي تعمل الواجهة حتى دون اتصال."""
    image = Image.new("RGB", (320, 460), "#252525")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 300, 320, 460), fill="#3A1015")
    draw.text((20, 350), title[:18], fill="#FFFFFF")

    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)

    return base64.b64encode(buffer.getvalue()).decode("ascii")


def tmdb_title(item: dict[str, Any]) -> str:
    return str(item.get("title") or item.get("name") or "بدون عنوان")


def format_item(
    item: dict[str, Any],
    media_type: str,
) -> dict[str, Any]:
    date = str(
        item.get("release_date")
        or item.get("first_air_date")
        or ""
    )

    year = date[:4] if date else "جديد"
    media_label = "فيلم" if media_type == "movie" else "أنمي"

    return {
        "title": tmdb_title(item),
        "subtitle": f"{media_label} • {year}",
        "rating": f"{float(item.get('vote_average', 0)):.1f}",
        "poster": item.get("poster_path"),
    }


class CinemaData:
    """طبقة صغيرة لجلب بيانات TMDB دون كشف مفتاح الوصول في الكود."""

    def __init__(self) -> None:
        self.api_key = os.getenv("TMDB_API_KEY", "").strip()
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "Cinema-App/1.0"}
        )

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def fetch(
        self,
        endpoint: str,
        extra_params: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not self.configured:
            return []

        params: dict[str, Any] = {
            "api_key": self.api_key,
            "language": "ar-SA",
            "page": 1,
        }

        if extra_params:
            params.update(extra_params)

        response = self.session.get(
            f"{TMDB_BASE_URL}/{endpoint}",
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        payload = response.json()
        return payload.get("results", [])

    def load_catalog(
        self,
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
    ]:
        movies = [
            format_item(item, "movie")
            for item in self.fetch("movie/popular")
        ]

        anime = [
            format_item(item, "tv")
            for item in self.fetch(
                "discover/tv",
                {
                    "with_genres": 16,
                    "with_original_language": "ja",
                    "sort_by": "popularity.desc",
                },
            )
        ]

        return movies, anime


def poster_card(item: dict[str, Any]) -> ft.Container:
    title = str(item["title"])
    poster_path = item.get("poster")

    if poster_path:
        poster = ft.Image(
            src=f"{TMDB_IMAGE_URL}{poster_path}",
            width=158,
            height=214,
            fit=ft.BoxFit.COVER,
            border_radius=10,
        )
    else:
        poster = ft.Image(
            src_base64=placeholder_base64(title),
            width=158,
            height=214,
            fit=ft.BoxFit.COVER,
            border_radius=10,
        )

    return ft.Container(
        width=174,
        bgcolor=SURFACE,
        border_radius=14,
        padding=8,
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Stack(
                    height=214,
                    controls=[
                        poster,
                        ft.Container(
                            alignment=ft.Alignment.BOTTOM_LEFT,
                            padding=10,
                            content=ft.Text(
                                f"★ {item['rating']}",
                                color="#FFFFFF",
                                weight=ft.FontWeight.BOLD,
                                size=12,
                            ),
                        ),
                    ],
                ),
                ft.Text(
                    title,
                    color=TEXT,
                    size=14,
                    weight=ft.FontWeight.BOLD,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    text_align=ft.TextAlign.RIGHT,
                ),
                ft.Text(
                    str(item["subtitle"]),
                    color=MUTED,
                    size=12,
                    max_lines=1,
                    overflow=ft.TextOverflow.ELLIPSIS,
                    text_align=ft.TextAlign.RIGHT,
                ),
            ],
        ),
    )


def catalog_section(
    title: str,
    items: list[dict[str, Any]],
) -> ft.Column:
    return ft.Column(
        spacing=14,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.TextButton(
                        "عرض الكل",
                        style=ft.ButtonStyle(color=ACCENT),
                    ),
                    ft.Text(
                        title,
                        color=TEXT,
                        size=21,
                        weight=ft.FontWeight.BOLD,
                    ),
                ],
            ),
            ft.Row(
                controls=[
                    poster_card(item)
                    for item in items
                ],
                spacing=14,
                scroll=ft.ScrollMode.AUTO,
            ),
        ],
    )


def main(page: ft.Page) -> None:
    page.title = "سينماي — أفلام وأنمي"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.spacing = 0

    data_source = CinemaData()

    movies = list(FALLBACK_MOVIES)
    anime = list(FALLBACK_ANIME)
    current_section = "الرئيسية"

    content = ft.Column(
        expand=True,
        spacing=28,
        scroll=ft.ScrollMode.AUTO,
    )

    navigation = ft.Column(spacing=6)
    status = ft.Text("", color=MUTED, size=12)

    def hero() -> ft.Container:
        return ft.Container(
            height=220,
            border_radius=18,
            padding=28,
            gradient=ft.LinearGradient(
                begin=ft.Alignment.TOP_RIGHT,
                end=ft.Alignment.BOTTOM_LEFT,
                colors=[
                    "#3B1016",
                    "#1A0C0E",
                    "#171717",
                ],
            ),
            content=ft.Column(
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.END,
                spacing=12,
                controls=[
                    ft.Text(
                        "اكتشف عالمك القادم",
                        color=TEXT,
                        size=28,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "أفلام وأنمي مختارة بعناية، في مكان واحد.",
                        color="#D8D8D8",
                        size=15,
                    ),
                    ft.FilledButton(
                        "ابدأ المشاهدة",
                        icon=ft.Icons.PLAY_ARROW,
                        style=ft.ButtonStyle(
                            bgcolor=ACCENT,
                            color=TEXT,
                            shape=ft.RoundedRectangleBorder(
                                radius=9,
                            ),
                        ),
                    ),
                ],
            ),
        )

    def nav_button(
        label: str,
        icon: str,
    ) -> ft.Container:
        return ft.Container(
            border_radius=10,
            bgcolor=(
                ACCENT
                if label == current_section
                else None
            ),
            padding=ft.Padding.symmetric(
                horizontal=14,
                vertical=11,
            ),
            on_click=lambda _event, section=label: (
                render_section(section)
            ),
            content=ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(
                        icon,
                        color=TEXT,
                        size=19,
                    ),
                    ft.Text(
                        label,
                        color=TEXT,
                        size=14,
                    ),
                ],
            ),
        )

    def refresh_navigation() -> None:
        navigation.controls.clear()

        menu_items = [
            ("الرئيسية", ft.Icons.HOME),
            ("الأفلام", ft.Icons.MOVIE),
            ("الأنمي", ft.Icons.LIVE_TV),
            ("المفضلة", ft.Icons.BOOKMARK),
        ]

        for label, icon in menu_items:
            navigation.controls.append(
                nav_button(label, icon)
            )

    def render_section(name: str) -> None:
        nonlocal current_section

        current_section = name
        content.controls.clear()

        if name == "الأفلام":
            content.controls.extend(
                [
                    ft.Text(
                        "الأفلام",
                        color=TEXT,
                        size=27,
                        weight=ft.FontWeight.BOLD,
                    ),
                    catalog_section(
                        "الأفلام الأكثر مشاهدة",
                        movies,
                    ),
                ]
            )

        elif name == "الأنمي":
            content.controls.extend(
                [
                    ft.Text(
                        "الأنمي",
                        color=TEXT,
                        size=27,
                        weight=ft.FontWeight.BOLD,
                    ),
                    catalog_section(
                        "اختيارات محبي الأنمي",
                        anime,
                    ),
                ]
            )

        elif name == "المفضلة":
            content.controls.extend(
                [
                    ft.Text(
                        "المفضلة",
                        color=TEXT,
                        size=27,
                        weight=ft.FontWeight.BOLD,
                    ),
                    ft.Text(
                        "أضف أعمالك المفضلة لتظهر هنا.",
                        color=MUTED,
                        size=15,
                    ),
                ]
            )

        else:
            content.controls.extend(
                [
                    hero(),
                    catalog_section(
                        "أفلام مقترحة لك",
                        movies,
                    ),
                    catalog_section(
                        "أنمي يستحق المشاهدة",
                        anime,
                    ),
                ]
            )

        refresh_navigation()
        page.update()

    def load_from_tmdb(
        _event: ft.ControlEvent | None = None,
    ) -> None:
        nonlocal movies, anime

        if not data_source.configured:
            status.value = (
                "أضف TMDB_API_KEY إلى Secrets "
                "لجلب البيانات الحقيقية."
            )
            page.update()
            return

        status.value = "جارٍ تحديث الأفلام والأنمي..."
        page.update()

        try:
            fresh_movies, fresh_anime = (
                data_source.load_catalog()
            )

            if fresh_movies:
                movies = fresh_movies

            if fresh_anime:
                anime = fresh_anime

            status.value = "تم تحديث البيانات من TMDB."
            render_section(current_section)

        except requests.RequestException as error:
            status.value = (
                "تعذر الاتصال بـ TMDB، تم الإبقاء "
                f"على البيانات الاحتياطية: {error}"
            )
            page.update()

        except (ValueError, KeyError) as error:
            status.value = (
                f"استجابة غير متوقعة من TMDB: {error}"
            )
            page.update()

    sidebar = ft.Container(
        width=190,
        padding=ft.Padding.only(
            left=18,
            right=18,
            top=24,
            bottom=24,
        ),
        bgcolor="#101010",
        content=ft.Column(
            spacing=22,
            controls=[
                ft.Text(
                    "سينماي",
                    color=ACCENT,
                    size=25,
                    weight=ft.FontWeight.BOLD,
                ),
                ft.Text(
                    "أفلام وأنمي",
                    color=MUTED,
                    size=12,
                ),
                navigation,
                ft.Container(expand=True),
                ft.Text(
                    "الإصدار 1.0",
                    color="#666666",
                    size=11,
                ),
            ],
        ),
    )

    search = ft.TextField(
        hint_text="ابحث عن فيلم أو أنمي",
        prefix_icon=ft.Icons.SEARCH,
        filled=True,
        bgcolor=SURFACE,
        border_color=ft.Colors.TRANSPARENT,
        focused_border_color=ACCENT,
        color=TEXT,
        hint_style=ft.TextStyle(color=MUTED),
        border_radius=24,
        height=45,
        width=320,
    )

    top_bar = ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Row(
                spacing=10,
                controls=[
                    ft.CircleAvatar(
                        content=ft.Text(
                            "م",
                            color=TEXT,
                            weight=ft.FontWeight.BOLD,
                        ),
                        bgcolor=ACCENT,
                        radius=19,
                    ),
                    ft.Text(
                        "مرحباً بك",
                        color=MUTED,
                        size=13,
                    ),
                    ft.IconButton(
                        icon=ft.Icons.REFRESH,
                        tooltip="تحديث البيانات",
                        icon_color=MUTED,
                        on_click=load_from_tmdb,
                    ),
                ],
            ),
            search,
        ],
    )

    refresh_navigation()
    render_section("الرئيسية")

    page.add(
        ft.Row(
            expand=True,
            spacing=0,
            controls=[
                sidebar,
                ft.VerticalDivider(
                    width=1,
                    color="#242424",
                ),
                ft.Container(
                    expand=True,
                    padding=ft.Padding.symmetric(
                        horizontal=30,
                        vertical=24,
                    ),
                    content=ft.Column(
                        expand=True,
                        spacing=12,
                        controls=[
                            top_bar,
                            status,
                            content,
                        ],
                    ),
                ),
            ],
        )
    )


if __name__ == "__main__":
    ft.run(
        main,
        host="0.0.0.0",
        port=5000,
        view=ft.AppView.WEB_BROWSER,
    )

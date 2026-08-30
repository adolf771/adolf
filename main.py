"""Palestine Movie App - Flet mobile client.

The app uses TMDB only for metadata and Consumet for live playback sources.
No sample or hard-coded video URL is used.  Set the following environment
variables in the Replit Secrets / build environment:

    TMDB_API_KEY       the existing TMDB key supplied by the app owner
    CONSUMET_BASE_URL  optional override for a self-hosted Consumet instance
    VIDSRC_BASE_URL    optional Vidsrc embed host (defaults to vidsrc.to)

Consumet availability is intentionally not checked during startup.  The
configured placeholder lets the built-in fallback path continue to Vidsrc
when no Consumet server is available.
"""

from __future__ import annotations

import base64
import os
from io import BytesIO
from typing import Any
from urllib.parse import quote

import flet as ft
import requests
from PIL import Image, ImageDraw

try:
    import flet_video as ftv
except ImportError:
    ftv = None

try:
    import flet_webview as fwv
except ImportError:
    fwv = None


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w780"
# The API key stays in Replit Secrets and is never committed to GitHub.
TMDB_API_KEY = af9a9f29019a8416529a60c07110347d
CONSUMET_BASE_URL = "https://consumet.org"


VIDSRC_BASE_URL = os.getenv("VIDSRC_BASE_URL", "https://vidsrc.to").strip().rstrip("/")

BACKGROUND = "#07090D"
SURFACE = "#11151D"
SURFACE_LIGHT = "#1B222D"
TEXT = "#F7F8FA"
MUTED = "#AAB2BF"
ACCENT = "#F20D22"
PAGE_SIZE = 20

VIDSRC_BLOCKED_LINK_PREFIXES = [
    "about:blank",
    "javascript:",
    "intent:",
    "market:",
    "mailto:",
    "tel:",
    "https://doubleclick.net",
    "https://*.doubleclick.net",
    "https://googlesyndication.com",
    "https://*.googlesyndication.com",
    "https://googleadservices.com",
    "https://*.googleadservices.com",
    "https://popads.net",
    "https://*.popads.net",
    "https://propellerads.com",
    "https://*.propellerads.com",
]

# Vidsrc is an HTML embed page.  This script runs after each navigation and
# removes common ad containers while neutralising popup and redirect APIs.
# Native WebView navigation is also guarded by prevent_links below.
VIDSRC_BLOCKER_SCRIPT = r"""
(function () {
  "use strict";
  if (window.__palestineMovieBlockerInstalled) return;
  window.__palestineMovieBlockerInstalled = true;

  const blockedPattern = /(doubleclick|googlesyndication|googleadservices|popads|propellerads|adservice|adnxs|clickadu|exoclick|trafficjunky|onclickads)/i;
  const adSelector = [
    '[id*="ad" i]', '[class*="ad-" i]', '[class*="ads" i]',
    '[class*="popup" i]', '[class*="popunder" i]',
    'iframe[src*="ads" i]', 'iframe[src*="doubleclick" i]',
    'script[src*="ads" i]', 'a[target="_blank"]'
  ].join(",");

  const clean = (root) => {
    if (!root || !root.querySelectorAll) return;
    root.querySelectorAll(adSelector).forEach((node) => {
      const source = node.src || node.href || "";
      if (blockedPattern.test(source) || node.matches('a[target="_blank"]')) {
        node.remove();
      }
    });
  };

  const originalOpen = window.open;
  window.open = function (url) {
    if (!url || blockedPattern.test(String(url))) return null;
    return null;
  };
  window.alert = function () {};
  window.confirm = function () { return false; };
  window.prompt = function () { return null; };

  ["assign", "replace"].forEach((method) => {
    const original = window.location[method];
    try {
      window.location[method] = function (url) {
        if (blockedPattern.test(String(url || ""))) return;
        return original.call(window.location, url);
      };
    } catch (_) {}
  });

  const originalFetch = window.fetch;
  window.fetch = function (input, init) {
    const url = typeof input === "string" ? input : (input && input.url) || "";
    if (blockedPattern.test(String(url))) {
      return Promise.reject(new Error("Blocked advertising request"));
    }
    return originalFetch.call(this, input, init);
  };

  const originalXhrOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function (method, url) {
    if (blockedPattern.test(String(url || ""))) {
      this.__palestineMovieBlocked = true;
    }
    return originalXhrOpen.apply(this, arguments);
  };
  const originalXhrSend = XMLHttpRequest.prototype.send;
  XMLHttpRequest.prototype.send = function () {
    if (this.__palestineMovieBlocked) return;
    return originalXhrSend.apply(this, arguments);
  };

  document.addEventListener("click", (event) => {
    const link = event.target && event.target.closest
      ? event.target.closest("a")
      : null;
    if (link && (link.target === "_blank" || blockedPattern.test(link.href || ""))) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);

  document.addEventListener("submit", (event) => {
    const action = event.target && event.target.action || "";
    if (blockedPattern.test(action)) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);

  clean(document);
  new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => clean(node));
    });
  }).observe(document.documentElement || document, { childList: true, subtree: true });
})();
"""

CATEGORY_LABELS = {
    "movie": "فيلم",
    "series": "مسلسل",
    "anime": "أنمي",
    "cartoon": "كرتون",
}


class ApiConfigurationError(RuntimeError):
    """Raised when a live API has not been configured."""


def placeholder_base64(title: str) -> str:
    """Create an offline poster when TMDB has no image."""
    image = Image.new("RGB", (520, 720), "#252B36")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 470, 520, 720), fill="#52101A")
    draw.text((28, 560), title[:22], fill="#FFFFFF")
    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return base64.b64encode(output.getvalue()).decode("ascii")


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
    """Metadata and live-source client."""

    def __init__(self) -> None:
        self.api_key = af9a9f29019a8416529a60c07110347d
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Palestine-Movie-App/1.0"})

    @property
    def tmdb_configured(self) -> bool:
        return bool(self.api_key)

    @property
    def consumet_configured(self) -> bool:
        # Do not probe or validate Consumet. Requests are attempted lazily and
        # live_sources() falls back when the placeholder/server is unavailable.
        return True

    def _json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: int = 15,
    ) -> Any:
        response = self.session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def tmdb(
        self,
        endpoint: str,
        params: dict[str, Any] | None = None,
        page: int = 1,
    ) -> list[dict[str, Any]]:
        if not self.tmdb_configured:
            return []
        request_params: dict[str, Any] = {
            "api_key": self.api_key,
            "language": "ar-SA",
            "page": page,
        }
        if params:
            request_params.update(params)
        payload = self._json(f"{TMDB_BASE_URL}/{endpoint}", request_params)
        return payload.get("results", []) if isinstance(payload, dict) else []

    def consumet(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{CONSUMET_BASE_URL}/{path.lstrip('/')}"
        return self._json(url, params=params, timeout=20)

    def load_catalog(self) -> dict[str, list[dict[str, Any]]]:
        return {
            "movies": [
                format_item(item, "movie")
                for item in self.tmdb("movie/popular")
            ],
            "series": [
                format_item(item, "series")
                for item in self.tmdb("tv/popular")
            ],
            "anime": [
                format_item(item, "anime")
                for item in self.tmdb(
                    "discover/tv",
                    {
                        "with_genres": 16,
                        "with_original_language": "ja",
                        "sort_by": "popularity.desc",
                    },
                )
            ],
            "cartoons": [
                format_item(item, "cartoon")
                for item in self.tmdb(
                    "discover/tv",
                    {
                        "with_genres": 16,
                        "without_original_language": "ja",
                        "sort_by": "popularity.desc",
                    },
                )
            ],
        }

    def search(self, query: str) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []
        for item in self.tmdb(
            "search/multi",
            {"query": query, "include_adult": False},
        ):
            media_type = item.get("media_type")
            if media_type == "movie":
                items.append(format_item(item, "movie"))
            elif media_type == "tv":
                kind = "anime" if item.get("original_language") == "ja" else "series"
                items.append(format_item(item, kind))
        return items

    def details(self, item: dict[str, Any]) -> dict[str, Any]:
        media_id = item.get("id")
        if not media_id or not self.tmdb_configured:
            return {}
        endpoint = "movie" if item.get("kind") == "movie" else "tv"
        payload = self._json(
            f"{TMDB_BASE_URL}/{endpoint}/{media_id}",
            {"api_key": self.api_key, "language": "ar-SA"},
        )
        return payload if isinstance(payload, dict) else {}

    def season_episodes(
        self,
        media_id: Any,
        season_number: int,
    ) -> list[dict[str, Any]]:
        if not media_id or not self.tmdb_configured:
            return []
        payload = self._json(
            f"{TMDB_BASE_URL}/tv/{media_id}/season/{season_number}",
            {"api_key": self.api_key, "language": "ar-SA"},
        )
        episodes = payload.get("episodes", []) if isinstance(payload, dict) else []
        return [
            {
                "episode_id": str(
                    episode.get("id")
                    or f"{media_id}-s{season_number}-e{episode.get('episode_number')}"
                ),
                "episode_number": episode.get("episode_number", 1),
                "season_number": season_number,
                "title": str(
                    episode.get("name")
                    or f"الحلقة {episode.get('episode_number', 1)}"
                ),
                "subtitle": (
                    f"الموسم {season_number} • الحلقة "
                    f"{episode.get('episode_number', 1)}"
                ),
            }
            for episode in episodes
            if episode.get("episode_number") is not None
        ]

    def gogoanime_episodes(self, title: str) -> list[dict[str, Any]]:
        """Search Gogoanime through the configured Consumet instance."""
        search_payload = self.consumet(f"anime/gogoanime/{quote(title)}")
        results = (
            search_payload.get("results", [])
            if isinstance(search_payload, dict)
            else []
        )
        if not isinstance(results, list) or not results:
            return []
        anime_id = results[0].get("id")
        if not anime_id:
            return []
        info = self.consumet("anime/gogoanime/info", {"id": anime_id})
        raw_episodes = info.get("episodes", []) if isinstance(info, dict) else []
        return [
            {
                "episode_id": str(episode.get("id", "")),
                "episode_number": episode.get("number", 1),
                "season_number": 1,
                "title": f"الحلقة {episode.get('number', 1)}",
                "subtitle": "Gogoanime • حلقة مترجمة",
            }
            for episode in raw_episodes
            if episode.get("id")
        ]

    def _source_payload(self, payload: Any) -> list[dict[str, Any]]:
        if not isinstance(payload, dict):
            return []
        raw_sources = payload.get("sources", [])
        if isinstance(raw_sources, dict):
            raw_sources = [raw_sources]
        if not isinstance(raw_sources, list):
            return []

        headers = payload.get("headers", {})
        headers = headers if isinstance(headers, dict) else {}
        sources: list[dict[str, Any]] = []
        for raw in raw_sources:
            if not isinstance(raw, dict):
                continue
            url = str(raw.get("url") or "").strip()
            if not url.startswith(("https://", "http://")):
                continue
            sources.append(
                {
                    "url": url,
                    "quality": str(raw.get("quality") or "auto"),
                    "is_m3u8": bool(raw.get("isM3U8") or raw.get("is_m3u8")),
                    "headers": {
                        key: str(value)
                        for key, value in headers.items()
                        if value
                    },
                    "provider": "Consumet",
                    "playable": True,
                }
            )
        return sources

    def _flixhq_sources(self, title: str) -> list[dict[str, Any]]:
        """Resolve a movie/show to direct sources through Consumet."""
        search = self.consumet(f"movies/flixhq/{quote(title)}")
        results = search.get("results", []) if isinstance(search, dict) else []
        if not isinstance(results, list) or not results:
            return []
        media_id = results[0].get("id")
        if not media_id:
            return []
        info = self.consumet("movies/flixhq/info", {"id": media_id})
        episodes = info.get("episodes", []) if isinstance(info, dict) else []
        if not episodes:
            return []
        episode_id = episodes[0].get("id") or episodes[0].get("episodeId")
        if not episode_id:
            return []
        payload = self.consumet(
            "movies/flixhq/watch",
            {"episodeId": episode_id},
        )
        return self._source_payload(payload)

    def vidsrc_embed_url(
        self,
        item: dict[str, Any],
        entry: dict[str, Any],
    ) -> str:
        """Return a Vidsrc embed reference, never pretend it is an MP4 stream."""
        media_id = item.get("id")
        if not media_id:
            return ""
        if item.get("kind") == "movie":
            return f"{VIDSRC_BASE_URL}/embed/movie/{media_id}"
        season = entry.get("season_number", 1)
        episode = entry.get("episode_number", 1)
        return f"{VIDSRC_BASE_URL}/embed/tv/{media_id}/{season}-{episode}"

    def live_sources(
        self,
        item: dict[str, Any],
        entry: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Get direct playable sources; no fake URL is ever returned."""
        if item.get("kind") == "anime":
            payloads = [
                lambda: self.consumet(
                    "anime/gogoanime/watch",
                    {"episodeId": entry.get("episode_id")},
                ),
                lambda: self.consumet(
                    f"anime/gogoanime/watch/{quote(str(entry.get('episode_id', '')))}"
                ),
            ]
            for request in payloads:
                try:
                    sources = self._source_payload(request())
                    if sources:
                        return sources
                except (ApiConfigurationError, requests.RequestException, ValueError):
                    continue
        else:
            try:
                sources = self._flixhq_sources(str(item.get("title", "")))
                if sources:
                    return sources
            except (ApiConfigurationError, requests.RequestException, ValueError):
                pass

        # Vidsrc provides an HTML embed page, not a direct media stream.
        # Keep the live reference for a future WebView integration, but do
        # not pass it to VideoMedia because that would fail at playback time.
        embed_url = self.vidsrc_embed_url(item, entry)
        return (
            [
                {
                    "url": embed_url,
                    "quality": "Vidsrc embed",
                    "provider": "Vidsrc",
                    "headers": {},
                    "playable": False,
                }
            ]
            if embed_url
            else []
        )


def main(page: ft.Page) -> None:
    page.title = "Palestine Movie App"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO

    data = CinemaData()
    catalogs: dict[str, list[dict[str, Any]]] = {
        "movies": [],
        "series": [],
        "anime": [],
        "cartoons": [],
    }
    current_view = "home"
    selected_item: dict[str, Any] | None = None
    status = ft.Text("", color=MUTED, size=12, text_align=ft.TextAlign.RIGHT)
    content = ft.Column(spacing=18, scroll=ft.ScrollMode.AUTO)

    def notify(message: str) -> None:
        status.value = message
        page.update()

    def item_image(item: dict[str, Any], width: int = 150, height: int = 210) -> ft.Image:
        poster = item.get("poster")
        if poster and str(poster).startswith(("http://", "https://")):
            source = str(poster)
        elif poster:
            source = f"{TMDB_IMAGE_URL}{poster}"
        else:
            source = (
                "data:image/png;base64,"
                + placeholder_base64(str(item.get("title", "محتوى")))
            )
        return ft.Image(
            src=source,
            width=width,
            height=height,
            fit=ft.BoxFit.COVER,
            border_radius=12,
        )

    def poster_card(item: dict[str, Any]) -> ft.Container:
        return ft.Container(
            width=162,
            bgcolor=SURFACE,
            border_radius=16,
            padding=6,
            on_click=lambda _event, chosen=item: open_details(chosen),
            content=ft.Column(
                spacing=6,
                controls=[
                    item_image(item),
                    ft.Text(
                        str(item.get("title", "بدون عنوان")),
                        color=TEXT,
                        size=13,
                        weight=ft.FontWeight.BOLD,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                    ft.Text(
                        f"★ {item.get('rating', '—')}  •  {item.get('subtitle', '')}",
                        color=MUTED,
                        size=10,
                        max_lines=1,
                        overflow=ft.TextOverflow.ELLIPSIS,
                        text_align=ft.TextAlign.RIGHT,
                    ),
                ],
            ),
        )

    def source_title(source: dict[str, Any]) -> str:
        return f"{source.get('provider', 'مصدر')} • {source.get('quality', 'auto')}"

    def show_vidsrc_webview(
        item: dict[str, Any],
        source: dict[str, Any],
        entry: dict[str, Any],
    ) -> None:
        """Show Vidsrc in-app and inject the popup/ad guard after navigation."""
        if fwv is None:
            notify("ثبّت flet-webview لتشغيل Vidsrc داخل التطبيق.")
            return

        url = str(source.get("url", "")).strip()
        if not url.startswith(("https://", "http://")):
            notify("رابط Vidsrc غير صالح.")
            return

        async def inject_blocker(_event: Any = None) -> None:
            try:
                await webview.set_javascript_mode(fwv.JavaScriptMode.UNRESTRICTED)
                await webview.run_javascript(VIDSRC_BLOCKER_SCRIPT)
            except Exception as error:
                notify(f"تعذر تفعيل حماية WebView: {error}")

        def guard_navigation(event: Any) -> None:
            changed_url = str(getattr(event, "data", "") or "").lower()
            blocked_tokens = (
                "doubleclick",
                "googlesyndication",
                "googleadservices",
                "popads",
                "propellerads",
                "adservice",
                "adnxs",
                "clickadu",
                "exoclick",
                "trafficjunky",
                "onclickads",
            )
            if changed_url.startswith(("intent:", "market:", "mailto:", "tel:")):
                page.run_task(webview.go_back)
            elif any(token in changed_url for token in blocked_tokens):
                page.run_task(webview.go_back)

        webview = fwv.WebView(
            url=url,
            prevent_links=VIDSRC_BLOCKED_LINK_PREFIXES,
            bgcolor="#050608",
            expand=True,
            on_page_ended=inject_blocker,
            on_url_change=guard_navigation,
        )

        content.controls.clear()
        content.controls.extend(
            [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=TEXT,
                            on_click=lambda _event: open_details(item),
                        ),
                        ft.Text("مشاهدة آمنة", color=TEXT, size=24),
                    ],
                ),
                ft.Container(
                    height=520,
                    bgcolor="#050608",
                    border_radius=18,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=webview,
                ),
                ft.Text(
                    f"{item.get('title', 'المحتوى')} • "
                    f"{entry.get('title', 'الحلقة')} • Vidsrc",
                    color=TEXT,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.RIGHT,
                ),
            ]
        )
        page.update()

    def show_player(
        item: dict[str, Any],
        source: dict[str, Any],
        entry: dict[str, Any],
    ) -> None:
        if not source.get("playable"):
            if source.get("provider") == "Vidsrc":
                show_vidsrc_webview(item, source, entry)
                return
            notify(
                "Vidsrc يعيد صفحة تضمين HTML وليس رابط فيديو مباشر؛ "
                "يلزم WebView لتشغيله."
            )
            return
        if ftv is None:
            notify("ثبّت flet-video لتفعيل المشغل داخل التطبيق.")
            return

        url = str(source.get("url", "")).strip()
        headers = source.get("headers") or {}
        media_kwargs: dict[str, Any] = {}
        if headers:
            media_kwargs["http_headers"] = headers
        media = ftv.VideoMedia(url, **media_kwargs)
        player = ftv.Video(
            expand=True,
            autoplay=True,
            playlist=[media],
        )

        content.controls.clear()
        content.controls.extend(
            [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=TEXT,
                            on_click=lambda _event: open_details(item),
                        ),
                        ft.Text("المشغل", color=TEXT, size=24),
                    ],
                ),
                ft.Container(
                    height=320,
                    bgcolor="#050608",
                    border_radius=18,
                    clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                    content=player,
                ),
                ft.Text(
                    f"{item.get('title', 'المحتوى')} • "
                    f"{entry.get('title', 'الحلقة')} • {source_title(source)}",
                    color=TEXT,
                    size=16,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.RIGHT,
                ),
            ]
        )
        page.update()

    def choose_source(
        item: dict[str, Any],
        entry: dict[str, Any],
    ) -> None:
        notify("جارٍ البحث عن مصدر بث حي...")
        try:
            sources = data.live_sources(item, entry)
        except (
            ApiConfigurationError,
            requests.RequestException,
            ValueError,
            KeyError,
        ) as error:
            notify(f"تعذر استخراج رابط حي: {error}")
            return
        playable = [source for source in sources if source.get("playable")]
        if not playable:
            vidsrc_source = next(
                (source for source in sources if source.get("provider") == "Vidsrc"),
                None,
            )
            if vidsrc_source:
                show_vidsrc_webview(item, vidsrc_source, entry)
                return
            notify("لم يتوفر مصدر بث حي لهذا المحتوى حالياً.")
            return
        dialog = ft.AlertDialog(
            modal=True,
            bgcolor=SURFACE,
            title=ft.Text("اختر المصدر والجودة", color=TEXT),
            content=ft.Column(
                tight=True,
                controls=[
                    ft.FilledButton(
                        source_title(source),
                        on_click=lambda _event, chosen=source: (
                            page.pop_dialog(),
                            show_player(item, chosen, entry),
                        ),
                        style=ft.ButtonStyle(bgcolor=ACCENT, color=TEXT),
                    )
                    for source in playable
                ],
            ),
            actions=[
                ft.TextButton(
                    "إلغاء",
                    on_click=lambda _event: page.pop_dialog(),
                )
            ],
        )
        page.show_dialog(dialog)

    def episode_row(item: dict[str, Any], entry: dict[str, Any]) -> ft.Container:
        return ft.Container(
            bgcolor=SURFACE_LIGHT,
            border_radius=12,
            padding=10,
            content=ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.PLAY_CIRCLE_FILLED,
                        icon_color=ACCENT,
                        icon_size=30,
                        tooltip="تشغيل مباشر",
                        on_click=lambda _event: choose_source(item, entry),
                    ),
                    ft.Column(
                        expand=True,
                        spacing=3,
                        controls=[
                            ft.Text(
                                str(entry.get("title", "الفيلم الكامل")),
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
                ],
            ),
        )

    def open_details(item: dict[str, Any]) -> None:
        nonlocal current_view, selected_item
        current_view = "details"
        selected_item = item
        details = {}
        if data.tmdb_configured:
            try:
                details = data.details(item)
                if details.get("overview"):
                    item["overview"] = details["overview"]
            except (requests.RequestException, ValueError, KeyError):
                pass

        entries: list[dict[str, Any]] = []
        if item.get("kind") == "anime" and data.consumet_configured:
            try:
                entries = data.gogoanime_episodes(str(item.get("title", "")))
            except (requests.RequestException, ValueError, KeyError):
                entries = []
        elif item.get("kind") in {"series", "anime"}:
            seasons = [
                season.get("season_number")
                for season in details.get("seasons", [])
                if season.get("season_number", 0) > 0
            ]
            if seasons:
                try:
                    entries = data.season_episodes(item.get("id"), int(seasons[0]))
                except (requests.RequestException, ValueError, KeyError):
                    entries = []

        if not entries:
            entries = [
                {
                    "episode_id": str(item.get("id") or item.get("title", "")),
                    "episode_number": 1,
                    "season_number": 1,
                    "title": "الفيلم الكامل" if item.get("kind") == "movie" else "الحلقة 1",
                    "subtitle": "مصدر حي من Consumet عند الضغط على تشغيل",
                }
            ]

        content.controls.clear()
        content.controls.extend(
            [
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.ARROW_BACK,
                            icon_color=TEXT,
                            on_click=lambda _event: render_home(),
                        ),
                        ft.Text("تفاصيل العمل", color=TEXT, size=22),
                    ],
                ),
                ft.Container(
                    bgcolor=SURFACE,
                    border_radius=18,
                    padding=14,
                    content=ft.Column(
                        spacing=12,
                        controls=[
                            ft.Container(
                                alignment=ft.alignment.center,
                                content=item_image(item, 240, 320),
                            ),
                            ft.Text(
                                str(item.get("title", "بدون عنوان")),
                                color=TEXT,
                                size=25,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                            ft.Text(
                                f"{item.get('rating', '—')} ★ • {item.get('subtitle', '')}",
                                color="#FFD54A",
                                text_align=ft.TextAlign.RIGHT,
                            ),
                            ft.Text(
                                str(item.get("overview", "")),
                                color="#D5D9E0",
                                size=15,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                            ft.Text(
                                "الحلقات والمشاهدة",
                                color=TEXT,
                                size=18,
                                weight=ft.FontWeight.BOLD,
                                text_align=ft.TextAlign.RIGHT,
                            ),
                            ft.Column(
                                spacing=8,
                                controls=[episode_row(item, entry) for entry in entries],
                            ),
                        ],
                    ),
                ),
            ]
        )
        page.update()

    def render_home() -> None:
        nonlocal current_view
        current_view = "home"
        content.controls.clear()
        controls: list[ft.Control] = [
            ft.Text(
                "Palestine Movie 🇵🇸",
                color=ACCENT,
                size=26,
                weight=ft.FontWeight.BOLD,
                text_align=ft.TextAlign.RIGHT,
            ),
        ]
        for key, title in (
            ("movies", "الأفلام"),
            ("series", "المسلسلات"),
            ("anime", "الأنمي"),
            ("cartoons", "الكرتون"),
        ):
            items = catalogs.get(key, [])
            if items:
                controls.extend(
                    [
                        ft.Text(
                            title,
                            color=TEXT,
                            size=20,
                            weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.RIGHT,
                        ),
                        ft.Row(
                            controls=[poster_card(item) for item in items[:PAGE_SIZE]],
                            spacing=10,
                            scroll=ft.ScrollMode.AUTO,
                        ),
                    ]
                )
        if not any(catalogs.values()):
            controls.append(
                ft.Text(
                    "اضغط تحديث لتحميل الكتالوج من TMDB.",
                    color=MUTED,
                    size=16,
                    text_align=ft.TextAlign.RIGHT,
                )
            )
        content.controls.extend(controls)
        page.update()

    def refresh(_event: ft.ControlEvent | None = None) -> None:
        if not data.tmdb_configured:
            notify("أضف TMDB_API_KEY إلى Secrets باستخدام قيمته الأصلية.")
            return
        notify("جارٍ تحميل المحتوى من TMDB...")
        try:
            fresh = data.load_catalog()
            for key, items in fresh.items():
                catalogs[key] = items
            notify("تم تحديث الكتالوج.")
            render_home()
        except (requests.RequestException, ValueError, KeyError) as error:
            notify(f"تعذر تحديث الكتالوج: {error}")

    def perform_search(event: ft.ControlEvent) -> None:
        query = (event.control.value or "").strip()
        if not query:
            render_home()
            return
        if not data.tmdb_configured:
            notify("أضف TMDB_API_KEY إلى Secrets للبحث.")
            return
        try:
            results = data.search(query)
        except (requests.RequestException, ValueError, KeyError) as error:
            notify(f"تعذر البحث: {error}")
            return
        content.controls.clear()
        content.controls.extend(
            [
                ft.Text("نتائج البحث", color=TEXT, size=24),
                ft.Row(
                    wrap=True,
                    spacing=10,
                    run_spacing=10,
                    controls=[poster_card(item) for item in results]
                    or [ft.Text("لا توجد نتائج.", color=MUTED)],
                ),
            ]
        )
        page.update()

    search = ft.TextField(
        hint_text="ابحث عن فيلم أو مسلسل أو أنمي",
        prefix_icon=ft.Icons.SEARCH,
        filled=True,
        bgcolor=SURFACE,
        color=TEXT,
        border_radius=20,
        on_submit=perform_search,
    )
    page.add(
        ft.Container(
            padding=16,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.REFRESH,
                                icon_color=MUTED,
                                on_click=refresh,
                            ),
                            ft.Container(expand=True, content=search),
                        ]
                    ),
                    status,
                    content,
                ],
            ),
        )
    )
    render_home()


if __name__ == "__main__":
    ft.run(
        main,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        view=ft.AppView.WEB_BROWSER,
    )

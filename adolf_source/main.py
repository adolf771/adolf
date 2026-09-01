"""Palestine Movie App - Flet mobile client.

The app uses TMDB only for metadata and Consumet for live playback sources.
No sample or hard-coded video URL is used.
TMDB metadata uses the TMDB_API_KEY environment secret, and live playback uses
the fixed Consumet service URL defined below.
"""

from __future__ import annotations

import asyncio
import base64
import os
import threading
import time
from pathlib import Path
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


TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w780"
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()
try:
    from build_config import TMDB_PROXY_URL as BUILD_TMDB_PROXY_URL
except ImportError:
    BUILD_TMDB_PROXY_URL = ""

# The APK contains only this public URL; the TMDB credential stays server-side.
TMDB_PROXY_URL = "https://palestine-movie-api--m46560834.replit.app/api"
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
        self.proxy_url = TMDB_PROXY_URL
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "Palestine-Movie-App/1.0"})
        self._cache: dict[str, tuple[float, Any]] = {}
        self._cache_lock = threading.Lock()

    @property
    def tmdb_configured(self) -> bool:
        return bool(self.proxy_url)

    def _json(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        timeout: int = 15,
    ) -> Any:
        response = self.session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        return response.json()

    def _cached_json(self, cache_key: str, url: str, params: dict[str, Any] | None = None, timeout: int = 20, ttl: int = 300) -> Any:
        now = time.monotonic()
        with self._cache_lock:
            cached = self._cache.get(cache_key)
            if cached and cached[0] > now:
                return cached[1]
        response = self.session.get(url, params=params, timeout=timeout)
        response.raise_for_status()
        payload = response.json()
        with self._cache_lock:
            self._cache[cache_key] = (time.monotonic() + ttl, payload)
        return payload

    def tmdb_proxy(self, path: str, params: dict[str, Any] | None = None) -> Any:
        if not self.tmdb_configured:
            return {}
        url = f"{self.proxy_url}/{path.lstrip('/')}"
        cache_key = "tmdb:" + url + ":" + repr(sorted((params or {}).items()))
        return self._cached_json(cache_key, url, params=params, timeout=20, ttl=300)

    def consumet(self, path: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{CONSUMET_BASE_URL}/{path.lstrip('/')}"
        cache_key = "consumet:" + url + ":" + repr(sorted((params or {}).items()))
        return self._cached_json(cache_key, url, params=params, timeout=25, ttl=180)

    def load_catalog(self) -> dict[str, list[dict[str, Any]]]:
        payload = self.tmdb_proxy("catalog")
        return payload if isinstance(payload, dict) else {}

    def search(self, query: str) -> list[dict[str, Any]]:
        payload = self.tmdb_proxy("search", {"q": query})
        return payload if isinstance(payload, list) else []

    def details(self, item: dict[str, Any]) -> dict[str, Any]:
        media_id = item.get("id")
        if not media_id or not self.tmdb_configured:
            return {}
        endpoint = "movie" if item.get("kind") == "movie" else "tv"
        payload = self.tmdb_proxy(
            f"details/{endpoint}/{quote(str(media_id), safe='')}"
        )
        return payload if isinstance(payload, dict) else {}

    def season_episodes(
        self,
        media_id: Any,
        season_number: int,
    ) -> list[dict[str, Any]]:
        if not media_id or not self.tmdb_configured:
            return []
        payload = self.tmdb_proxy(
            f"season/{quote(str(media_id), safe='')}/{season_number}"
        )
        return payload if isinstance(payload, list) else []

    def gogoanime_episodes(self, title: str) -> list[dict[str, Any]]:
        """Search Gogoanime and return every episode available from Consumet."""
        search_payload = self.consumet(f"anime/gogoanime/{quote(title, safe='')}")
        results = search_payload.get("results", []) if isinstance(search_payload, dict) else []
        if not isinstance(results, list) or not results:
            return []
        anime_id = results[0].get("id")
        if not anime_id:
            return []
        info = {}
        for path, params in (
            ("anime/gogoanime/info", {"id": anime_id}),
            (f"anime/gogoanime/info/{quote(str(anime_id), safe='')}", None),
        ):
            try:
                info = self.consumet(path, params)
                if isinstance(info, dict) and info.get("episodes"):
                    break
            except (requests.RequestException, ValueError):
                continue
        raw_episodes = info.get("episodes", []) if isinstance(info, dict) else []
        output = []
        for episode in raw_episodes if isinstance(raw_episodes, list) else []:
            if not isinstance(episode, dict) or not episode.get("id"):
                continue
            number = episode.get("number") or episode.get("episodeNumber") or 1
            output.append({
                "episode_id": str(episode.get("id")),
                "episode_number": number,
                "season_number": 1,
                "title": str(episode.get("title") or f"الحلقة {number}"),
                "subtitle": str(episode.get("description") or "Gogoanime • حلقة متوفرة عبر Consumet"),
                "duration": episode.get("duration") or "",
            })
        return output

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
                    "size": raw.get("size") or raw.get("fileSize") or raw.get("size_bytes"),
                    "provider": "Consumet",
                    "playable": True,
                }
            )
        return sources

    def _flixhq_sources(self, title: str, entry: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        """Resolve a movie or the selected episode through Consumet FlixHQ."""
        search = self.consumet(f"movies/flixhq/{quote(title, safe='')}")
        results = search.get("results", []) if isinstance(search, dict) else []
        if not isinstance(results, list) or not results:
            return []
        media_id = results[0].get("id")
        if not media_id:
            return []
        info = self.consumet("movies/flixhq/info", {"id": media_id})
        episodes = info.get("episodes", []) if isinstance(info, dict) else []
        if not isinstance(episodes, list) or not episodes:
            return []
        wanted = entry or {}
        wanted_number = str(wanted.get("episode_number", "1"))
        selected = None
        for candidate in episodes:
            if str(candidate.get("id") or candidate.get("episodeId")) == str(wanted.get("episode_id")):
                selected = candidate
                break
            if str(candidate.get("number") or candidate.get("episode_number")) == wanted_number:
                selected = candidate
        selected = selected or episodes[0]
        episode_id = selected.get("id") or selected.get("episodeId")
        if not episode_id:
            return []
        payload = self.consumet("movies/flixhq/watch", {"episodeId": episode_id})
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
                sources = self._flixhq_sources(str(item.get("title", "")), entry)
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
    page.title = "Palestine Movie"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO

    data = CinemaData()
    catalogs: dict[str, list[dict[str, Any]]] = {"movies": [], "series": [], "anime": [], "cartoons": []}
    current_view = "home"
    active_category = "all"
    selected_item: dict[str, Any] | None = None
    details_token = 0
    catalog_loading = False
    search_loading = False
    downloads: dict[str, dict[str, Any]] = {}
    try:
        favorite_values = page.client_storage.get("palestine_movie_favorites") or []
        favorites = {str(value) for value in favorite_values}
    except Exception:
        favorites = set()

    status = ft.Text("", color=MUTED, size=12, text_align=ft.TextAlign.RIGHT)
    content = ft.Column(spacing=18, scroll=ft.ScrollMode.AUTO, expand=True)
    search = ft.TextField(
        hint_text="ابحث بالعربية أو الإنجليزية...",
        prefix_icon=ft.Icons.SEARCH,
        filled=True,
        bgcolor=SURFACE,
        color=TEXT,
        hint_style=ft.TextStyle(color=MUTED),
        border_radius=18,
        border_color=SURFACE_LIGHT,
        focused_border_color=ACCENT,
        text_align=ft.TextAlign.RIGHT,
        on_submit=lambda event: page.run_task(perform_search_async, event.control.value or ""),
        expand=True,
    )

    def notify(message: str) -> None:
        status.value = message
        page.update()

    def item_key(item: dict[str, Any]) -> str:
        return f"{item.get('kind', 'movie')}:{item.get('id', item.get('title', ''))}"

    def save_favorites() -> None:
        try:
            page.client_storage.set("palestine_movie_favorites", sorted(favorites))
        except Exception:
            pass

    def media_source(item: dict[str, Any], field: str = "poster") -> str:
        value = item.get(field) or item.get("poster")
        if value and str(value).startswith(("http://", "https://", "data:")):
            return str(value)
        if value:
            return f"{TMDB_IMAGE_URL}{value}"
        return "data:image/png;base64," + placeholder_base64(str(item.get("title", "محتوى")))

    def item_image(item: dict[str, Any], width: int = 150, height: int = 210, backdrop: bool = False) -> ft.Image:
        return ft.Image(
            src=media_source(item, "backdrop" if backdrop else "poster"),
            width=width,
            height=height,
            fit=ft.BoxFit.COVER,
            border_radius=12,
        )

    def red_button(label: str, handler: Any, icon: Any = None) -> ft.Control:
        return ft.FilledButton(
            label,
            icon=icon,
            on_click=handler,
            style=ft.ButtonStyle(bgcolor=ACCENT, color=TEXT),
        )

    def toggle_favorite(item: dict[str, Any]) -> None:
        key = item_key(item)
        if key in favorites:
            favorites.remove(key)
            notify("تمت إزالة العمل من المفضلة.")
        else:
            favorites.add(key)
            notify("تمت إضافة العمل إلى المفضلة.")
        save_favorites()
        if current_view == "favorites":
            render_favorites()
        else:
            page.update()

    def favorite_button(item: dict[str, Any]) -> ft.IconButton:
        return ft.IconButton(
            icon=ft.Icons.FAVORITE if item_key(item) in favorites else ft.Icons.FAVORITE_BORDER,
            icon_color=ACCENT if item_key(item) in favorites else MUTED,
            tooltip="إزالة من المفضلة" if item_key(item) in favorites else "إضافة للمفضلة",
            on_click=lambda _event, chosen=item: toggle_favorite(chosen),
        )

    def poster_card(item: dict[str, Any]) -> ft.Container:
        return ft.Container(
            width=164,
            bgcolor=SURFACE,
            border_radius=16,
            padding=6,
            on_click=lambda _event, chosen=item: open_details(chosen),
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Stack(
                        width=152,
                        height=202,
                        controls=[
                            item_image(item, 152, 202),
                            ft.Container(alignment=ft.alignment.Alignment(1, -1), content=favorite_button(item)),
                        ],
                    ),
                    ft.Text(str(item.get("title", "بدون عنوان")), color=TEXT, size=13, weight=ft.FontWeight.BOLD, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, text_align=ft.TextAlign.RIGHT),
                    ft.Text(f"★ {item.get('rating', '—')} • {item.get('subtitle', '')}", color=MUTED, size=10, max_lines=1, overflow=ft.TextOverflow.ELLIPSIS, text_align=ft.TextAlign.RIGHT),
                ],
            ),
        )

    def horizontal_cards(items: list[dict[str, Any]]) -> ft.Row:
        return ft.Row(controls=[poster_card(item) for item in items], spacing=10, scroll=ft.ScrollMode.AUTO)

    def category_chip(label: str, value: str) -> ft.Container:
        return ft.Container(
            bgcolor=ACCENT if active_category == value else SURFACE_LIGHT,
            border_radius=18,
            padding=ft.Padding(left=16, top=9, right=16, bottom=9),
            on_click=lambda _event, chosen=value: select_category(chosen),
            content=ft.Text(label, color=TEXT, size=13, weight=ft.FontWeight.BOLD),
        )

    def hero_card(item: dict[str, Any]) -> ft.Container:
        return ft.Container(
            height=246,
            border_radius=20,
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            content=ft.Stack(
                controls=[
                    item_image(item, 900, 246, backdrop=True),
                    ft.Container(
                        bgcolor="#D907090D",
                        padding=18,
                        alignment=ft.alignment.Alignment(1, 0),
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.END,
                            spacing=7,
                            controls=[
                                ft.Text("اختيار اليوم", color="#FFD0D5", size=12, weight=ft.FontWeight.BOLD),
                                ft.Text(str(item.get("title", "فيلم مميز")), color=TEXT, size=25, weight=ft.FontWeight.BOLD, max_lines=2, text_align=ft.TextAlign.RIGHT),
                                ft.Text(f"{item.get('subtitle', '')} • ★ {item.get('rating', '—')}", color="#F4E6E8", size=13, text_align=ft.TextAlign.RIGHT),
                                red_button("شاهد الآن", lambda _event, chosen=item: start_watch(chosen, movie_entry(chosen)), ft.Icons.PLAY_ARROW),
                            ],
                        ),
                    ),
                ],
            ),
        )

    def movie_entry(item: dict[str, Any]) -> dict[str, Any]:
        return {"episode_id": str(item.get("id") or item.get("title", "")), "episode_number": 1, "season_number": 1, "title": "الفيلم الكامل", "subtitle": "مصدر مباشر من Consumet عند الضغط على التشغيل"}

    def render_home() -> None:
        nonlocal current_view
        current_view = "home"
        all_items = [item for key in catalogs for item in catalogs[key]]
        if active_category == "all":
            visible = all_items
        else:
            visible = catalogs.get(active_category, [])
        controls: list[ft.Control] = [
            ft.Row(controls=[category_chip("الكل", "all"), category_chip("أفلام", "movies"), category_chip("مسلسلات", "series"), category_chip("أنمي", "anime"), category_chip("كرتون", "cartoons")], spacing=8, scroll=ft.ScrollMode.AUTO),
        ]
        if all_items:
            controls.append(hero_card(all_items[0]))
        if visible:
            title = {"all": "الأكثر مشاهدة", "movies": "الأفلام", "series": "المسلسلات", "anime": "الأنمي", "cartoons": "الكرتون"}.get(active_category, "المحتوى")
            controls.extend([ft.Text(title, color=TEXT, size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), horizontal_cards(visible[:PAGE_SIZE])])
        else:
            controls.append(ft.Container(padding=30, alignment=ft.alignment.Alignment(0, 0), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.ProgressRing(color=ACCENT) if catalog_loading else ft.Text("جارٍ تجهيز الكتالوج...", color=MUTED, size=16)])))
        content.controls.clear()
        content.controls.extend(controls)
        page.update()

    def select_category(category: str) -> None:
        nonlocal active_category
        active_category = category
        render_home()

    def source_title(source: dict[str, Any]) -> str:
        quality = str(source.get("quality") or "جودة تلقائية")
        size = source.get("size") or source.get("size_bytes")
        size_text = f" • {size}" if size else ""
        stream_text = " • HLS" if source.get("is_m3u8") else ""
        return f"{source.get('provider', 'مصدر')} • {quality}{size_text}{stream_text}"

    def show_vidsrc_webview(item: dict[str, Any], source: dict[str, Any], entry: dict[str, Any]) -> None:
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
            blocked_tokens = ("doubleclick", "googlesyndication", "googleadservices", "popads", "propellerads", "adservice", "adnxs", "clickadu", "exoclick", "trafficjunky", "onclickads")
            if changed_url.startswith(("intent:", "market:", "mailto:", "tel:")):
                page.run_task(webview.go_back)
            elif any(token in changed_url for token in blocked_tokens):
                page.run_task(webview.go_back)

        webview = fwv.WebView(url=url, prevent_links=VIDSRC_BLOCKED_LINK_PREFIXES, bgcolor="#050608", expand=True, on_page_ended=inject_blocker, on_url_change=guard_navigation)
        content.controls.clear()
        content.controls.extend([
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT, on_click=lambda _event: open_details(item)), ft.Text("مشاهدة آمنة", color=TEXT, size=24)]),
            ft.Container(height=520, bgcolor="#050608", border_radius=18, clip_behavior=ft.ClipBehavior.ANTI_ALIAS, content=webview),
            ft.Text(f"{item.get('title', 'المحتوى')} • {entry.get('title', 'الحلقة')} • Vidsrc", color=TEXT, size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
        ])
        page.update()

    def show_player(item: dict[str, Any], source: dict[str, Any], entry: dict[str, Any]) -> None:
        if not source.get("playable"):
            if source.get("provider") == "Vidsrc":
                show_vidsrc_webview(item, source, entry)
            else:
                notify("المصدر لا يعيد فيديو مباشراً.")
            return
        if ftv is None:
            notify("ثبّت flet-video لتفعيل المشغل داخل التطبيق.")
            return
        url = str(source.get("url", "")).strip()
        media_kwargs: dict[str, Any] = {}
        if source.get("headers"):
            media_kwargs["http_headers"] = source["headers"]
        media = ftv.VideoMedia(url, **media_kwargs)
        player = ftv.Video(expand=True, autoplay=True, show_controls=True, playlist=[media])
        content.controls.clear()
        content.controls.extend([
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT, on_click=lambda _event: open_details(item)), ft.Text("المشغل الداخلي", color=TEXT, size=24)]),
            ft.Container(height=330, bgcolor="#050608", border_radius=18, clip_behavior=ft.ClipBehavior.ANTI_ALIAS, content=player),
            ft.Text(f"{item.get('title', 'المحتوى')} • {entry.get('title', 'الحلقة')} • {source_title(source)}", color=TEXT, size=16, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT),
        ])
        page.update()

    def close_sheet() -> None:
        try:
            page.pop_dialog()
        except Exception:
            pass

    def show_source_sheet(item: dict[str, Any], entry: dict[str, Any], sources: list[dict[str, Any]], for_download: bool = False) -> None:
        valid = [source for source in sources if source.get("playable")]
        if not valid:
            fallback = next((source for source in sources if source.get("provider") == "Vidsrc"), None)
            if fallback and not for_download:
                show_vidsrc_webview(item, fallback, entry)
            else:
                notify("لم يتوفر رابط مناسب لهذا الإجراء حالياً.")
            return

        def choose(_event: Any, chosen: dict[str, Any]) -> None:
            close_sheet()
            if for_download:
                start_download(item, chosen, entry)
            else:
                show_player(item, chosen, entry)

        rows = []
        for source in valid:
            rows.append(ft.Container(bgcolor=SURFACE_LIGHT, border_radius=14, padding=12, content=ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[red_button("ابدأ التنزيل" if for_download else "مشاهدة", lambda event, chosen=source: choose(event, chosen), ft.Icons.DOWNLOAD if for_download else ft.Icons.PLAY_ARROW), ft.Text(source_title(source), color=TEXT, size=13, text_align=ft.TextAlign.RIGHT)])))
        sheet = ft.BottomSheet(content=ft.Container(bgcolor=SURFACE, padding=18, content=ft.Column(spacing=10, tight=True, controls=[ft.Text("اختر الجودة", color=TEXT, size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), *rows, ft.TextButton("إلغاء", on_click=lambda _event: close_sheet())])))
        page.show_dialog(sheet)

    async def resolve_sources_async(item: dict[str, Any], entry: dict[str, Any], for_download: bool = False) -> None:
        notify("جارٍ الاتصال بـ Consumet لاستخراج المصادر...")
        try:
            sources = await asyncio.to_thread(data.live_sources, item, entry)
        except (requests.RequestException, ValueError, KeyError) as error:
            notify(f"تعذر استخراج المصادر: {error}")
            return
        show_source_sheet(item, entry, sources, for_download)

    def start_watch(item: dict[str, Any], entry: dict[str, Any]) -> None:
        page.run_task(resolve_sources_async, item, entry, False)

    def start_download_choice(item: dict[str, Any], entry: dict[str, Any]) -> None:
        page.run_task(resolve_sources_async, item, entry, True)

    def download_file(download_id: str, source: dict[str, Any]) -> None:
        state = downloads[download_id]
        try:
            target_dir = Path(os.getenv("FLET_APP_STORAGE_DATA", ".")) / "downloads"
            target_dir.mkdir(parents=True, exist_ok=True)
            title = str(state.get("title", "video"))
            safe_name = "".join(ch if ch.isalnum() or ch in "-_ " else "_" for ch in title).strip() or "video"
            path = target_dir / f"{safe_name}_{download_id[-6:]}.mp4"
            with data.session.get(str(source.get("url")), stream=True, timeout=(10, 60)) as response:
                response.raise_for_status()
                total = int(response.headers.get("content-length") or 0)
                state["total"] = total
                state["downloaded"] = 0
                with path.open("wb") as output:
                    for chunk in response.iter_content(chunk_size=128 * 1024):
                        if state.get("cancelled"):
                            state["status"] = "ملغى"
                            return
                        if chunk:
                            output.write(chunk)
                            state["downloaded"] += len(chunk)
                            state["progress"] = state["downloaded"] / total if total else -1
            state["path"] = str(path)
            state["progress"] = 1
            state["status"] = "مكتمل"
        except Exception as error:
            state["status"] = f"فشل: {error}"

    async def download_worker(download_id: str, source: dict[str, Any]) -> None:
        task = asyncio.create_task(asyncio.to_thread(download_file, download_id, source))
        while not task.done():
            render_downloads()
            await asyncio.sleep(0.35)
        await task
        render_downloads()
        notify("اكتمل التنزيل." if downloads[download_id].get("status") == "مكتمل" else downloads[download_id].get("status", "انتهى التنزيل"))

    def start_download(item: dict[str, Any], source: dict[str, Any], entry: dict[str, Any]) -> None:
        if source.get("is_m3u8"):
            notify("هذه الجودة HLS بصيغة m3u8 ولا يمكن تنزيلها كملف مباشر من التطبيق.")
            return
        download_id = f"{item_key(item)}-{entry.get('episode_number', 1)}-{int(time.time() * 1000)}"
        downloads[download_id] = {"title": f"{item.get('title', 'محتوى')} - {entry.get('title', '')}", "quality": source.get("quality", "auto"), "status": "جاري التحضير", "progress": 0, "downloaded": 0, "total": 0, "cancelled": False, "path": ""}
        render_downloads()
        page.run_task(download_worker, download_id, source)

    def cancel_download(download_id: str) -> None:
        if download_id in downloads:
            downloads[download_id]["cancelled"] = True
            downloads[download_id]["status"] = "جارٍ الإلغاء"
            render_downloads()

    def open_download(download_id: str) -> None:
        path = downloads.get(download_id, {}).get("path")
        if not path:
            notify("الملف لم يكتمل تنزيله بعد.")
            return
        try:
            page.launch_url(Path(path).as_uri())
        except Exception as error:
            notify(f"الملف محفوظ في: {path}")

    def render_downloads() -> None:
        nonlocal current_view
        current_view = "downloads"
        controls: list[ft.Control] = [ft.Text("التنزيلات", color=TEXT, size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT)]
        if not downloads:
            controls.append(ft.Container(padding=40, alignment=ft.alignment.Alignment(0, 0), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Icon(ft.Icons.DOWNLOAD, color=MUTED, size=48), ft.Text("لا توجد تنزيلات بعد", color=MUTED, size=16)])))
        else:
            for download_id, state in downloads.items():
                progress = state.get("progress", 0)
                progress_control = ft.ProgressBar(value=progress if progress >= 0 else None, color=ACCENT, bgcolor=SURFACE)
                actions = [ft.IconButton(icon=ft.Icons.OPEN_IN_NEW, icon_color=TEXT, on_click=lambda _event, chosen=download_id: open_download(chosen))] if state.get("status") == "مكتمل" else [ft.IconButton(icon=ft.Icons.CANCEL, icon_color=ACCENT, on_click=lambda _event, chosen=download_id: cancel_download(chosen))]
                controls.append(ft.Container(bgcolor=SURFACE, border_radius=14, padding=12, content=ft.Column(spacing=7, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[*actions, ft.Text(f"{state.get('title', '')} • {state.get('quality', '')}", color=TEXT, size=13, text_align=ft.TextAlign.RIGHT)]), progress_control, ft.Text(str(state.get("status", "")), color=MUTED, size=11, text_align=ft.TextAlign.RIGHT)])))
        content.controls.clear()
        content.controls.extend(controls)
        page.update()

    def episode_row(item: dict[str, Any], entry: dict[str, Any]) -> ft.Container:
        duration = str(entry.get("duration") or "")
        subtitle = str(entry.get("subtitle") or "") + (f" • {duration}" if duration else "")
        return ft.Container(bgcolor=SURFACE_LIGHT, border_radius=12, padding=10, content=ft.Column(spacing=7, controls=[ft.Text(str(entry.get("title", "الحلقة")), color=TEXT, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), ft.Text(subtitle, color=MUTED, size=12, text_align=ft.TextAlign.RIGHT), ft.Row(alignment=ft.MainAxisAlignment.END, controls=[red_button("مشاهدة", lambda _event, chosen=entry: start_watch(item, chosen), ft.Icons.PLAY_ARROW), ft.TextButton("تحميل", on_click=lambda _event, chosen=entry: start_download_choice(item, chosen))])]))

    def fallback_entry(item: dict[str, Any]) -> dict[str, Any]:
        return movie_entry(item) if item.get("kind") == "movie" else {"episode_id": str(item.get("id") or item.get("title", "")), "episode_number": 1, "season_number": 1, "title": "الحلقة 1", "subtitle": "مصدر حي من Consumet عند الضغط على التشغيل"}

    def render_detail_shell(item: dict[str, Any], details: dict[str, Any], episodes: list[dict[str, Any]], seasons: list[int], token: int, loading: bool = False) -> None:
        if token != details_token:
            return
        is_serial = item.get("kind") in {"series", "cartoon", "anime"}
        episode_controls: list[ft.Control] = [ft.Text("الحلقات", color=TEXT, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT)]
        if seasons:
            episode_controls.append(ft.Dropdown(label="اختر الموسم", value=str(seasons[0]), options=[ft.dropdown.Option(str(season), f"الموسم {season}") for season in seasons], bgcolor=SURFACE_LIGHT, color=TEXT, label_style=ft.TextStyle(color=MUTED), on_change=lambda event: page.run_task(load_season_async, item, int(event.control.value), token)))
        if loading:
            episode_controls.append(ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.ProgressRing(color=ACCENT), ft.Text("جارٍ تحميل الحلقات...", color=MUTED)]))
        elif episodes:
            episode_controls.extend(episode_row(item, episode) for episode in episodes)
        elif is_serial:
            episode_controls.append(ft.Text("لا تتوفر حلقات لهذا العمل حالياً.", color=MUTED, text_align=ft.TextAlign.RIGHT))
        controls = [
            ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_color=TEXT, on_click=lambda _event: render_home()), ft.Text("تفاصيل العمل", color=TEXT, size=22)]),
            ft.Container(bgcolor=SURFACE, border_radius=18, padding=14, content=ft.Column(spacing=12, controls=[ft.Stack(width=300, height=290, controls=[item_image(item, 300, 290), ft.Container(alignment=ft.alignment.Alignment(1, -1), content=favorite_button(item))]), ft.Text(str(item.get("title", "بدون عنوان")), color=TEXT, size=25, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), ft.Text(f"{item.get('rating', '—')} ★ • {item.get('subtitle', '')}", color="#FFD54A", text_align=ft.TextAlign.RIGHT), ft.Text(str(details.get("overview") or item.get("overview") or "لا يوجد وصف متوفر حالياً."), color="#D5D9E0", size=15, text_align=ft.TextAlign.RIGHT), red_button("إضافة للمفضلة" if item_key(item) not in favorites else "إزالة من المفضلة", lambda _event: toggle_favorite(item), ft.Icons.FAVORITE), *episode_controls]))
        ]
        content.controls.clear()
        content.controls.extend(controls)
        page.update()

    async def load_season_async(item: dict[str, Any], season_number: int, token: int) -> None:
        if token != details_token:
            return
        render_detail_shell(item, {}, [], [season_number], token, True)
        try:
            episodes = await asyncio.to_thread(data.season_episodes, item.get("id"), season_number)
        except (requests.RequestException, ValueError, KeyError):
            episodes = []
        render_detail_shell(item, {}, episodes, [season_number], token, False)

    async def populate_details_async(item: dict[str, Any], token: int) -> None:
        try:
            details = await asyncio.to_thread(data.details, item)
        except (requests.RequestException, ValueError, KeyError):
            details = {}
        enriched = dict(item)
        if details.get("overview"):
            enriched["overview"] = details["overview"]
        selected_item = enriched
        seasons = []
        for season in details.get("seasons", []) if isinstance(details, dict) else []:
            try:
                number = int(season.get("season_number", 0))
                if number > 0:
                    seasons.append(number)
            except (TypeError, ValueError):
                pass
        render_detail_shell(enriched, details, [], seasons, token, item.get("kind") in {"series", "cartoon", "anime"})
        if item.get("kind") == "movie":
            render_detail_shell(enriched, details, [movie_entry(enriched)], [], token, False)
            return
        try:
            episodes = await asyncio.to_thread(data.gogoanime_episodes, str(item.get("title", ""))) if item.get("kind") == "anime" else await asyncio.to_thread(data.season_episodes, item.get("id"), seasons[0]) if seasons else []
        except (requests.RequestException, ValueError, KeyError):
            episodes = []
        render_detail_shell(enriched, details, episodes, seasons, token, False)

    def open_details(item: dict[str, Any]) -> None:
        nonlocal current_view, selected_item, details_token
        current_view = "details"
        selected_item = item
        details_token += 1
        token = details_token
        render_detail_shell(item, {}, [], [], token, True)
        page.run_task(populate_details_async, item, token)

    async def load_catalog_async() -> None:
        nonlocal catalog_loading
        if catalog_loading:
            return
        catalog_loading = True
        render_home()
        try:
            fresh = await asyncio.to_thread(data.load_catalog)
            for key in catalogs:
                values = fresh.get(key, []) if isinstance(fresh, dict) else []
                catalogs[key] = [format_item(value, value.get("kind") if isinstance(value, dict) else None) for value in values if isinstance(value, dict)]
            notify("تم تحميل الكتالوج.")
        except (requests.RequestException, ValueError, KeyError) as error:
            notify(f"تعذر تحميل الكتالوج: {error}")
        finally:
            catalog_loading = False
            if current_view == "home":
                render_home()

    async def perform_search_async(query: str) -> None:
        nonlocal search_loading, current_view
        query = query.strip()
        if not query:
            render_home()
            return
        if search_loading:
            return
        search_loading = True
        current_view = "search"
        content.controls.clear()
        content.controls.extend([ft.Text("نتائج البحث", color=TEXT, size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), ft.Row(alignment=ft.MainAxisAlignment.CENTER, controls=[ft.ProgressRing(color=ACCENT), ft.Text("جارٍ البحث...", color=MUTED)])])
        page.update()
        try:
            results = await asyncio.to_thread(data.search, query)
            results = [format_item(value, value.get("kind") if isinstance(value, dict) else None) for value in results if isinstance(value, dict)]
            content.controls.clear()
            content.controls.extend([ft.Text(f"نتائج البحث عن «{query}»", color=TEXT, size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), ft.Row(wrap=True, spacing=10, run_spacing=10, controls=[poster_card(item) for item in results] or [ft.Text("لا توجد نتائج.", color=MUTED, size=16, text_align=ft.TextAlign.RIGHT)])])
            page.update()
        except (requests.RequestException, ValueError, KeyError) as error:
            notify(f"تعذر البحث: {error}")
        finally:
            search_loading = False

    def render_search() -> None:
        nonlocal current_view
        current_view = "search"
        content.controls.clear()
        content.controls.extend([ft.Text("ابحث عن فيلم أو مسلسل أو أنمي", color=TEXT, size=22, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), ft.Text("اكتب الكلمة ثم اضغط زر البحث أو Enter.", color=MUTED, text_align=ft.TextAlign.RIGHT)])
        page.update()

    def render_favorites() -> None:
        nonlocal current_view
        current_view = "favorites"
        all_items = [item for key in catalogs for item in catalogs[key]]
        items = [item for item in all_items if item_key(item) in favorites]
        content.controls.clear()
        content.controls.extend([ft.Text("المفضلة", color=TEXT, size=24, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.RIGHT), ft.Row(wrap=True, spacing=10, run_spacing=10, controls=[poster_card(item) for item in items] or [ft.Container(padding=40, alignment=ft.alignment.Alignment(0, 0), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, controls=[ft.Icon(ft.Icons.FAVORITE_BORDER, color=MUTED, size=48), ft.Text("قائمة المفضلة فارغة", color=MUTED, size=16), ft.Text("اضغط القلب على أي بطاقة لحفظها هنا.", color=MUTED, size=13)]))])])
        page.update()

    def render_view(view: str) -> None:
        if view == "home":
            render_home()
        elif view == "search":
            render_search()
        elif view == "downloads":
            render_downloads()
        else:
            render_favorites()

    def nav_button(label: str, icon: Any, view: str) -> ft.Container:
        selected = current_view == view
        return ft.Container(expand=True, padding=8, border_radius=12, bgcolor="#332F0D16" if selected else None, on_click=lambda _event, chosen=view: render_view(chosen), content=ft.Column(horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=2, controls=[ft.Icon(icon, color=ACCENT if selected else MUTED, size=22), ft.Text(label, color=TEXT if selected else MUTED, size=11)]))

    header = ft.Container(bgcolor=BACKGROUND, padding=ft.Padding(left=16, top=18, right=16, bottom=8), content=ft.Column(spacing=12, controls=[ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Palestine Movie 🇵🇸", color=TEXT, size=25, weight=ft.FontWeight.BOLD), ft.Icon(ft.Icons.LOCAL_MOVIES, color=ACCENT, size=30)]), ft.Row(spacing=8, controls=[search, ft.IconButton(icon=ft.Icons.SEARCH, icon_color=TEXT, bgcolor=ACCENT, tooltip="بحث", on_click=lambda _event: page.run_task(perform_search_async, search.value or ""))])]))
    bottom_nav = ft.Container(bgcolor=SURFACE, padding=ft.Padding(left=8, top=7, right=8, bottom=12), content=ft.Row(spacing=4, controls=[nav_button("الرئيسية", ft.Icons.HOME, "home"), nav_button("البحث", ft.Icons.SEARCH, "search"), nav_button("التنزيلات", ft.Icons.DOWNLOAD, "downloads"), nav_button("المفضلة", ft.Icons.FAVORITE, "favorites")]))
    page.add(ft.Column(expand=True, spacing=0, controls=[header, ft.Container(expand=True, padding=ft.Padding(left=16, top=0, right=16, bottom=0), content=content), bottom_nav]))
    render_home()
    page.run_task(load_catalog_async)



if __name__ == "__main__":
    ft.run(
        main,
        host="0.0.0.0",
        port=int(os.getenv("PORT", "5000")),
        view=ft.AppView.WEB_BROWSER,
    )
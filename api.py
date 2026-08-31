"""Server-side TMDB proxy. Run: uvicorn api:app --host 0.0.0.0 --port $PORT"""
from __future__ import annotations

import os
import time
from typing import Any

import requests
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.getenv("TMDB_API_KEY", "").strip()
CACHE_TTL = 120
RATE_LIMIT = 60
_cache: dict[str, tuple[float, Any]] = {}
_hits: dict[str, list[float]] = {}

app = FastAPI(title="Palestine Movie API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET"], allow_headers=["*"])
LABELS = {"movie": "فيلم", "series": "مسلسل", "anime": "أنمي", "cartoon": "كرتون"}

def guard(request: Request) -> None:
    now = time.monotonic()
    address = request.client.host if request.client else "unknown"
    recent = [stamp for stamp in _hits.get(address, []) if stamp > now - 60]
    if len(recent) >= RATE_LIMIT:
        raise HTTPException(status_code=429, detail="طلبات كثيرة، حاول لاحقاً")
    recent.append(now)
    _hits[address] = recent
    if not TMDB_API_KEY:
        raise HTTPException(status_code=503, detail="خدمة الكتالوج غير مهيأة")

def tmdb(path: str, params: dict[str, Any] | None = None) -> Any:
    query = {"api_key": TMDB_API_KEY, "language": "ar-SA"}
    if params:
        query.update(params)
    cache_key = path + repr(sorted((k, v) for k, v in query.items() if k != "api_key"))
    cached = _cache.get(cache_key)
    if cached and cached[0] > time.monotonic():
        return cached[1]
    try:
        response = requests.get(f"{TMDB_BASE_URL}/{path.lstrip('/')}", params=query, timeout=15)
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as error:
        raise HTTPException(status_code=502, detail="تعذر الوصول إلى خدمة TMDB") from error
    _cache[cache_key] = (time.monotonic() + CACHE_TTL, payload)
    return payload

def item(raw: dict[str, Any], kind: str | None = None) -> dict[str, Any]:
    media_type = kind or str(raw.get("media_type") or "movie")
    date = str(raw.get("release_date") or raw.get("first_air_date") or "")
    year = date[:4] if date else "جديد"
    title = str(raw.get("title") or raw.get("name") or "بدون عنوان")
    try:
        rating = f"{float(raw.get('vote_average') or 0):.1f}"
    except (TypeError, ValueError):
        rating = "—"
    return {"id": raw.get("id"), "title": title, "subtitle": f"{LABELS.get(media_type, 'محتوى')} • {year}", "rating": rating, "poster": raw.get("poster_path"), "backdrop": raw.get("backdrop_path") or raw.get("poster_path"), "overview": str(raw.get("overview") or "لا يوجد وصف متوفر حالياً."), "kind": media_type}

def results(path: str, params: dict[str, Any], kind: str) -> list[dict[str, Any]]:
    payload = tmdb(path, params)
    raw = payload.get("results", []) if isinstance(payload, dict) else []
    return [item(entry, kind) for entry in raw if isinstance(entry, dict)]

@app.get("/health")
def health() -> dict[str, bool]:
    return {"ok": bool(TMDB_API_KEY)}

@app.get("/catalog")
def catalog(request: Request) -> dict[str, list[dict[str, Any]]]:
    guard(request)
    return {"movies": results("movie/popular", {"page": 1}, "movie"), "series": results("tv/popular", {"page": 1}, "series"), "anime": results("discover/tv", {"with_genres": 16, "with_original_language": "ja", "sort_by": "popularity.desc", "page": 1}, "anime"), "cartoons": results("discover/tv", {"with_genres": 16, "without_original_language": "ja", "sort_by": "popularity.desc", "page": 1}, "cartoon")}

@app.get("/search")
def search(request: Request, q: str = Query(min_length=1, max_length=120)) -> list[dict[str, Any]]:
    guard(request)
    payload = tmdb("search/multi", {"query": q.strip(), "include_adult": False, "page": 1})
    output = []
    for raw in payload.get("results", []) if isinstance(payload, dict) else []:
        if raw.get("media_type") == "movie":
            output.append(item(raw, "movie"))
        elif raw.get("media_type") == "tv":
            output.append(item(raw, "anime" if raw.get("original_language") == "ja" else "series"))
    return output

@app.get("/details/{media_type}/{media_id}")
def details(request: Request, media_type: str, media_id: int) -> dict[str, Any]:
    guard(request)
    if media_type not in {"movie", "tv"} or media_id < 1:
        raise HTTPException(status_code=400, detail="معرّف محتوى غير صالح")
    return tmdb(f"{media_type}/{media_id}")

@app.get("/season/{media_id}/{season_number}")
def season(request: Request, media_id: int, season_number: int) -> list[dict[str, Any]]:
    guard(request)
    if media_id < 1 or season_number < 0:
        raise HTTPException(status_code=400, detail="بيانات الموسم غير صالحة")
    payload = tmdb(f"tv/{media_id}/season/{season_number}")
    episodes = payload.get("episodes", []) if isinstance(payload, dict) else []
    return [{"episode_id": str(ep.get("id") or f"{media_id}-s{season_number}-e{ep.get('episode_number')}"), "episode_number": ep.get("episode_number", 1), "season_number": season_number, "title": str(ep.get("name") or f"الحلقة {ep.get('episode_number', 1)}"), "subtitle": f"الموسم {season_number} • الحلقة {ep.get('episode_number', 1)}"} for ep in episodes if ep.get("episode_number") is not None]

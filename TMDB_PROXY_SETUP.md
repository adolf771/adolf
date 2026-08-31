# Secure TMDB setup

The APK must never receive TMDB_API_KEY. The mobile client calls api.py, and only that server calls TMDB.

## 1. Run the proxy

Deploy this repository as a web service with:

    uvicorn api:app --host 0.0.0.0 --port $PORT

Add TMDB_API_KEY to the server's Replit Secrets. Do not add it to the APK build environment, GitHub Actions, screenshots, or source files.

Check the service at /health; it must return {"ok": true}.

## 2. Configure the APK build

Create a GitHub Actions repository variable named TMDB_PROXY_URL containing the public HTTPS URL of the proxy (without a trailing slash). This is a public endpoint, not a secret.

Before flet build apk in .github/workflows/build.yml, generate the ignored build-only file:

    test -n "$TMDB_PROXY_URL" || { echo "Repository variable TMDB_PROXY_URL is required"; exit 1; }
    python - "$TMDB_PROXY_URL" <<'PY'
    from pathlib import Path
    import sys
    Path("build_config.py").write_text(
        "TMDB_PROXY_URL = " + repr(sys.argv[1]) + "\n",
        encoding="utf-8",
    )
    PY

The workflow must compile both main.py and api.py. The generated build_config.py contains only the public proxy URL and is ignored by Git.

## 3. Rotate the old key

If the old TMDB key was shown in a screenshot or pasted into chat, revoke it in TMDB and create a replacement. Put the replacement only in the proxy server's Secrets.

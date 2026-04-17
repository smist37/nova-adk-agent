# TODO: yt-dlp is currently the primary fetch path; eventually it should be the fallback behind a cleaner caption API.
import json
import re
import urllib.request

import yt_dlp

_YT_ID_RE = re.compile(
    r"(?:youtube\.com/(?:watch\?v=|embed/|v/|shorts/)|youtu\.be/)([A-Za-z0-9_-]{11})"
)

_TRANSCRIPT_CHAR_CAP = 60_000


def fetch_transcript(url: str) -> dict:
    """Fetch the transcript of a YouTube video via yt-dlp.

    Prefers manually-authored subtitles; falls back to auto-generated captions.
    Uses YouTube's json3 caption format when available (clean text, no rolling
    duplicates typical of auto-caption VTT). Returns {"transcript": str,
    "video_id": str} on success, or {"error": str}. Transcript is truncated.
    """
    if not _YT_ID_RE.search(url):
        return {"error": f"Could not extract a YouTube video ID from URL: {url}"}

    opts = {
        "skip_download": True,
        "writesubtitles": True,
        "writeautomaticsub": True,
        "quiet": True,
        "no_warnings": True,
    }
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except yt_dlp.utils.DownloadError as exc:
        return {"error": f"yt-dlp could not load video: {exc}"}
    except Exception as exc:
        return {"error": f"yt-dlp failed: {exc}"}

    video_id = info.get("id") or _YT_ID_RE.search(url).group(1)
    tracks = _pick_caption_track(info.get("subtitles") or {}) or _pick_caption_track(
        info.get("automatic_captions") or {}
    )
    if not tracks:
        return {"error": f"No English captions available for video {video_id}."}

    by_ext = {fmt.get("ext"): fmt for fmt in tracks}
    chosen = by_ext.get("json3") or by_ext.get("srv3") or by_ext.get("vtt") or tracks[0]

    req = urllib.request.Request(
        chosen["url"],
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:
        return {"error": f"Caption fetch failed: {exc}"}

    ext = chosen.get("ext")
    if ext == "json3":
        text = _parse_json3(raw)
    elif ext and ext.startswith("srv"):
        text = _parse_srv_xml(raw)
    else:
        text = _parse_vtt(raw)

    truncated = text[:_TRANSCRIPT_CHAR_CAP]
    result: dict = {"transcript": truncated, "video_id": video_id}
    if len(text) > _TRANSCRIPT_CHAR_CAP:
        result["truncated"] = True
        result["original_chars"] = len(text)
    return result


def _pick_caption_track(tracks_by_lang: dict) -> list | None:
    for lang in ("en", "en-US", "en-GB", "en-orig"):
        if lang in tracks_by_lang:
            return tracks_by_lang[lang]
    for lang, tracks in tracks_by_lang.items():
        if lang.startswith("en"):
            return tracks
    return None


def _parse_json3(raw: str) -> str:
    data = json.loads(raw)
    parts: list[str] = []
    for event in data.get("events") or []:
        for seg in event.get("segs") or []:
            t = seg.get("utf8")
            if t and t != "\n":
                parts.append(t)
    return " ".join("".join(parts).split())


def _parse_srv_xml(raw: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", raw).split())


def _parse_vtt(raw: str) -> str:
    out: list[str] = []
    prev: str | None = None
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith(("WEBVTT", "NOTE", "STYLE")) or "-->" in line:
            continue
        if line.isdigit():
            continue
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line or line == prev:
            continue
        out.append(line)
        prev = line
    return " ".join(out)

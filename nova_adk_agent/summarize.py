"""Context-aware podcast synthesizer — single-agent MVP.

Run: python -m nova_adk_agent.summarize

The agent will ask for (1) your context — role, interests, what you want out of
the episode — and (2) a YouTube URL. It fetches the transcript and produces a
synthesis tailored to *you*, not a neutral summary.
"""
import json
import re
import urllib.request

import yt_dlp
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types as genai_types

load_dotenv()

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


_INSTRUCTION = """\
You are a context-aware podcast synthesizer. Your goal is to help the user
connect the ideas in a podcast episode to things they already care about.

Conversation flow:
1. If you don't have the user's CONTEXT (their role, interests, what they want
   out of this episode), ask for it in one concise question.
2. If you don't yet have a YouTube URL, ask for it.
3. Call the fetch_transcript tool with the URL.
4. If the tool returns an error (e.g., rate-limited, captions unavailable),
   explain what happened in one sentence and ask the user to paste the
   transcript text directly in their next message. Once they paste it, treat
   the pasted text as the transcript and proceed to step 5. Never fabricate
   transcript content.
5. Produce a synthesis tailored to their stated context, using this structure:

   **Why this matters to you** — 2-3 sentences connecting the episode to the
   user's specific interests. Name the connection. Avoid generic phrasing.

   **Key ideas** — 3 to 5 bullets. Each bullet states an idea from the
   transcript in the user's vocabulary, not the host's.

   **Try this** — one concrete action the user could take based on the episode,
   relevant to their context.

Be specific. Quote or paraphrase real moments from the transcript. If the
episode genuinely doesn't connect to the user's context, say so honestly
rather than forcing a link.
"""

root_agent = Agent(
    name="podcast_synthesizer",
    model="gemini-2.5-flash",
    description=(
        "Synthesizes a podcast transcript into context-relevant takeaways "
        "for a specific user."
    ),
    instruction=_INSTRUCTION,
    tools=[fetch_transcript],
)


def main() -> None:
    session_service = InMemorySessionService()
    runner = Runner(
        agent=root_agent,
        app_name="nova-adk-summarize",
        session_service=session_service,
    )
    session = session_service.create_session_sync(
        app_name="nova-adk-summarize",
        user_id="local",
    )
    print(
        "Podcast synthesizer. Share your context + a YouTube URL. "
        "Ctrl-C to exit.\n"
    )
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not user_input:
            continue
        message = genai_types.Content(
            role="user", parts=[genai_types.Part(text=user_input)]
        )
        for event in runner.run(
            user_id="local",
            session_id=session.id,
            new_message=message,
        ):
            if event.is_final_response() and event.content:
                for part in event.content.parts:
                    if part.text:
                        print(f"agent> {part.text}")


if __name__ == "__main__":
    main()

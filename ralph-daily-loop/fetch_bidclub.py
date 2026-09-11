#!/usr/bin/env python3
"""Fetch recent BidClub podcast episodes into the daily-report source contract.

The scanner keeps discovery small: it reads only the newest API page, filters by
the report window, and fetches details for recent candidates. Full transcripts
remain on BidClub and are never copied into the stage snapshot.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime, timedelta, timezone
from html import unescape
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_URL = "https://bidclub.ai/api/v1/episodes"
BIDCLUB_URL = "https://bidclub.ai"
USER_AGENT = "AI-News-Digest/BidClubScanner (+https://github.com/chengjialu8888/AI_News_Digest)"


def parse_timestamp(value: Any) -> datetime | None:
    """Parse an ISO timestamp and normalize it to UTC."""
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def episode_datetime(episode: dict[str, Any]) -> datetime | None:
    return parse_timestamp(episode.get("published_at")) or parse_timestamp(
        episode.get("date")
    )


def is_recent(episode: dict[str, Any], since: datetime, today: date) -> bool:
    published = episode_datetime(episode)
    if published:
        return published >= since
    # A date-only record is still useful when the API omits a timestamp. Keep
    # the fallback conservative at the report's current UTC date.
    raw_date = str(episode.get("date") or "")[:10]
    try:
        return date.fromisoformat(raw_date) >= today
    except ValueError:
        return False


def fetch_json(url: str, timeout: int = 30) -> Any:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        return json.load(response)


def compact_markdown(value: Any, limit: int = 2400) -> str:
    """Keep a readable evidence excerpt without moving a transcript downstream."""
    text = unescape(str(value or ""))
    text = re.sub(r"```.*?```", " ", text, flags=re.DOTALL)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)
    text = re.sub(r"[*_`~]", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.MULTILINE)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def detail_url(slug: str) -> str:
    return f"{API_URL}/{slug}"


def bidclub_episode_url(slug: str) -> str:
    return f"{BIDCLUB_URL}/e/{slug}"


def make_record(episode: dict[str, Any], detail: dict[str, Any] | None) -> dict[str, Any]:
    detail = detail or {}
    show = episode.get("shows")
    if not isinstance(show, dict):
        show = detail.get("shows")
    if not isinstance(show, dict):
        show = {}
    show_name = show.get("name") or episode.get("show_id") or "Unknown show"
    title = (
        episode.get("display_title")
        or detail.get("display_title")
        or episode.get("title")
        or "Untitled podcast episode"
    )
    slug = str(episode.get("slug") or detail.get("slug") or "").strip()
    original_url = (
        episode.get("source_url")
        or detail.get("source_url")
        or episode.get("rss_url")
        or episode.get("youtube_url")
        or bidclub_episode_url(slug)
    )
    tldr = detail.get("tldr_md") or detail.get("tldr_md_alt")
    digest = detail.get("digest_md") or detail.get("digest_md_alt")
    evidence_excerpt = compact_markdown(tldr or digest or episode.get("dek"), 2400)
    summary = compact_markdown(episode.get("dek") or tldr or digest, 900)
    published = episode_datetime(episode)
    date_value = episode.get("date") or (published.date().isoformat() if published else "")
    detail_show = detail.get("shows") or {}
    hosts = show.get("hosts") or (detail_show.get("hosts") if isinstance(detail_show, dict) else None)

    return {
        "title": title,
        "source": f"BidClub · {show_name}",
        "url": original_url,
        "summary": summary,
        "board": "海外建设者",
        "date": date_value,
        "published_at": episode.get("published_at"),
        "signal_level": "⚪",
        "cross_validated": False,
        "podcast": True,
        "podcast_source": "BidClub.ai",
        "podcast_show": show_name,
        "podcast_hosts": hosts,
        "podcast_duration_min": episode.get("duration_min"),
        "episode_slug": slug,
        "bidclub_url": bidclub_episode_url(slug),
        "bidclub_detail_url": detail_url(slug),
        "podcast_evidence_excerpt": evidence_excerpt,
        "podcast_detail_status": "fetched" if detail else "metadata_only",
        "transcript_available": bool(detail.get("transcript_md") or detail.get("transcript_md_alt")),
        "source_links": [url for url in (original_url, bidclub_episode_url(slug)) if url],
        "provenance": episode.get("provenance") or detail.get("provenance") or [],
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def scan(args: argparse.Namespace) -> int:
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=args.since_hours)
    meta: dict[str, Any] = {
        "source": "BidClub.ai",
        "api_url": args.api_url,
        "checked_at": now.isoformat(),
        "since": since.isoformat(),
        "status": "ok",
        "new_count": 0,
        "detail_limit": args.detail_limit,
        "errors": [],
    }

    try:
        query = urlencode({"limit": min(max(args.page_limit, 1), 100), "offset": 0})
        payload = fetch_json(f"{args.api_url}?{query}", args.timeout)
        episodes = payload.get("episodes", []) if isinstance(payload, dict) else []
        if not isinstance(episodes, list):
            raise ValueError("API response field 'episodes' is not an array")
        meta["page_count"] = len(episodes)
        meta["next_offset"] = (payload.get("pagination") or {}).get("next_offset")
    except Exception as exc:  # A source outage should not block the other Goals.
        meta["status"] = "error"
        meta["errors"].append(f"episode index: {exc}")
        write_json(args.out, [])
        write_json(args.meta_out, meta)
        return 0

    recent = [
        episode
        for episode in episodes
        if isinstance(episode, dict) and is_recent(episode, since, now.date())
    ]
    recent.sort(key=lambda item: episode_datetime(item) or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    recent = recent[: args.max_episodes]
    meta["recent_candidates"] = len(recent)

    records: list[dict[str, Any]] = []
    detail_failures = 0
    for index, episode in enumerate(recent):
        slug = str(episode.get("slug") or "").strip()
        detail: dict[str, Any] | None = None
        if slug and index < args.detail_limit:
            try:
                payload = fetch_json(detail_url(slug), args.timeout)
                if isinstance(payload, dict):
                    detail = payload
            except Exception as exc:
                detail_failures += 1
                meta["errors"].append(f"detail {slug}: {exc}")
        record = make_record(episode, detail)
        if index >= args.detail_limit:
            record["podcast_detail_status"] = "skipped_limit"
        records.append(record)

    meta["new_count"] = len(records)
    meta["detail_fetched"] = min(len(records), args.detail_limit)
    meta["detail_failures"] = detail_failures
    meta["latest_slugs"] = [item.get("episode_slug") for item in records[:5]]
    if detail_failures:
        meta["status"] = "partial"

    write_json(args.out, records)
    write_json(args.meta_out, meta)
    state = {
        "last_scan_at": meta["checked_at"],
        "last_status": meta["status"],
        "last_new_count": len(records),
        "last_latest_slugs": meta["latest_slugs"],
    }
    write_json(args.state, state)
    print(f"BidClub scan: {len(records)} recent episodes ({meta['status']})")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True, help="JSON source snapshot path")
    parser.add_argument("--meta-out", type=Path, required=True, help="scan metadata path")
    parser.add_argument("--state", type=Path, required=True, help="last-scan state path")
    parser.add_argument("--api-url", default=API_URL)
    parser.add_argument("--since-hours", type=int, default=24)
    parser.add_argument("--page-limit", type=int, default=100)
    parser.add_argument("--max-episodes", type=int, default=30)
    parser.add_argument("--detail-limit", type=int, default=20)
    parser.add_argument("--timeout", type=int, default=30)
    return parser


if __name__ == "__main__":
    sys.exit(scan(build_parser().parse_args()))

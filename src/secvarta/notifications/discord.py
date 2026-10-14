"""Discord webhook delivery for SecVarta daily digests."""

import os
from pathlib import Path
from urllib.parse import urlparse

import httpx
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")

DISCORD_WEBHOOK_ENV = "SECVARTA_DISCORD_WEBHOOK_URL"


def _truncate(value: str, max_length: int) -> str:
    value = " ".join((value or "").split())
    if len(value) <= max_length:
        return value
    return value[: max_length - 1].rstrip() + "…"


def _is_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def build_digest_payload(articles: list, digest_date: str) -> dict:
    """Build a Discord webhook payload with at most 10 article embeds."""
    if not articles:
        return {
            "content": f"**SecVarta Daily Threat Brief** · {digest_date}",
            "embeds": [
                {
                    "title": "No new articles found today",
                    "description": (
                        "No stored articles had a publication date matching "
                        "today's Asia/Kolkata calendar date."
                    ),
                }
            ],
            "allowed_mentions": {"parse": []},
        }

    embeds = []
    for article in articles[:10]:
        title = _truncate(
            getattr(article, "title", "Untitled article") or "Untitled article", 120
        )
        url = getattr(article, "url", "") or ""
        summary = _truncate(getattr(article, "summary", "") or "", 200)
        published_at = _truncate(getattr(article, "published_at", "") or "Unknown", 80)
        cves = sorted({cve.cve_id.upper() for cve in getattr(article, "cves", [])})

        embed = {"title": title}
        if _is_http_url(url):
            embed["url"] = url
        if summary:
            embed["description"] = summary
        fields = [{"name": "Published", "value": published_at, "inline": True}]
        if cves:
            fields.append(
                {
                    "name": "CVEs",
                    "value": _truncate(", ".join(cves), 120),
                    "inline": True,
                }
            )
        embed["fields"] = fields
        embeds.append(embed)

    return {
        "content": (
            f"**SecVarta Daily Threat Brief** · {digest_date} · "
            f"{len(articles[:10])} article(s)"
        ),
        "embeds": embeds,
        # Feed content is untrusted; disable @everyone and role mentions.
        "allowed_mentions": {"parse": []},
    }


def send_digest(articles: list, digest_date: str) -> None:
    """Send the digest to Discord. The webhook URL is never included in our errors."""
    webhook_url = os.getenv(DISCORD_WEBHOOK_ENV, "").strip()
    if not webhook_url:
        raise RuntimeError(
            f"{DISCORD_WEBHOOK_ENV} is missing. "
            "Add it to the project's ignored .env file."
        )

    parsed = urlparse(webhook_url)
    if parsed.scheme != "https" or parsed.hostname not in {
        "discord.com",
        "discordapp.com",
    }:
        raise RuntimeError(
            f"{DISCORD_WEBHOOK_ENV} must be an HTTPS Discord webhook URL."
        )
    if not parsed.path.startswith("/api/webhooks/"):
        raise RuntimeError(
            f"{DISCORD_WEBHOOK_ENV} does not look like a Discord webhook URL."
        )

    payload = build_digest_payload(articles, digest_date)
    try:
        response = httpx.post(webhook_url, json=payload, timeout=15.0)
    except httpx.RequestError:
        raise RuntimeError(
            "Could not reach Discord to deliver the daily digest."
        ) from None

    if not 200 <= response.status_code < 300:
        raise RuntimeError(
            f"Discord rejected the daily digest (HTTP {response.status_code}). "
            "Check the webhook configuration and Discord response limits."
        )

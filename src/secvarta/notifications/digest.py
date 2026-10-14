"""Run ingestion and send a digest for articles published today in India."""

from datetime import UTC, date, datetime
from email.utils import parsedate_to_datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from secvarta.database.connection import get_session
from secvarta.database.models import Article
from secvarta.ingestion.service import IngestionResult, main as ingest_main
from secvarta.notifications.discord import send_digest

INDIA_TZ = ZoneInfo("Asia/Kolkata")


def parse_published_at(value: str) -> datetime | None:
    """Parse RSS/Atom RFC 2822 dates or ISO 8601 timestamps into aware datetimes.

    Legacy database rows can contain raw RSS date strings. Naive timestamps are
    interpreted as UTC because they do not carry enough information to infer a zone.
    """
    value = (value or "").strip()
    if not value:
        return None

    parsed: datetime | None = None
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        pass

    if parsed is None:
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed


def filter_articles_for_date(
    articles: Iterable[Article], target_date: date, limit: int = 10
) -> list[Article]:
    """Return articles published on target_date in Asia/Kolkata, newest first."""
    matching: list[tuple[datetime, Article]] = []
    for article in articles:
        published_at = parse_published_at(article.published_at)
        if published_at is None:
            continue
        local_published_at = published_at.astimezone(INDIA_TZ)
        if local_published_at.date() == target_date:
            matching.append((local_published_at, article))

    matching.sort(key=lambda item: item[0], reverse=True)
    return [article for _, article in matching[:limit]]


def get_todays_articles(target_date: date, limit: int = 10) -> list[Article]:
    """Read stored articles and filter them by their publication date in IST."""
    with get_session() as session:
        statement = (
            select(Article)
            .options(selectinload(Article.cves))
            .where(Article.published_at != "")
        )
        articles = list(session.scalars(statement).all())
        return filter_articles_for_date(articles, target_date, limit=limit)


def run_daily_digest() -> int:
    """Ingest first, then send today's top 10 articles to Discord.

    A run is considered unusable if every configured feed failed to fetch. Partial
    feed failures are tolerated when at least one feed was fetched successfully.
    """
    result: IngestionResult = ingest_main()
    if result.successful_feeds == 0:
        raise RuntimeError(
            "Ingestion did not fetch any feeds successfully; "
            "Discord digest was not sent."
        )

    today = datetime.now(INDIA_TZ).date()
    articles = get_todays_articles(today, limit=10)
    send_digest(articles, today.isoformat())

    print(
        f"Discord daily digest sent for {today.isoformat()} "
        f"({len(articles)} article(s); {result.successful_feeds}/"
        f"{result.total_feeds} feeds fetched successfully)."
    )
    if result.failed_feeds:
        print(f"Warning: {result.failed_feeds} feed(s) failed during ingestion.")
    return len(articles)

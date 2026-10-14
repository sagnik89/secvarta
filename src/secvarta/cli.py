import argparse
import re
import sys

from secvarta.database.connection import get_session
from secvarta.database.repository import (
    get_articles_by_cve,
    get_latest_articles_page,
    search_articles,
)
from secvarta.ingestion.service import main as ingest_main
from secvarta.notifications.digest import run_daily_digest

CVE_PATTERN = re.compile(r"^CVE-\d{4}-\d{4,}$", re.IGNORECASE)


def positive_int(value: str) -> int:
    """Parse a positive integer for CLI arguments."""
    try:
        number = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be an integer") from exc

    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")

    return number


def page_size_int(value: str) -> int:
    """Parse a page size between 1 and 100."""
    number = positive_int(value)

    if number > 100:
        raise argparse.ArgumentTypeError("must not exceed 100")

    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="secvarta",
        description="Cybersecurity intelligence, connected.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    subparsers.add_parser(
        "ingest",
        help="Fetch configured feeds and store articles.",
    )

    subparsers.add_parser(
        "daily-digest",
        help="Ingest feeds and send today's top 10 articles to Discord.",
    )

    articles_parser = subparsers.add_parser(
        "articles",
        help="List the latest articles.",
    )
    articles_parser.add_argument(
        "--page",
        type=positive_int,
        default=1,
        help="Page number (default: 1).",
    )
    articles_parser.add_argument(
        "--page-size",
        type=page_size_int,
        default=20,
        help="Articles per page, maximum 100 (default: 20).",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Search article titles and summaries.",
    )
    search_parser.add_argument(
        "query",
        help="Text to search for.",
    )
    search_parser.add_argument(
        "--limit",
        type=page_size_int,
        default=20,
        help="Maximum results (default: 20, maximum: 100).",
    )

    cve_parser = subparsers.add_parser(
        "cve",
        help="Find articles associated with a CVE identifier.",
    )
    cve_parser.add_argument(
        "cve_id",
        help="CVE identifier, e.g. CVE-2026-12345.",
    )
    cve_parser.add_argument(
        "--limit",
        type=page_size_int,
        default=20,
        help="Maximum results (default: 20, maximum: 100).",
    )

    return parser


def display_articles(articles: list) -> None:
    """Print article records in a readable terminal format."""
    if not articles:
        print("No articles found.")
        return

    for index, article in enumerate(articles, start=1):
        print(f"\n{index}. {article.title}")
        print(f"   URL: {article.url}")

        if article.published_at:
            print(f"   Published: {article.published_at}")

        if article.summary:
            summary = " ".join(article.summary.split())
            if len(summary) > 200:
                summary = summary[:197] + "..."
            print(f"   Summary: {summary}")

        if article.cves:
            cve_ids = ", ".join(sorted(cve.cve_id for cve in article.cves))
            print(f"   CVEs: {cve_ids}")


def handle_articles(args: argparse.Namespace) -> None:
    with get_session() as session:
        result = get_latest_articles_page(
            session,
            page=args.page,
            page_size=args.page_size,
        )

        print(
            f"Articles — page {result.page}/{result.total_pages} ({result.total} total)"
        )
        display_articles(result.items)

        if result.has_previous:
            print(f"\nPrevious page: --page {result.page - 1}")

        if result.has_next:
            print(f"Next page: --page {result.page + 1}")


def handle_search(args: argparse.Namespace) -> None:
    with get_session() as session:
        articles = search_articles(
            session,
            query=args.query,
            limit=args.limit,
        )

        print(f"Search results for: {args.query}")
        display_articles(articles)


def handle_cve(args: argparse.Namespace) -> None:
    cve_id = args.cve_id.strip().upper()

    if not CVE_PATTERN.fullmatch(cve_id):
        raise ValueError("Invalid CVE format. Expected something like CVE-2026-12345.")

    with get_session() as session:
        articles = get_articles_by_cve(
            session,
            cve_id=cve_id,
            limit=args.limit,
        )

        print(f"Articles associated with {cve_id}")
        display_articles(articles)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command == "ingest":
            ingest_main()

        elif args.command == "daily-digest":
            run_daily_digest()

        elif args.command == "articles":
            handle_articles(args)

        elif args.command == "search":
            handle_search(args)

        elif args.command == "cve":
            handle_cve(args)

        return 0

    except (ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

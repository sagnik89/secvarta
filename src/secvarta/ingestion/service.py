from dataclasses import dataclass

import httpx

from secvarta.database.connection import get_session
from secvarta.database.repository import save_article
from secvarta.ingestion.cve_extractor import extract_cves
from secvarta.ingestion.fetcher import get_url
from secvarta.ingestion.normalizer import normalize_entry
from secvarta.ingestion.parser import parse_xml

from secvarta.ingestion.urls import urls


@dataclass(frozen=True)
class IngestionResult:
    """Summary of a feed ingestion run."""

    total_feeds: int
    successful_feeds: int
    failed_feeds: int
    articles_processed: int
    cve_references_found: int


def main() -> IngestionResult:
    articles = []
    successful_feeds = 0
    failed_feeds = 0

    for url in urls:
        try:
            xml_text = get_url(url)
        except httpx.HTTPError as exc:
            failed_feeds += 1
            # Keep error logs concise and avoid printing arbitrary exception details.
            print(f"Failed to fetch feed {url} ({type(exc).__name__}).")
            continue

        successful_feeds += 1
        d = parse_xml(xml_text)

        for entry in d.entries:
            article = normalize_entry(entry)

            article["cves"] = extract_cves(
                article["title"],
                article["summary"],
            )
            article["source_feed"] = url
            articles.append(article)

        print(f"Entries from {url}: {len(d.entries)}")

    # Save collected articles in a single transaction.
    with get_session() as session, session.begin():
        for article_data in articles:
            save_article(session, article_data)

    print("Database save completed.")

    total_cves = sum(len(article["cves"]) for article in articles)
    print(f"Total articles processed: {len(articles)}")
    print(f"Total CVE references found: {total_cves}")

    return IngestionResult(
        total_feeds=len(urls),
        successful_feeds=successful_feeds,
        failed_feeds=failed_feeds,
        articles_processed=len(articles),
        cve_references_found=total_cves,
    )


if __name__ == "__main__":
    main()

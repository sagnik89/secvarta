import httpx

from secvarta.database.connection import get_session
from secvarta.database.repository import save_article
from secvarta.ingestion.cve_extractor import extract_cves
from secvarta.ingestion.fetcher import get_url
from secvarta.ingestion.normalizer import normalize_entry
from secvarta.ingestion.parser import parse_xml

from secvarta.ingestion.urls import urls


def main():

    articles = []

    for url in urls:
        try:
            xml_text = get_url(url)
        except httpx.HTTPError as exc:
            print(f"Failed to fetch {url}: {exc}")
            continue

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


if __name__ == "__main__":
    main()

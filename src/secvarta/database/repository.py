from sqlalchemy import func, select
from sqlalchemy.orm import Session

from secvarta.database.models import CVE, Article
from secvarta.database.schemas import PaginatedResult


def save_article(session: Session, article_data: dict) -> Article:
    """
    Save an article and its CVE relationships.

    Existing article URLs are reused rather than inserted again.
    Existing CVE records are reused across articles.
    """
    url = article_data["url"]

    article = session.scalar(select(Article).where(Article.url == url))

    if article is None:
        article = Article(
            title=article_data["title"],
            url=url,
            summary=article_data.get("summary") or "",
            published_at=article_data.get("published_at") or "",
        )
        session.add(article)
        session.flush()

    for identifier in article_data.get("cves", []):
        identifier = identifier.upper()

        cve = session.scalar(select(CVE).where(CVE.cve_id == identifier))

        if cve is None:
            cve = CVE(cve_id=identifier)
            session.add(cve)
            session.flush()

        if cve not in article.cves:
            article.cves.append(cve)

    return article


def get_latest_articles_page(
    session: Session,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResult[Article]:
    """Return a page of articles and pagination metadata."""
    if page < 1:
        raise ValueError("page must be at least 1")

    if not 1 <= page_size <= 100:
        raise ValueError("page_size must be between 1 and 100")

    total = session.scalar(select(func.count()).select_from(Article)) or 0

    offset = (page - 1) * page_size

    statement = (
        select(Article)
        .order_by(Article.ingested_at.desc(), Article.id.desc())
        .limit(page_size)
        .offset(offset)
    )

    items = list(session.scalars(statement).all())

    return PaginatedResult(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


def search_articles(
    session: Session,
    query: str,
    limit: int = 20,
) -> list[Article]:
    """Search article titles and summaries using a text query."""
    query = query.strip()

    if not query:
        raise ValueError("query must not be empty")

    if limit < 1:
        raise ValueError("limit must be at least 1")

    statement = (
        select(Article)
        .where(
            Article.title.contains(query, autoescape=True)
            | Article.summary.contains(query, autoescape=True)
        )
        .order_by(Article.ingested_at.desc(), Article.id.desc())
        .limit(limit)
    )

    return list(session.scalars(statement).all())


def get_articles_by_cve(
    session: Session,
    cve_id: str,
    limit: int = 20,
) -> list[Article]:
    """Return articles associated with a CVE identifier."""
    cve_id = cve_id.strip().upper()

    if not cve_id:
        raise ValueError("cve_id must not be empty")

    if limit < 1:
        raise ValueError("limit must be at least 1")

    statement = (
        select(Article)
        .join(Article.cves)
        .where(CVE.cve_id == cve_id)
        .order_by(Article.ingested_at.desc(), Article.id.desc())
        .limit(limit)
    )

    return list(session.scalars(statement).all())

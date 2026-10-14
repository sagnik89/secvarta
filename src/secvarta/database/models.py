from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all SecVarta database models."""


article_cves = Table(
    "article_cves",
    Base.metadata,
    Column(
        "article_id",
        ForeignKey("articles.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "cve_id",
        ForeignKey("cves.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Article(Base):
    __tablename__ = "articles"
    __table_args__ = (UniqueConstraint("url", name="uq_articles_url"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="", nullable=False)
    published_at: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(UTC),
        nullable=False,
    )

    cves: Mapped[list[CVE]] = relationship(
        secondary=article_cves,
        back_populates="articles",
        passive_deletes=True,
    )


class CVE(Base):
    __tablename__ = "cves"

    id: Mapped[int] = mapped_column(primary_key=True)
    cve_id: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
    )

    articles: Mapped[list[Article]] = relationship(
        secondary=article_cves,
        back_populates="cves",
        passive_deletes=True,
    )

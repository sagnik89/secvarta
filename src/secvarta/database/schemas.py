from dataclasses import dataclass
from typing import TypeVar

T = TypeVar("T")


@dataclass
class PaginatedResult[T]:
    """Metadata and records for a paginated query."""

    items: list[T]
    page: int
    page_size: int
    total: int

    @property
    def total_pages(self) -> int:
        if self.total == 0:
            return 0

        return (self.total + self.page_size - 1) // self.page_size

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def has_previous(self) -> bool:
        return self.page > 1

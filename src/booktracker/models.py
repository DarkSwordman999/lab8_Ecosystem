"""Модель предметной области (слой данных, M в MVC)."""

from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Optional

STATUSES = ("planned", "reading", "finished")


@dataclass
class Book:
    title: str
    author: str
    isbn: Optional[str] = None
    year: Optional[int] = None
    pages: Optional[int] = None
    status: str = "planned"
    rating: Optional[int] = None
    finished_on: Optional[str] = None
    id: Optional[int] = field(default=None)

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

    def mark_finished(self, today=None):
        self.status = "finished"
        self.finished_on = (today or date.today()).isoformat()

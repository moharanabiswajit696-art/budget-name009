"""
Expense dataclass — represents a single spending record.
"""

import datetime
from dataclasses import dataclass


@dataclass
class Expense:
    """A single expense entry."""

    amount: float
    category: str
    description: str
    date: datetime.date

    def to_dict(self) -> dict:
        """Return a plain dict suitable for writing as a CSV row."""
        return {
            "amount": self.amount,
            "category": self.category,
            "description": self.description,
            "date": self.date.isoformat(),  # YYYY-MM-DD string
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        """Reconstruct an Expense from a CSV row dict."""
        return cls(
            amount=float(data["amount"]),
            category=data["category"],
            description=data["description"],
            date=datetime.date.fromisoformat(data["date"]),
        )

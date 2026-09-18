"""
Core business logic for the Personal Budget Planner.

BudgetPlanner owns all state (budget + expenses) and handles persistence
to budget.json (budget) and expenses.csv (expenses).
"""

import csv
import json
import datetime
from pathlib import Path

from expense import Expense
from validator import (
    validate_budget,
    validate_amount,
    validate_category,
    validate_date,
    validate_description,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORIES: list[str] = ["Food", "Travel", "Shopping", "Education", "Healthcare", "Entertainment"]

_BASE_DIR = Path(__file__).parent
CSV_FILE: Path = _BASE_DIR / "expenses.csv"
BUDGET_FILE: Path = _BASE_DIR / "budget.json"

_CSV_FIELDNAMES = ["amount", "category", "description", "date"]


# ---------------------------------------------------------------------------
# BudgetPlanner class
# ---------------------------------------------------------------------------

class BudgetPlanner:
    """Manages monthly budget and expense records with CSV/JSON persistence."""

    def __init__(self) -> None:
        self.monthly_budget: float = self._load_budget()
        self.expenses: list[Expense] = self._load_expenses()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_budget(self, amount: float) -> None:
        """Set (or update) the monthly budget and persist it to budget.json."""
        validate_budget(amount)
        self.monthly_budget = float(amount)
        self._save_budget()

    def add_expense(
        self,
        amount: float,
        category: str,
        description: str,
        date: datetime.date,
    ) -> None:
        """Validate and add a new expense, appending it to expenses.csv."""
        validate_amount(amount, self.monthly_budget)
        validate_category(category, CATEGORIES)
        validate_description(description)
        validate_date(date)

        expense = Expense(
            amount=float(amount),
            category=category,
            description=description,
            date=date,
        )
        self.expenses.append(expense)
        self._append_expense_to_csv(expense)

    def delete_expense(self, index: int) -> None:
        """Remove the expense at the given index and rewrite expenses.csv."""
        self.expenses.pop(index)
        self._rewrite_csv()

    def get_total_spent(self) -> float:
        """Return the sum of all expense amounts."""
        return sum(e.amount for e in self.expenses)

    def get_remaining_budget(self) -> float:
        """Return monthly_budget minus total spent (may be negative if overspent)."""
        return self.monthly_budget - self.get_total_spent()

    def get_category_summary(self) -> dict[str, float]:
        """Return {category: total_amount} for each category with at least one expense."""
        summary: dict[str, float] = {}
        for expense in self.expenses:
            summary[expense.category] = summary.get(expense.category, 0.0) + expense.amount
        return summary

    def get_all_expenses(self) -> list[Expense]:
        """Return a shallow copy of the expenses list."""
        return list(self.expenses)

    # ------------------------------------------------------------------
    # Persistence helpers (private)
    # ------------------------------------------------------------------

    def _load_budget(self) -> float:
        """Load budget from budget.json; return 0.0 if file is missing or corrupt."""
        if not BUDGET_FILE.exists():
            return 0.0
        try:
            data = json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
            return float(data.get("monthly_budget", 0.0))
        except (json.JSONDecodeError, ValueError, KeyError):
            return 0.0

    def _save_budget(self) -> None:
        """Persist the current monthly_budget to budget.json."""
        BUDGET_FILE.write_text(
            json.dumps({"monthly_budget": self.monthly_budget}, indent=2),
            encoding="utf-8",
        )

    def _load_expenses(self) -> list[Expense]:
        """Load expenses from expenses.csv; return empty list if file is missing or corrupt."""
        if not CSV_FILE.exists():
            return []
        expenses: list[Expense] = []
        try:
            with CSV_FILE.open(newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        expenses.append(Expense.from_dict(row))
                    except (KeyError, ValueError):
                        # Skip malformed rows silently
                        continue
        except OSError:
            return []
        return expenses

    def _append_expense_to_csv(self, expense: Expense) -> None:
        """Append a single expense row to expenses.csv, creating the file if needed."""
        file_exists = CSV_FILE.exists()
        with CSV_FILE.open("a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            if not file_exists:
                writer.writeheader()
            writer.writerow(expense.to_dict())

    def _rewrite_csv(self) -> None:
        """Rewrite expenses.csv from the current in-memory expenses list."""
        with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_CSV_FIELDNAMES)
            writer.writeheader()
            for expense in self.expenses:
                writer.writerow(expense.to_dict())

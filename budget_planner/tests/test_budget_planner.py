"""
pytest tests for Personal Budget Planner.

Covers:
  - BudgetPlanner calculations
  - Validation rules (all five validators)
  - Overspending behaviour
  - Category summary
  - CSV round-trip persistence
  - Expense dataclass to_dict / from_dict
"""

import csv
import datetime
import json
import sys
from pathlib import Path

import pytest

# Make budget_planner/ importable
sys.path.insert(0, str(Path(__file__).parent.parent / "budget_planner"))

from exceptions import (
    BudgetPlannerError,
    InvalidBudgetError,
    InvalidCategoryError,
    InvalidDateError,
    InvalidExpenseError,
)
from expense import Expense
from budget_planner import BudgetPlanner, CATEGORIES, CSV_FILE, BUDGET_FILE
from validator import (
    validate_budget,
    validate_amount,
    validate_category,
    validate_date,
    validate_description,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def clean_data_files(tmp_path, monkeypatch):
    """Redirect CSV_FILE and BUDGET_FILE to a tmp directory for every test."""
    import budget_planner as bp_module

    tmp_csv = tmp_path / "expenses.csv"
    tmp_budget = tmp_path / "budget.json"

    monkeypatch.setattr(bp_module, "CSV_FILE", tmp_csv)
    monkeypatch.setattr(bp_module, "BUDGET_FILE", tmp_budget)
    yield


@pytest.fixture
def planner(clean_data_files):
    """Return a fresh BudgetPlanner backed by temp files."""
    return BudgetPlanner()


@pytest.fixture
def funded_planner(planner):
    """Return a planner with a $1000 budget already set."""
    planner.set_budget(1000.0)
    return planner


# ---------------------------------------------------------------------------
# Expense dataclass tests
# ---------------------------------------------------------------------------

class TestExpense:
    def test_to_dict_round_trip(self):
        e = Expense(
            amount=42.5,
            category="Food",
            description="Lunch",
            date=datetime.date(2025, 6, 15),
        )
        d = e.to_dict()
        assert d == {
            "amount": 42.5,
            "category": "Food",
            "description": "Lunch",
            "date": "2025-06-15",
        }

    def test_from_dict_round_trip(self):
        row = {"amount": "99.99", "category": "Travel", "description": "Bus", "date": "2025-01-10"}
        e = Expense.from_dict(row)
        assert e.amount == 99.99
        assert e.category == "Travel"
        assert e.date == datetime.date(2025, 1, 10)


# ---------------------------------------------------------------------------
# Validator tests
# ---------------------------------------------------------------------------

class TestValidators:
    def test_validate_budget_ok(self):
        validate_budget(500)  # should not raise

    def test_validate_budget_zero(self):
        with pytest.raises(InvalidBudgetError):
            validate_budget(0)

    def test_validate_budget_negative(self):
        with pytest.raises(InvalidBudgetError):
            validate_budget(-100)

    def test_validate_budget_string(self):
        with pytest.raises(InvalidBudgetError):
            validate_budget("abc")

    def test_validate_amount_ok(self):
        validate_amount(50, 1000)  # should not raise

    def test_validate_amount_zero(self):
        with pytest.raises(InvalidExpenseError):
            validate_amount(0, 1000)

    def test_validate_amount_exceeds_budget(self):
        with pytest.raises(InvalidExpenseError, match="cannot exceed"):
            validate_amount(1500, 1000)

    def test_validate_category_ok(self):
        validate_category("Food", CATEGORIES)  # should not raise

    def test_validate_category_invalid(self):
        with pytest.raises(InvalidCategoryError):
            validate_category("Gambling", CATEGORIES)

    def test_validate_date_ok(self):
        validate_date(datetime.date.today())  # should not raise

    def test_validate_date_future(self):
        future = datetime.date.today() + datetime.timedelta(days=1)
        with pytest.raises(InvalidDateError):
            validate_date(future)

    def test_validate_date_not_a_date(self):
        with pytest.raises(InvalidDateError):
            validate_date("2025-01-01")

    def test_validate_description_ok(self):
        validate_description("Short note")  # should not raise

    def test_validate_description_empty_ok(self):
        validate_description("")  # empty is allowed

    def test_validate_description_too_long(self):
        with pytest.raises(InvalidExpenseError, match="too long"):
            validate_description("x" * 101)


# ---------------------------------------------------------------------------
# BudgetPlanner calculation tests
# ---------------------------------------------------------------------------

class TestBudgetPlannerCalculations:
    def test_set_budget(self, planner):
        planner.set_budget(2000)
        assert planner.monthly_budget == 2000.0

    def test_set_budget_invalid(self, planner):
        with pytest.raises(InvalidBudgetError):
            planner.set_budget(-50)

    def test_add_expense_and_total(self, funded_planner):
        funded_planner.add_expense(200, "Food", "Groceries", datetime.date.today())
        funded_planner.add_expense(150, "Travel", "Bus pass", datetime.date.today())
        assert funded_planner.get_total_spent() == pytest.approx(350.0)

    def test_remaining_budget(self, funded_planner):
        funded_planner.add_expense(400, "Shopping", "Clothes", datetime.date.today())
        assert funded_planner.get_remaining_budget() == pytest.approx(600.0)

    def test_overspend_allowed(self, funded_planner):
        """Overspending in total is allowed — remaining budget goes negative."""
        funded_planner.add_expense(999, "Food", "Big dinner", datetime.date.today())
        # Adding a second expense that together exceed budget is fine (each is <= budget)
        funded_planner.add_expense(500, "Travel", "Flight", datetime.date.today())
        remaining = funded_planner.get_remaining_budget()
        assert remaining == pytest.approx(1000 - 999 - 500)
        assert remaining < 0

    def test_single_expense_cannot_exceed_budget(self, funded_planner):
        """A single expense that exceeds the budget is blocked."""
        with pytest.raises(InvalidExpenseError, match="cannot exceed"):
            funded_planner.add_expense(1500, "Food", "Huge bill", datetime.date.today())

    def test_category_summary(self, funded_planner):
        funded_planner.add_expense(100, "Food", "Lunch", datetime.date.today())
        funded_planner.add_expense(200, "Food", "Dinner", datetime.date.today())
        funded_planner.add_expense(300, "Travel", "Flight", datetime.date.today())
        summary = funded_planner.get_category_summary()
        assert summary["Food"] == pytest.approx(300.0)
        assert summary["Travel"] == pytest.approx(300.0)
        assert "Shopping" not in summary

    def test_delete_expense(self, funded_planner):
        funded_planner.add_expense(50, "Food", "Coffee", datetime.date.today())
        funded_planner.add_expense(100, "Shopping", "Book", datetime.date.today())
        funded_planner.delete_expense(0)
        expenses = funded_planner.get_all_expenses()
        assert len(expenses) == 1
        assert expenses[0].category == "Shopping"

    def test_get_all_expenses_returns_copy(self, funded_planner):
        funded_planner.add_expense(10, "Food", "Snack", datetime.date.today())
        copy = funded_planner.get_all_expenses()
        copy.clear()
        assert len(funded_planner.get_all_expenses()) == 1


# ---------------------------------------------------------------------------
# CSV persistence tests
# ---------------------------------------------------------------------------

class TestCSVPersistence:
    def test_expenses_persist_across_instances(self, clean_data_files):
        import budget_planner as bp_module

        p1 = BudgetPlanner()
        p1.set_budget(500)
        p1.add_expense(75, "Food", "Lunch", datetime.date.today())
        p1.add_expense(120, "Travel", "Taxi", datetime.date.today())

        # New instance reads from same tmp files
        p2 = BudgetPlanner()
        assert p2.monthly_budget == pytest.approx(500.0)
        assert len(p2.get_all_expenses()) == 2
        assert p2.get_total_spent() == pytest.approx(195.0)

    def test_budget_persists_across_instances(self, clean_data_files):
        p1 = BudgetPlanner()
        p1.set_budget(1234.56)

        p2 = BudgetPlanner()
        assert p2.monthly_budget == pytest.approx(1234.56)

    def test_delete_persists(self, clean_data_files):
        p1 = BudgetPlanner()
        p1.set_budget(1000)
        p1.add_expense(50, "Food", "A", datetime.date.today())
        p1.add_expense(60, "Travel", "B", datetime.date.today())
        p1.delete_expense(0)

        p2 = BudgetPlanner()
        expenses = p2.get_all_expenses()
        assert len(expenses) == 1
        assert expenses[0].category == "Travel"

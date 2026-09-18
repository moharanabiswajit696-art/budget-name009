"""
Input validation functions for the Personal Budget Planner.

Each function raises the appropriate BudgetPlannerError subclass
with a clear, UI-ready message when a value is invalid.
"""

import datetime
import math

from exceptions import (
    InvalidBudgetError,
    InvalidCategoryError,
    InvalidDateError,
    InvalidExpenseError,
)


def validate_budget(value) -> None:
    """Raise InvalidBudgetError if value is not a finite positive number."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise InvalidBudgetError("Budget must be a number.")
    if math.isnan(v) or math.isinf(v):
        raise InvalidBudgetError("Budget must be a finite number.")
    if v <= 0:
        raise InvalidBudgetError("Budget must be greater than $0.00.")


def validate_amount(value, monthly_budget: float) -> None:
    """Raise InvalidExpenseError if value is not a finite positive number or exceeds the budget."""
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise InvalidExpenseError("Expense amount must be a number.")
    if math.isnan(v) or math.isinf(v):
        raise InvalidExpenseError("Expense amount must be a finite number.")
    if v <= 0:
        raise InvalidExpenseError("Expense amount must be greater than $0.00.")
    if v > monthly_budget:
        raise InvalidExpenseError(
            f"A single expense (${v:,.2f}) cannot exceed the monthly budget (${monthly_budget:,.2f})."
        )


def validate_category(value, allowed_categories: list) -> None:
    """Raise InvalidCategoryError if value is not in the allowed list."""
    if value not in allowed_categories:
        raise InvalidCategoryError(
            f"'{value}' is not a valid category. Choose from: {', '.join(allowed_categories)}."
        )


def validate_date(value) -> None:
    """Raise InvalidDateError if value is not a date or is in the future."""
    if not isinstance(value, datetime.date):
        raise InvalidDateError("Expense date must be a valid calendar date.")
    if value > datetime.date.today():
        raise InvalidDateError("Expense date cannot be in the future.")


def validate_description(value: str) -> None:
    """Raise InvalidExpenseError if description exceeds 100 characters.

    An empty description is allowed — description is optional.
    """
    if len(value) > 100:
        raise InvalidExpenseError(
            f"Description is too long ({len(value)} chars). Maximum is 100 characters."
        )

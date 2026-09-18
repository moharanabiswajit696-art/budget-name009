"""
Custom exception hierarchy for the Personal Budget Planner.

All exceptions carry a human-readable message suitable for display in the UI.
"""


class BudgetPlannerError(Exception):
    """Base exception for all Budget Planner errors."""


class InvalidBudgetError(BudgetPlannerError):
    """Raised when the monthly budget value is invalid (zero, negative, or non-numeric)."""


class InvalidExpenseError(BudgetPlannerError):
    """Raised when an expense value is invalid (bad amount, description too long, etc.)."""


class InvalidCategoryError(BudgetPlannerError):
    """Raised when the selected category is not in the allowed list."""


class InvalidDateError(BudgetPlannerError):
    """Raised when the expense date is invalid or in the future."""

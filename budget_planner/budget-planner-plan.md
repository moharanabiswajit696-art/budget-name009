# Personal Budget Planner — Implementation Plan

## Top-Level Overview

**Goal:** Build a small, beginner-friendly Personal Budget Planner web app using Python and Streamlit.

**Scope:**
- Single-user, single-month view
- Data persists across restarts: expenses to `expenses.csv`, monthly budget to `budget.json`
- Currency fixed to USD ($)
- Features: set budget, add expense, view/delete expenses, summary cards, category bar chart
- No authentication, no multi-user support, no edit-in-place

**Approach:**
Build the project in five focused layers, each independently testable:
1. Custom exceptions
2. Expense data structure
3. Core business logic (BudgetPlanner class)
4. Input validation
5. Streamlit UI (app entry point)

**Non-goals:**
- No database (CSV + JSON only)
- No user authentication
- No currency selection
- No expense editing (delete only)
- No multi-month filtering

---

## File Structure

```
budget_planner/
├── app.py              — Streamlit UI, entry point
├── expense.py          — Expense dataclass
├── budget_planner.py   — Core logic class
├── validator.py        — All validation functions
├── exceptions.py       — Custom exception hierarchy
├── expenses.csv        — Auto-created on first run
├── budget.json         — Auto-created on first budget save
└── requirements.txt    — streamlit, pandas
```

---

## Sub-Tasks

---

### Sub-Task 1 — Custom Exception Classes

**Status:** [x] done

**Intent:**
Define a small, clean exception hierarchy so that all layers (validation, business logic, UI) can raise and catch typed errors without string-matching. This is the foundation every other module depends on.

**Expected Outcomes:**
- `exceptions.py` exists with a base `BudgetPlannerError` and four specific subclasses
- Every exception carries a human-readable message suitable for display in the UI

**Todo List:**
1. Create `exceptions.py`
2. Define base class `BudgetPlannerError(Exception)`
3. Define `InvalidBudgetError(BudgetPlannerError)` — raised when budget value is invalid
4. Define `InvalidExpenseError(BudgetPlannerError)` — raised when expense amount is invalid
5. Define `InvalidCategoryError(BudgetPlannerError)` — raised when category is not in the allowed list
6. Define `InvalidDateError(BudgetPlannerError)` — raised when the date is invalid or in the future

**Relevant Context:**
- No dependencies on any other project file
- All other modules import from this file

---

### Sub-Task 2 — Expense Dataclass

**Status:** [x] done

**Intent:**
Define the `Expense` data structure that represents a single spending record. Using a Python `dataclass` keeps it clean and beginner-readable.

**Expected Outcomes:**
- `expense.py` exists with an `Expense` dataclass
- The dataclass has exactly four fields matching the data model
- The dataclass can convert itself to and from a CSV row (dict) for persistence

**Todo List:**
1. Create `expense.py`
2. Define `Expense` as a `@dataclass` with fields:
   - `amount: float`
   - `category: str`
   - `description: str`
   - `date: datetime.date`
3. Add a `to_dict()` method that returns a plain dict (for CSV writing)
4. Add a `from_dict(data: dict)` classmethod that reconstructs an `Expense` from a CSV row dict

**Relevant Context:**
- Imported by `budget_planner.py` and `app.py`
- `to_dict` / `from_dict` must handle the `date` field as an ISO string (`YYYY-MM-DD`) for CSV compatibility

---

### Sub-Task 3 — Core Business Logic

**Status:** [x] done

**Intent:**
Implement the `BudgetPlanner` class that owns all state (budget + expenses list) and all business logic (calculations, persistence). The UI layer calls only this class — it never manipulates data directly.

**Expected Outcomes:**
- `budget_planner.py` exists with a fully working `BudgetPlanner` class
- Budget loads from `budget.json` on init; saves on `set_budget()`
- Expenses load from `expenses.csv` on init; append on `add_expense()`; rewrite on `delete_expense()`
- All six public methods work correctly and raise the appropriate custom exceptions on bad input

**Todo List:**
1. Create `budget_planner.py`
2. Define constants at the top: `CATEGORIES = ["Food", "Travel", "Shopping", "Education"]`, `CSV_FILE = "expenses.csv"`, `BUDGET_FILE = "budget.json"`
3. Implement `BudgetPlanner.__init__()`: load budget from `budget.json` (default `0.0` if missing), load expenses from `expenses.csv` (empty list if missing)
4. Implement `set_budget(amount: float)`: validate amount > 0, persist to `budget.json`, update `self.monthly_budget`
5. Implement `add_expense(amount, category, description, date)`: validate inputs, create `Expense`, append to `self.expenses`, append a new row to `expenses.csv`
6. Implement `delete_expense(index: int)`: remove expense at given index from `self.expenses`, rewrite the full `expenses.csv`
7. Implement `get_total_spent() -> float`: sum of all expense amounts
8. Implement `get_remaining_budget() -> float`: `monthly_budget - get_total_spent()`
9. Implement `get_category_summary() -> dict`: return `{category: total_amount}` for each category that has at least one expense
10. Implement `get_all_expenses() -> list`: return a copy of `self.expenses`

**Relevant Context:**
- Imports `Expense` from `expense.py`
- Imports all custom exceptions from `exceptions.py`
- CSV columns must match `Expense.to_dict()` keys exactly: `amount`, `category`, `description`, `date`
- Uses Python's built-in `csv` and `json` modules — no extra dependencies

---

### Sub-Task 4 — Input Validation

**Status:** [x] done

**Intent:**
Centralize all input validation rules in one `validator.py` module. Each function raises the appropriate custom exception if the value is invalid. Keeping validation separate from the UI and business logic makes both easier to read and test.

**Expected Outcomes:**
- `validator.py` exists with five focused validation functions
- Each function raises the correct subclass of `BudgetPlannerError` with a clear message
- `budget_planner.py` calls these functions before any state changes

**Todo List:**
1. Create `validator.py`
2. Implement `validate_budget(value)`:
   - Raises `InvalidBudgetError` if value is not a positive number
3. Implement `validate_amount(value, monthly_budget)`:
   - Raises `InvalidExpenseError` if value is not a positive number
   - Raises `InvalidExpenseError` if value exceeds `monthly_budget`
4. Implement `validate_category(value, allowed_categories)`:
   - Raises `InvalidCategoryError` if value is not in the allowed list
5. Implement `validate_date(value)`:
   - Raises `InvalidDateError` if value is not a `datetime.date` instance
   - Raises `InvalidDateError` if value is in the future
6. Implement `validate_description(value)`:
   - Raises `InvalidExpenseError` if description exceeds 100 characters (no error if empty — description is optional)

**Relevant Context:**
- Imports only from `exceptions.py`
- Called inside `BudgetPlanner.set_budget()` and `BudgetPlanner.add_expense()`

---

### Sub-Task 5 — Streamlit UI

**Status:** [x] done

**Intent:**
Build the Streamlit front-end in `app.py`. The UI owns zero business logic — it only calls `BudgetPlanner` methods and renders the results. All state lives in `st.session_state` (backed by the persisted files).

**Expected Outcomes:**
- Running `streamlit run app.py` shows a working budget planner
- Page has four clearly separated sections: Set Budget, Add Expense, Expense Table, Summary
- All validation errors display as friendly `st.error()` messages — no unhandled exceptions
- Delete button on each table row removes the expense and refreshes the view
- Summary section shows: total spent, remaining budget (red if negative), category bar chart
- If no budget is set, the Add Expense form is disabled with a clear prompt

**Todo List:**
1. Create `app.py` and `requirements.txt` (`streamlit`, `pandas`)
2. Initialize `BudgetPlanner` once using `st.session_state` to avoid reloading on every interaction
3. Build **Set Budget** section:
   - Number input for budget amount
   - "Save Budget" button that calls `planner.set_budget()`
   - Show current budget value if already set
4. Build **Add Expense** section (disabled if `monthly_budget == 0`):
   - Number input for amount
   - Selectbox for category (choices from `CATEGORIES`)
   - Text input for description (max 100 chars shown as hint)
   - Date input defaulting to today
   - "Add Expense" button that calls `planner.add_expense()`
   - Wrap call in try/except `BudgetPlannerError` and show `st.error()` on failure
5. Build **Expense Table** section:
   - Show `st.info("No expenses yet.")` if list is empty
   - Otherwise render expenses as a `st.dataframe` with a separate "Delete" column
   - Each row has a delete button that calls `planner.delete_expense(index)` and triggers rerun
6. Build **Summary** section (only shown if budget is set):
   - Metric cards: Monthly Budget, Total Spent, Remaining Budget
   - Remaining budget metric displayed in red text if negative using `st.markdown`
   - Bar chart of category spending using `st.bar_chart` with pandas Series from `get_category_summary()`
   - Show `st.warning("No expenses to chart yet.")` if no expenses exist

**Relevant Context:**
- Imports `BudgetPlanner` from `budget_planner.py`
- Imports `BudgetPlannerError` from `exceptions.py`
- Imports `CATEGORIES` constant from `budget_planner.py`
- Uses only Streamlit built-ins and pandas — no custom CSS required

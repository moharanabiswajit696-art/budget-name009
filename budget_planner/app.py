"""
Streamlit UI — Personal Budget Planner entry point.

Sections:
  1. Set Budget
  2. Add Expense
  3. Expense Table (with Delete buttons)
  4. Summary (metrics + category bar chart)
"""

import sys
import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

# Allow imports from the budget_planner package directory
sys.path.insert(0, str(Path(__file__).parent))

from budget_planner import BudgetPlanner, CATEGORIES  # noqa: E402
from exceptions import BudgetPlannerError  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Personal Budget Planner",
    page_icon="💰",
    layout="centered",
)

st.title("💰 Personal Budget Planner")

# ---------------------------------------------------------------------------
# Session state — initialise BudgetPlanner once per session
# ---------------------------------------------------------------------------

if "planner" not in st.session_state:
    st.session_state.planner = BudgetPlanner()

planner: BudgetPlanner = st.session_state.planner

# ---------------------------------------------------------------------------
# Section 1 — Set Budget
# ---------------------------------------------------------------------------

st.header("1. Monthly Budget")

with st.form("budget_form"):
    budget_input = st.number_input(
        "Set your monthly budget ($)",
        min_value=0.0,
        value=max(planner.monthly_budget, 0.0),
        step=100.0,
        format="%.2f",
    )
    save_budget = st.form_submit_button("Save Budget")

if save_budget:
    try:
        planner.set_budget(budget_input)
        st.success(f"Monthly budget set to ${planner.monthly_budget:,.2f}")
    except BudgetPlannerError as e:
        st.error(str(e))

if planner.monthly_budget > 0:
    st.info(f"Current budget: **${planner.monthly_budget:,.2f}**")

# ---------------------------------------------------------------------------
# Section 2 — Add Expense
# ---------------------------------------------------------------------------

st.header("2. Add Expense")

if planner.monthly_budget == 0:
    st.warning("Please set a monthly budget above before adding expenses.")
else:
    with st.form("expense_form"):
        col1, col2 = st.columns(2)
        with col1:
            amount_input = st.number_input(
                "Amount ($)",
                min_value=0.01,
                step=1.0,
                format="%.2f",
            )
        with col2:
            category_input = st.selectbox("Category", CATEGORIES)

        description_input = st.text_input(
            "Description (optional, max 100 characters)",
            max_chars=100,
        )
        date_input = st.date_input(
            "Expense Date",
            value=datetime.date.today(),
            max_value=datetime.date.today(),
        )
        add_expense = st.form_submit_button("Add Expense")

    if add_expense:
        try:
            planner.add_expense(
                amount=amount_input,
                category=category_input,
                description=description_input,
                date=date_input,
            )
            st.success(
                f"Added ${amount_input:,.2f} under {category_input} on {date_input}."
            )
            st.rerun()
        except BudgetPlannerError as e:
            st.error(str(e))

# ---------------------------------------------------------------------------
# Section 3 — Expense Table
# ---------------------------------------------------------------------------

st.header("3. All Expenses")

expenses = planner.get_all_expenses()

if not expenses:
    st.info("No expenses yet. Add one above!")
else:
    for i, expense in enumerate(expenses):
        col_amt, col_cat, col_desc, col_date, col_del = st.columns(
            [1.5, 1.5, 2.5, 1.5, 1]
        )
        col_amt.write(f"**${expense.amount:,.2f}**")
        col_cat.write(expense.category)
        col_desc.write(expense.description or "—")
        col_date.write(str(expense.date))
        if col_del.button("🗑️", key=f"del_{i}", help="Delete this expense"):
            planner.delete_expense(i)
            st.rerun()

    # Show as a clean dataframe below the interactive rows
    df = pd.DataFrame([e.to_dict() for e in expenses])
    df.columns = ["Amount ($)", "Category", "Description", "Date"]
    df["Amount ($)"] = df["Amount ($)"].apply(lambda x: f"${float(x):,.2f}")
    st.dataframe(df, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Section 4 — Summary
# ---------------------------------------------------------------------------

if planner.monthly_budget > 0:
    st.header("4. Summary")

    total_spent = planner.get_total_spent()
    remaining = planner.get_remaining_budget()

    col_b, col_s, col_r = st.columns(3)
    col_b.metric("Monthly Budget", f"${planner.monthly_budget:,.2f}")
    col_s.metric("Total Spent", f"${total_spent:,.2f}")

    # Remaining — red markdown if overspent, normal metric if within budget
    if remaining < 0:
        col_r.metric("Remaining Budget", f"${remaining:,.2f}", delta=f"${remaining:,.2f}")
        st.markdown(
            f"<p style='color:red;font-weight:bold;'>⚠️ You are overspent by "
            f"${abs(remaining):,.2f}!</p>",
            unsafe_allow_html=True,
        )
    else:
        col_r.metric("Remaining Budget", f"${remaining:,.2f}")

    # Category bar chart
    st.subheader("Spending by Category")
    summary = planner.get_category_summary()
    if not summary:
        st.warning("No expenses to chart yet.")
    else:
        chart_data = pd.Series(summary, name="Amount ($)")
        st.bar_chart(chart_data)

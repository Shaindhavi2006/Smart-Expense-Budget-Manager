import csv
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import pandas as pd
import streamlit as st

APP_TITLE = "Smart Expense & Budget Manager"
DATA_FILE = Path("transactions.csv")
BUDGET_FILE = Path("budget.json")
CATEGORIES = [
    "Salary", "Food", "Travel", "Shopping", "Education",
    "Bills", "Entertainment", "Health", "Other"
]

st.set_page_config(page_title=APP_TITLE, page_icon="💰", layout="wide")

st.markdown("""
<style>
    .stApp { background: #F2F5FB; }
    [data-testid="stMetric"] {
        background: white; padding: 18px; border-radius: 12px;
        border: 1px solid #D8E1F0;
    }
    h1, h2, h3 { color: #172B4D; }
</style>
""", unsafe_allow_html=True)


def load_transactions():
    if not DATA_FILE.exists():
        return []
    result = []
    try:
        with DATA_FILE.open("r", newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                try:
                    amount = float(row.get("Amount", row.get("amount", 0)) or 0)
                    if amount < 0:
                        continue
                    result.append({
                        "ID": int(row.get("ID", row.get("id", 0)) or 0),
                        "Type": (row.get("Type", row.get("type", "Expense")) or "Expense").title(),
                        "Amount": amount,
                        "Category": row.get("Category", row.get("category", "Other")) or "Other",
                        "Date": row.get("Date", row.get("date", datetime.now().strftime("%d-%m-%Y"))) or datetime.now().strftime("%d-%m-%Y"),
                        "Description": row.get("Description", row.get("description", "")) or "",
                    })
                except (ValueError, TypeError):
                    continue
    except (OSError, csv.Error):
        st.warning("Could not read transactions.csv. A new transaction list will be used.")
    used = set()
    next_id = 1
    for item in result:
        if item["ID"] <= 0 or item["ID"] in used:
            while next_id in used:
                next_id += 1
            item["ID"] = next_id
        used.add(item["ID"])
        next_id = max(next_id, item["ID"] + 1)
    return result


def save_transactions(items):
    fields = ["ID", "Type", "Amount", "Category", "Date", "Description"]
    with DATA_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(items)


def load_budget():
    if BUDGET_FILE.exists():
        try:
            return max(0.0, float(json.loads(BUDGET_FILE.read_text(encoding="utf-8")).get("monthly_budget", 5000)))
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            pass
    return 5000.0


def save_budget(value):
    BUDGET_FILE.write_text(json.dumps({"monthly_budget": value}, indent=4), encoding="utf-8")


def parse_date(value):
    for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except (ValueError, AttributeError):
            continue
    return None


def money(value):
    return f"₹{value:,.2f}"


if "transactions" not in st.session_state:
    st.session_state.transactions = load_transactions()
if "monthly_budget" not in st.session_state:
    st.session_state.monthly_budget = load_budget()

transactions = st.session_state.transactions
budget = st.session_state.monthly_budget

st.title("💰 Smart Expense & Budget Manager")
st.caption("Track your money. Manage your future.")

today = datetime.now().date()
income_total = sum(x["Amount"] for x in transactions if x["Type"] == "Income")
expense_total = sum(x["Amount"] for x in transactions if x["Type"] == "Expense")
balance = income_total - expense_total
current_month_expenses = sum(
    x["Amount"] for x in transactions
    if x["Type"] == "Expense" and parse_date(x["Date"])
    and parse_date(x["Date"]).year == today.year
    and parse_date(x["Date"]).month == today.month
)

m1, m2, m3 = st.columns(3)
m1.metric("Total Income", money(income_total))
m2.metric("Total Expenses", money(expense_total))
m3.metric("Current Balance", money(balance))

with st.container(border=True):
    left, right = st.columns([3, 1])
    with left:
        st.subheader("Monthly Budget")
        st.write(f"Budget: **{money(budget)}**")
        progress = min(current_month_expenses / budget, 1.0) if budget > 0 else (1.0 if current_month_expenses else 0.0)
        st.progress(progress)
        if current_month_expenses > budget:
            st.error(f"This month's expenses: {money(current_month_expenses)} · Over budget by {money(current_month_expenses - budget)}")
        else:
            st.success(f"This month's expenses: {money(current_month_expenses)} · Remaining: {money(budget - current_month_expenses)}")
    with right:
        with st.form("budget_form"):
            new_budget = st.number_input("Set monthly budget (₹)", min_value=0.0, value=float(budget), step=500.0)
            if st.form_submit_button("Save Budget", use_container_width=True):
                st.session_state.monthly_budget = float(new_budget)
                try:
                    save_budget(float(new_budget))
                    st.success("Budget saved.")
                except OSError:
                    st.error("Could not save budget.")
                st.rerun()

st.divider()
st.subheader("Add a Transaction")
with st.form("add_transaction", clear_on_submit=True):
    c1, c2, c3 = st.columns(3)
    with c1:
        kind = st.selectbox("Type", ["Expense", "Income"])
        amount = st.number_input("Amount (₹)", min_value=0.01, value=100.0, step=50.0)
    with c2:
        category = st.selectbox("Category", CATEGORIES, index=1 if kind == "Expense" else 0)
        date_value = st.date_input("Date", value=today, format="DD-MM-YYYY")
    with c3:
        description = st.text_input("Description", placeholder="e.g. groceries, salary")
    submitted = st.form_submit_button("＋ Add Transaction", type="primary")
    if submitted:
        new_id = max((x["ID"] for x in transactions), default=0) + 1
        transactions.append({
            "ID": new_id, "Type": kind, "Amount": float(amount),
            "Category": category, "Date": date_value.strftime("%d-%m-%Y"),
            "Description": description.strip()
        })
        try:
            save_transactions(transactions)
            st.success("Transaction added successfully.")
            st.rerun()
        except OSError:
            st.error("Could not save transaction. Please check file permissions.")

st.divider()
st.subheader("Transaction History")

f1, f2, f3 = st.columns([2, 1, 1])
with f1:
    query = st.text_input("Search", placeholder="Search description, category, date, amount...")
with f2:
    chosen_type = st.selectbox("Filter by type", ["All", "Income", "Expense"])
with f3:
    chosen_category = st.selectbox("Filter by category", ["All"] + CATEGORIES)

filtered = []
for item in transactions:
    if chosen_type != "All" and item["Type"] != chosen_type:
        continue
    if chosen_category != "All" and item["Category"] != chosen_category:
        continue
    searchable = " ".join(str(item[k]) for k in ["ID", "Type", "Amount", "Category", "Date", "Description"]).lower()
    if query.lower().strip() and query.lower().strip() not in searchable:
        continue
    filtered.append(item)

filtered.sort(key=lambda x: (parse_date(x["Date"]) or datetime.min.date(), x["ID"]), reverse=True)
st.caption(f"{len(filtered)} transaction(s)")
if filtered:
    df = pd.DataFrame(filtered)
    df = df.rename(columns={"ID": "ID", "Type": "Type", "Amount": "Amount (₹)"})
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No transactions match these filters yet.")

if transactions:
    st.markdown("**Edit or delete a transaction**")
    options = {f'#{x["ID"]} · {x["Type"]} · {money(x["Amount"])} · {x["Category"]} · {x["Date"]}': x["ID"] for x in transactions}
    selected_label = st.selectbox("Choose transaction", list(options.keys()))
    selected_id = options[selected_label]
    selected = next(x for x in transactions if x["ID"] == selected_id)
    with st.expander("Edit selected transaction"):
        with st.form("edit_transaction"):
            e1, e2, e3 = st.columns(3)
            with e1:
                edit_type = st.selectbox("Type", ["Income", "Expense"], index=0 if selected["Type"] == "Income" else 1)
                edit_amount = st.number_input("Amount (₹)", min_value=0.01, value=float(selected["Amount"]), step=50.0)
            with e2:
                edit_category = st.selectbox("Category", CATEGORIES, index=CATEGORIES.index(selected["Category"]) if selected["Category"] in CATEGORIES else len(CATEGORIES)-1)
                parsed = parse_date(selected["Date"]) or today
                edit_date = st.date_input("Date", value=parsed, format="DD-MM-YYYY")
            with e3:
                edit_description = st.text_input("Description", value=selected["Description"])
            if st.form_submit_button("Save Changes"):
                selected.update({
                    "Type": edit_type, "Amount": float(edit_amount),
                    "Category": edit_category, "Date": edit_date.strftime("%d-%m-%Y"),
                    "Description": edit_description.strip()
                })
                save_transactions(transactions)
                st.success("Transaction updated.")
                st.rerun()
    if st.button("🗑️ Delete selected transaction", type="secondary"):
        st.session_state.transactions = [x for x in transactions if x["ID"] != selected_id]
        save_transactions(st.session_state.transactions)
        st.success("Transaction deleted.")
        st.rerun()

st.divider()
st.subheader("Reports")
expenses_by_category = defaultdict(float)
for item in transactions:
    if item["Type"] == "Expense":
        expenses_by_category[item["Category"]] += item["Amount"]

tab1, tab2 = st.tabs(["Expense Chart", "Monthly Report"])
with tab1:
    if expenses_by_category:
        chart_df = pd.DataFrame([
            {"Category": k, "Amount (₹)": v} for k, v in sorted(expenses_by_category.items(), key=lambda pair: pair[1], reverse=True)
        ]).set_index("Category")
        st.bar_chart(chart_df)
    else:
        st.info("Add expense transactions to see the category chart.")
with tab2:
    month_items = [
        x for x in transactions if parse_date(x["Date"])
        and parse_date(x["Date"]).year == today.year
        and parse_date(x["Date"]).month == today.month
    ]
    month_income = sum(x["Amount"] for x in month_items if x["Type"] == "Income")
    month_expense = sum(x["Amount"] for x in month_items if x["Type"] == "Expense")
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("This Month's Income", money(month_income))
    r2.metric("This Month's Expenses", money(month_expense))
    r3.metric("Monthly Balance", money(month_income - month_expense))
    r4.metric("Budget", money(budget))
    if month_items:
        st.dataframe(pd.DataFrame(month_items), use_container_width=True, hide_index=True)
    else:
        st.info("No transactions for the current month.")

if transactions:
    export_df = pd.DataFrame(transactions)
    csv_data = export_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Export Transactions as CSV", data=csv_data, file_name="expense_report.csv", mime="text/csv")

st.caption("Note: This demo stores data in local CSV/JSON files. Hosted free-app storage may reset when the app restarts; use a database for reliable long-term multi-user storage.")

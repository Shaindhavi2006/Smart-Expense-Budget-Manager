import csv
import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from collections import defaultdict

APP_TITLE = "Smart Expense & Budget Manager"
DATA_FILE = "transactions.csv"
BUDGET_FILE = "budget.json"

CATEGORIES = [
    "Salary", "Food", "Travel", "Shopping", "Education",
    "Bills", "Entertainment", "Health", "Other"
]

BG = "#F2F5FB"
NAVY = "#172B4D"
GREEN = "#16845B"
RED = "#E5484D"
BLUE = "#3563E9"
PURPLE = "#7950D6"
GRAY = "#65758B"
WHITE = "#FFFFFF"


class SmartFinanceManager:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1250x750")
        self.root.minsize(1000, 650)
        self.root.configure(bg=BG)

        self.transactions = []
        self.next_id = 1
        self.monthly_budget = 5000.0

        self.load_transactions()
        self.load_budget()
        self.setup_styles()
        self.build_ui()
        self.refresh_all()

    def setup_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "Treeview",
            background=WHITE,
            foreground=NAVY,
            rowheight=30,
            fieldbackground=WHITE,
            font=("Segoe UI", 10)
        )
        style.configure(
            "Treeview.Heading",
            background="#E8EEF9",
            foreground=NAVY,
            font=("Segoe UI", 10, "bold")
        )
        style.map(
            "Treeview",
            background=[("selected", "#D6E4FF")],
            foreground=[("selected", NAVY)]
        )
        style.configure("TCombobox", padding=5)

    def make_button(self, parent, text, command, color=BLUE):
        return tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg=WHITE,
            activebackground=color,
            activeforeground=WHITE,
            relief="flat",
            cursor="hand2",
            font=("Segoe UI", 9, "bold"),
            padx=12,
            pady=9
        )

    def money(self, amount):
        return f"₹{amount:,.2f}"

    def load_transactions(self):
        self.transactions = []
        if not os.path.exists(DATA_FILE):
            self.next_id = 1
            return

        try:
            with open(DATA_FILE, "r", newline="", encoding="utf-8-sig") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        transaction = {
                            "id": int(row.get("ID", row.get("id", 0))),
                            "type": row.get("Type", row.get("type", "Expense")).strip().title(),
                            "amount": float(row.get("Amount", row.get("amount", 0))),
                            "category": row.get("Category", row.get("category", "Other")).strip(),
                            "date": row.get("Date", row.get("date", datetime.now().strftime("%d-%m-%Y"))).strip(),
                            "description": row.get("Description", row.get("description", "")).strip()
                        }
                        if transaction["amount"] >= 0:
                            self.transactions.append(transaction)
                    except (ValueError, TypeError):
                        continue
        except (OSError, csv.Error) as error:
            messagebox.showerror("File Error", f"Could not read transactions.csv:\n{error}")

        # Repair missing or duplicate IDs safely.
        used_ids = set()
        largest_id = 0
        for item in self.transactions:
            item_id = item["id"]
            if item_id <= 0 or item_id in used_ids:
                largest_id += 1
                while largest_id in used_ids:
                    largest_id += 1
                item["id"] = largest_id
                used_ids.add(largest_id)
            else:
                used_ids.add(item_id)
                largest_id = max(largest_id, item_id)

        self.next_id = max(used_ids, default=0) + 1
        self.save_transactions()

    def save_transactions(self):
        try:
            with open(DATA_FILE, "w", newline="", encoding="utf-8") as file:
                fields = ["ID", "Type", "Amount", "Category", "Date", "Description"]
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                for item in self.transactions:
                    writer.writerow({
                        "ID": item["id"],
                        "Type": item["type"],
                        "Amount": f'{item["amount"]:.2f}',
                        "Category": item["category"],
                        "Date": item["date"],
                        "Description": item["description"]
                    })
        except OSError as error:
            messagebox.showerror("Save Error", f"Could not save transactions:\n{error}")

    def load_budget(self):
        if os.path.exists(BUDGET_FILE):
            try:
                with open(BUDGET_FILE, "r", encoding="utf-8") as file:
                    data = json.load(file)
                self.monthly_budget = max(0.0, float(data.get("monthly_budget", 5000)))
            except (OSError, ValueError, TypeError, json.JSONDecodeError):
                self.monthly_budget = 5000.0

    def save_budget(self):
        try:
            with open(BUDGET_FILE, "w", encoding="utf-8") as file:
                json.dump({"monthly_budget": self.monthly_budget}, file, indent=4)
        except OSError as error:
            messagebox.showerror("Save Error", f"Could not save budget:\n{error}")

    def parse_date(self, value):
        for fmt in ("%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except (ValueError, AttributeError):
                continue
        return None

    def is_current_month(self, item):
        parsed = self.parse_date(item["date"])
        today = datetime.now()
        return bool(parsed and parsed.year == today.year and parsed.month == today.month)

    def build_ui(self):
        header = tk.Frame(self.root, bg=NAVY, pady=16)
        header.pack(fill="x")

        tk.Label(
            header, text=APP_TITLE,
            font=("Segoe UI", 23, "bold"),
            bg=NAVY, fg=WHITE
        ).pack()

        tk.Label(
            header, text="Track your money. Manage your future.",
            font=("Segoe UI", 10),
            bg=NAVY, fg="#D8E3FF"
        ).pack(pady=(4, 0))

        cards = tk.Frame(self.root, bg=BG)
        cards.pack(fill="x", padx=20, pady=14)

        self.income_value = self.create_card(cards, "TOTAL INCOME", GREEN)
        self.expense_value = self.create_card(cards, "TOTAL EXPENSES", RED)
        self.balance_value = self.create_card(cards, "CURRENT BALANCE", BLUE)

        budget_frame = tk.Frame(self.root, bg=WHITE, highlightbackground="#D8E1F0", highlightthickness=1)
        budget_frame.pack(fill="x", padx=20, pady=(0, 12))

        top = tk.Frame(budget_frame, bg=WHITE)
        top.pack(fill="x", padx=16, pady=(12, 5))

        tk.Label(top, text="Monthly Budget", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 11, "bold")).pack(side="left")

        self.budget_value = tk.Label(top, text="", bg=WHITE, fg=NAVY,
                                     font=("Segoe UI", 10, "bold"))
        self.budget_value.pack(side="right")

        self.budget_bar = ttk.Progressbar(
            budget_frame, orient="horizontal", mode="determinate", maximum=100
        )
        self.budget_bar.pack(fill="x", padx=16, pady=5)

        bottom = tk.Frame(budget_frame, bg=WHITE)
        bottom.pack(fill="x", padx=16, pady=(4, 12))

        self.budget_message = tk.Label(
            bottom, text="", bg=WHITE, fg=GRAY, font=("Segoe UI", 9)
        )
        self.budget_message.pack(side="left")

        self.make_button(bottom, "Set Budget", self.set_budget, PURPLE).pack(side="right")

        actions = tk.Frame(self.root, bg=BG)
        actions.pack(fill="x", padx=20, pady=2)

        self.make_button(actions, "+ Add Income",
                         lambda: self.transaction_form("Income"), GREEN).pack(side="left", padx=(0, 8))
        self.make_button(actions, "+ Add Expense",
                         lambda: self.transaction_form("Expense"), RED).pack(side="left", padx=0)
        self.make_button(actions, "Edit Selected",
                         self.edit_transaction, BLUE).pack(side="left", padx=8)
        self.make_button(actions, "Delete Selected",
                         self.delete_transaction, GRAY).pack(side="left", padx=0)

        self.make_button(actions, "Expense Chart",
                         self.monthly_expense_chart, GREEN).pack(side="right", padx=(8, 0))
        self.make_button(actions, "Category Report",
                         self.category_report, NAVY).pack(side="right", padx=(8, 0))
        self.make_button(actions, "Monthly Report",
                         self.monthly_financial_report, PURPLE).pack(side="right", padx=(8, 0))
        self.make_button(actions, "Export CSV",
                         self.export_csv, BLUE).pack(side="right", padx=(8, 0))

        filters = tk.Frame(self.root, bg=WHITE, highlightbackground="#D8E1F0", highlightthickness=1)
        filters.pack(fill="x", padx=20, pady=10)

        tk.Label(filters, text="Search", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(12, 6), pady=10)
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(filters, textvariable=self.search_var, width=18)
        search_entry.pack(side="left", padx=(0, 14), pady=10)
        search_entry.bind("<KeyRelease>", lambda event: self.refresh_table())

        tk.Label(filters, text="Type", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        self.type_var = tk.StringVar(value="All")
        type_box = ttk.Combobox(
            filters, textvariable=self.type_var,
            values=["All", "Income", "Expense"], state="readonly", width=12
        )
        type_box.pack(side="left", padx=(0, 14))
        type_box.bind("<<ComboboxSelected>>", lambda event: self.refresh_table())

        tk.Label(filters, text="Category", bg=WHITE, fg=NAVY,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 6))
        self.category_var = tk.StringVar(value="All")
        category_box = ttk.Combobox(
            filters, textvariable=self.category_var,
            values=["All"] + CATEGORIES, state="readonly", width=16
        )
        category_box.pack(side="left", padx=(0, 14))
        category_box.bind("<<ComboboxSelected>>", lambda event: self.refresh_table())

        self.make_button(filters, "Clear Filters", self.clear_filters, GRAY).pack(side="left", pady=5)

        history = tk.Frame(self.root, bg=WHITE, highlightbackground="#D8E1F0", highlightthickness=1)
        history.pack(fill="both", expand=True, padx=20, pady=(0, 16))

        title_row = tk.Frame(history, bg=WHITE)
        title_row.pack(fill="x", padx=16, pady=(12, 8))

        tk.Label(title_row, text="Transaction History",
                 font=("Segoe UI", 14, "bold"), bg=WHITE, fg=NAVY).pack(side="left")

        self.count_label = tk.Label(title_row, text="0 transaction(s)",
                                    font=("Segoe UI", 9), bg=WHITE, fg=GRAY)
        self.count_label.pack(side="right")

        table_frame = tk.Frame(history, bg=WHITE)
        table_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        columns = ("ID", "Type", "Amount", "Category", "Date", "Description")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")

        widths = {
            "ID": 60, "Type": 100, "Amount": 130,
            "Category": 140, "Date": 130, "Description": 360
        }
        for col in columns:
            self.tree.heading(col, text=col if col != "Amount" else "Amount (₹)")
            self.tree.column(col, width=widths[col], minwidth=55, anchor="center")

        self.tree.column("Description", anchor="w")
        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        x_scroll = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll.grid(row=1, column=0, sticky="ew")
        table_frame.rowconfigure(0, weight=1)
        table_frame.columnconfigure(0, weight=1)

        self.tree.tag_configure("Income", foreground=GREEN)
        self.tree.tag_configure("Expense", foreground=RED)

    def create_card(self, parent, title, color):
        card = tk.Frame(parent, bg=WHITE, highlightbackground="#D8E1F0", highlightthickness=1)
        card.pack(side="left", fill="both", expand=True, padx=6)

        tk.Frame(card, bg=color, height=4).pack(fill="x")

        tk.Label(card, text=title, bg=WHITE, fg=GRAY,
                 font=("Segoe UI", 10, "bold")).pack(pady=(15, 7))

        value = tk.Label(card, text="₹0.00", bg=WHITE, fg=color,
                         font=("Segoe UI", 19, "bold"))
        value.pack(pady=(0, 17))
        return value

    def refresh_dashboard(self):
        income = sum(x["amount"] for x in self.transactions if x["type"] == "Income")
        expenses = sum(x["amount"] for x in self.transactions if x["type"] == "Expense")
        balance = income - expenses

        self.income_value.config(text=self.money(income))
        self.expense_value.config(text=self.money(expenses))
        self.balance_value.config(text=self.money(balance))

        current_expenses = sum(
            x["amount"] for x in self.transactions
            if x["type"] == "Expense" and self.is_current_month(x)
        )
        self.budget_value.config(text=self.money(self.monthly_budget))

        percentage = (
            current_expenses / self.monthly_budget * 100
            if self.monthly_budget > 0 else (100 if current_expenses else 0)
        )
        self.budget_bar["value"] = min(percentage, 100)

        if current_expenses > self.monthly_budget:
            self.budget_bar.configure(style="Red.Horizontal.TProgressbar")
            message = f"This month's expenses: {self.money(current_expenses)}  |  Over budget by {self.money(current_expenses - self.monthly_budget)}"
            color = RED
        else:
            self.budget_bar.configure(style="Green.Horizontal.TProgressbar")
            message = f"This month's expenses: {self.money(current_expenses)}  |  Remaining: {self.money(self.monthly_budget - current_expenses)}"
            color = GREEN

        self.budget_message.config(text=message, fg=color)

        style = ttk.Style()
        style.configure("Red.Horizontal.TProgressbar", troughcolor="#F0DADA", background=RED)
        style.configure("Green.Horizontal.TProgressbar", troughcolor="#DDEEE5", background=GREEN)

    def refresh_table(self):
        # Always clear the table before inserting, preventing duplicate Treeview IDs.
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        query = self.search_var.get().strip().lower()
        chosen_type = self.type_var.get()
        chosen_category = self.category_var.get()

        filtered = []
        for item in self.transactions:
            if chosen_type != "All" and item["type"] != chosen_type:
                continue
            if chosen_category != "All" and item["category"] != chosen_category:
                continue

            searchable = (
                str(item["id"]) + " " + item["type"] + " " +
                item["category"] + " " + item["date"] + " " +
                item["description"] + " " + str(item["amount"])
            ).lower()

            if query and query not in searchable:
                continue
            filtered.append(item)

        filtered.sort(key=lambda x: (self.parse_date(x["date"]) or datetime.min, x["id"]), reverse=True)

        for item in filtered:
            self.tree.insert(
                "", "end",
                iid=f"transaction_{item['id']}",
                values=(
                    item["id"], item["type"], f"{item['amount']:,.2f}",
                    item["category"], item["date"], item["description"]
                ),
                tags=(item["type"],)
            )

        self.count_label.config(text=f"{len(filtered)} transaction(s)")

    def refresh_all(self):
        self.refresh_dashboard()
        self.refresh_table()

    def clear_filters(self):
        self.search_var.set("")
        self.type_var.set("All")
        self.category_var.set("All")
        self.refresh_table()

    def transaction_form(self, kind, transaction=None):
        editing = transaction is not None

        win = tk.Toplevel(self.root)
        win.title("Edit Transaction" if editing else f"Add {kind}")
        win.geometry("430x430")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.transient(self.root)
        win.grab_set()

        tk.Label(
            win, text="Edit Transaction" if editing else f"Add {kind}",
            font=("Segoe UI", 17, "bold"), bg=BG, fg=NAVY
        ).pack(pady=(18, 12))

        form = tk.Frame(win, bg=WHITE, padx=20, pady=16)
        form.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        tk.Label(form, text="Type", bg=WHITE, fg=NAVY).grid(row=0, column=0, sticky="w", pady=7)
        type_var = tk.StringVar(value=transaction["type"] if editing else kind)
        type_box = ttk.Combobox(form, textvariable=type_var, values=["Income", "Expense"], state="readonly")
        type_box.grid(row=0, column=1, sticky="ew", pady=7)

        tk.Label(form, text="Amount (₹)", bg=WHITE, fg=NAVY).grid(row=1, column=0, sticky="w", pady=7)
        amount_var = tk.StringVar(value=str(transaction["amount"]) if editing else "")
        tk.Entry(form, textvariable=amount_var).grid(row=1, column=1, sticky="ew", pady=7)

        tk.Label(form, text="Category", bg=WHITE, fg=NAVY).grid(row=2, column=0, sticky="w", pady=7)
        category_var = tk.StringVar(value=transaction["category"] if editing else ("Salary" if kind == "Income" else "Food"))
        category_box = ttk.Combobox(form, textvariable=category_var, values=CATEGORIES, state="readonly")
        category_box.grid(row=2, column=1, sticky="ew", pady=7)

        tk.Label(form, text="Date (DD-MM-YYYY)", bg=WHITE, fg=NAVY).grid(row=3, column=0, sticky="w", pady=7)
        date_var = tk.StringVar(value=transaction["date"] if editing else datetime.now().strftime("%d-%m-%Y"))
        tk.Entry(form, textvariable=date_var).grid(row=3, column=1, sticky="ew", pady=7)

        tk.Label(form, text="Description", bg=WHITE, fg=NAVY).grid(row=4, column=0, sticky="w", pady=7)
        desc_var = tk.StringVar(value=transaction["description"] if editing else "")
        tk.Entry(form, textvariable=desc_var).grid(row=4, column=1, sticky="ew", pady=7)

        form.columnconfigure(1, weight=1)

        def save():
            try:
                amount = float(amount_var.get().strip())
                if amount <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid Amount", "Enter an amount greater than zero.", parent=win)
                return

            parsed = self.parse_date(date_var.get())
            if not parsed:
                messagebox.showwarning("Invalid Date", "Use DD-MM-YYYY format.", parent=win)
                return

            new_item = {
                "id": transaction["id"] if editing else self.next_id,
                "type": type_var.get(),
                "amount": amount,
                "category": category_var.get(),
                "date": parsed.strftime("%d-%m-%Y"),
                "description": desc_var.get().strip()
            }

            if editing:
                for index, old_item in enumerate(self.transactions):
                    if old_item["id"] == transaction["id"]:
                        self.transactions[index] = new_item
                        break
            else:
                self.transactions.append(new_item)
                self.next_id += 1

            self.save_transactions()
            self.refresh_all()
            win.destroy()

        self.make_button(form, "Save Transaction", save, GREEN).grid(
            row=5, column=0, columnspan=2, sticky="ew", pady=(18, 0)
        )

    def get_selected(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Select Transaction", "Please select a transaction first.")
            return None

        try:
            selected_id = int(self.tree.item(selection[0], "values")[0])
        except (ValueError, IndexError):
            messagebox.showerror("Selection Error", "Could not read the selected transaction.")
            return None

        for item in self.transactions:
            if item["id"] == selected_id:
                return item
        messagebox.showwarning("Not Found", "That transaction no longer exists.")
        return None

    def edit_transaction(self):
        item = self.get_selected()
        if item:
            self.transaction_form(item["type"], item)

    def delete_transaction(self):
        item = self.get_selected()
        if not item:
            return

        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete this transaction?\n\n{item['type']} — {self.money(item['amount'])}"
        ):
            self.transactions = [x for x in self.transactions if x["id"] != item["id"]]
            self.save_transactions()
            self.refresh_all()

    def set_budget(self):
        win = tk.Toplevel(self.root)
        win.title("Set Monthly Budget")
        win.geometry("360x200")
        win.resizable(False, False)
        win.configure(bg=BG)
        win.transient(self.root)
        win.grab_set()

        tk.Label(win, text="Set Monthly Budget",
                 font=("Segoe UI", 16, "bold"), bg=BG, fg=NAVY).pack(pady=(22, 12))

        amount_var = tk.StringVar(value=str(self.monthly_budget))
        entry = tk.Entry(win, textvariable=amount_var, justify="center", font=("Segoe UI", 12))
        entry.pack(padx=24, fill="x", pady=5)
        entry.focus_set()

        def save():
            try:
                amount = float(amount_var.get().strip())
                if amount < 0:
                    raise ValueError
            except ValueError:
                messagebox.showwarning("Invalid Budget", "Enter zero or a positive amount.", parent=win)
                return

            self.monthly_budget = amount
            self.save_budget()
            self.refresh_dashboard()
            win.destroy()

        self.make_button(win, "Save Budget", save, PURPLE).pack(pady=15)

    def monthly_expense_chart(self):
        expenses = defaultdict(float)
        for item in self.transactions:
            if item["type"] == "Expense":
                expenses[item["category"]] += item["amount"]

        if not expenses:
            messagebox.showinfo("Expense Chart", "No expense records to display.")
            return

        try:
            import matplotlib.pyplot as plt
        except ImportError:
            messagebox.showerror(
                "Missing Library",
                "Chart needs matplotlib.\nInstall it using: python -m pip install matplotlib"
            )
            return

        categories = sorted(expenses, key=expenses.get)
        values = [expenses[c] for c in categories]

        fig, ax = plt.subplots(figsize=(9, 5))
        bars = ax.barh(categories, values)
        ax.set_title("Expense Chart by Category", fontsize=15, fontweight="bold")
        ax.set_xlabel("Amount (₹)")
        ax.grid(axis="x", alpha=0.25)
        ax.bar_label(bars, labels=[f"₹{v:,.0f}" for v in values], padding=4)
        fig.tight_layout()
        plt.show()

    def category_report(self):
        totals = defaultdict(float)
        for item in self.transactions:
            if item["type"] == "Expense":
                totals[item["category"]] += item["amount"]

        win = tk.Toplevel(self.root)
        win.title("Expense Category Report")
        win.geometry("560x460")
        win.configure(bg=BG)

        tk.Label(win, text="Expense Category Report",
                 font=("Segoe UI", 18, "bold"), bg=BG, fg=NAVY).pack(pady=(18, 5))
        tk.Label(win, text="Total expenses grouped by category",
                 font=("Segoe UI", 10), bg=BG, fg=GRAY).pack(pady=(0, 12))

        frame = tk.Frame(win, bg=WHITE)
        frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        tree = ttk.Treeview(frame, columns=("Category", "Total"), show="headings")
        tree.heading("Category", text="Category")
        tree.heading("Total", text="Total Expense (₹)")
        tree.column("Category", width=240)
        tree.column("Total", width=220, anchor="e")
        tree.pack(fill="both", expand=True, padx=10, pady=10)

        for category, total in sorted(totals.items(), key=lambda pair: pair[1], reverse=True):
            tree.insert("", "end", values=(category, f"{total:,.2f}"))

        if not totals:
            tree.insert("", "end", values=("No expenses recorded", "₹0.00"))

    def monthly_financial_report(self):
        now = datetime.now()
        month_items = [
            item for item in self.transactions
            if (self.parse_date(item["date"]) is not None)
            and self.parse_date(item["date"]).year == now.year
            and self.parse_date(item["date"]).month == now.month
        ]

        income = sum(x["amount"] for x in month_items if x["type"] == "Income")
        expenses = sum(x["amount"] for x in month_items if x["type"] == "Expense")
        balance = income - expenses

        win = tk.Toplevel(self.root)
        win.title("Monthly Financial Report")
        win.geometry("900x600")
        win.minsize(750, 450)
        win.configure(bg=BG)

        tk.Label(
            win, text=f"Monthly Financial Report — {now.strftime('%B %Y')}",
            font=("Segoe UI", 18, "bold"), bg=BG, fg=NAVY
        ).pack(pady=(18, 12))

        summary = tk.Frame(win, bg=BG)
        summary.pack(fill="x", padx=14)

        for title, value, color in [
            ("Income", income, GREEN),
            ("Expenses", expenses, RED),
            ("Balance", balance, BLUE),
            ("Budget", self.monthly_budget, PURPLE)
        ]:
            card = tk.Frame(summary, bg=WHITE, highlightbackground="#D8E1F0", highlightthickness=1)
            card.pack(side="left", fill="both", expand=True, padx=5)
            tk.Label(card, text=title, bg=WHITE, fg=GRAY,
                     font=("Segoe UI", 10, "bold")).pack(pady=(12, 4))
            tk.Label(card, text=self.money(value), bg=WHITE, fg=color,
                     font=("Segoe UI", 13, "bold")).pack(pady=(0, 12))

        if expenses > self.monthly_budget:
            budget_text = f"Over budget by {self.money(expenses - self.monthly_budget)}"
            budget_color = RED
        else:
            budget_text = f"Remaining budget: {self.money(self.monthly_budget - expenses)}"
            budget_color = GREEN

        tk.Label(win, text=budget_text, bg=BG, fg=budget_color,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=22, pady=12)

        frame = tk.Frame(win, bg=WHITE)
        frame.pack(fill="both", expand=True, padx=18, pady=(0, 18))

        columns = ("Date", "Type", "Category", "Amount", "Description")
        tree = ttk.Treeview(frame, columns=columns, show="headings")
        for col in columns:
            tree.heading(col, text=col if col != "Amount" else "Amount (₹)")
            tree.column(col, width=140, anchor="center")
        tree.column("Description", width=240, anchor="w")

        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)
        scrollbar.pack(side="right", fill="y", padx=(0, 8), pady=8)

        month_items.sort(
            key=lambda x: self.parse_date(x["date"]) or datetime.min,
            reverse=True
        )
        for item in month_items:
            tree.insert("", "end", values=(
                item["date"], item["type"], item["category"],
                f"{item['amount']:,.2f}", item["description"]
            ))

        if not month_items:
            tree.insert("", "end", values=("-", "-", "No transactions", "0.00", "-"))

    def export_csv(self):
        if not self.transactions:
            messagebox.showinfo("Export CSV", "There are no transactions to export.")
            return

        path = filedialog.asksaveasfilename(
            title="Export Transactions",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="expense_report.csv"
        )
        if not path:
            return

        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                fields = ["ID", "Type", "Amount", "Category", "Date", "Description"]
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                for item in self.transactions:
                    writer.writerow({
                        "ID": item["id"],
                        "Type": item["type"],
                        "Amount": f'{item["amount"]:.2f}',
                        "Category": item["category"],
                        "Date": item["date"],
                        "Description": item["description"]
                    })
            messagebox.showinfo("Export Successful", f"CSV exported successfully:\n{path}")
        except OSError as error:
            messagebox.showerror("Export Error", f"Could not export CSV:\n{error}")


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartFinanceManager(root)
    root.mainloop()

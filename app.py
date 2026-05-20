"""
app.py — Flask web app for the expense tracker.

Run with:  python3 app.py
Then open: http://127.0.0.1:8080

Flask is a lightweight web framework. Each function below is a "route" —
it maps a URL to a Python function that returns an HTML page.
"""

from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import date
from tracker import (
    add_expense,
    delete_expense,
    load_expenses,
    get_monthly_expenses,
    get_monthly_income,
    set_monthly_income,
    summarise_by_category,
    load_recurring,
    add_recurring,
    delete_recurring,
    load_wishlist,
    add_wish,
    delete_wish,
    toggle_wish_purchased,
    VALID_CATEGORIES,
    VALID_ORIGINS,
    VALID_WISH_TYPES,
    VALID_WISH_PRIORITIES,
)

app = Flask(__name__)
# A secret key is required for Flask's flash() messages (error/success banners).
# In a real app you'd load this from an environment variable, not hardcode it.
app.secret_key = "cream-expense-tracker-secret"

# One color per category — used in charts and category badges.
CATEGORY_COLORS = {
    "food":          "#4caf50",
    "grocery":       "#9c7ee0",
    "transport":     "#f0a050",
    "subscriptions": "#5aabde",
    "extras":        "#e07a50",
    "bet":           "#d4be45",
}


@app.route("/")
def dashboard():
    """Home page: log-expense form + the 5 most recent expenses + saldo."""
    today = date.today()
    all_expenses = load_expenses()
    recent = list(reversed(all_expenses))[:5]

    # Split this month's expenses by origin for the saldo and credit sections.
    monthly_expenses = get_monthly_expenses(today.year, today.month)
    debit_expenses  = [e for e in monthly_expenses if e.get("origin", "debit") == "debit"]
    credit_expenses = [e for e in monthly_expenses if e.get("origin") == "credit"]

    spent_debit  = sum(float(e["amount"]) for e in debit_expenses)
    spent_credit = sum(float(e["amount"]) for e in credit_expenses)

    income = get_monthly_income(today.year, today.month)
    remaining = income - spent_debit

    recurring = load_recurring()
    recurring_debit_total  = sum(float(r["amount"]) for r in recurring if r.get("origin", "debit") == "debit")
    recurring_credit_total = sum(float(r["amount"]) for r in recurring if r.get("origin") == "credit")

    return render_template(
        "index.html",
        recent=recent,
        categories=VALID_CATEGORIES,
        origins=VALID_ORIGINS,
        category_colors=CATEGORY_COLORS,
        today=today.isoformat(),
        income=income,
        remaining=remaining,
        spent_debit=spent_debit,
        spent_credit=spent_credit,
        credit_expenses=list(reversed(credit_expenses)),
        current_year=today.year,
        current_month=today.month,
        recurring=recurring,
        recurring_debit_total=recurring_debit_total,
        recurring_credit_total=recurring_credit_total,
    )


@app.route("/add", methods=["POST"])
def add():
    """Handle the log-expense form submission."""
    # request.form is a dict of the values the user typed into the form.
    try:
        amount = float(request.form["amount"])
        category = request.form["category"]
        note = request.form.get("note", "")
        expense_date_str = request.form.get("expense_date", "")

        # Parse the date if the user provided one, otherwise default to today.
        if expense_date_str:
            expense_date = date.fromisoformat(expense_date_str)
        else:
            expense_date = date.today()

        origin = request.form.get("origin", "debit")
        if origin == "recurring":
            add_recurring(amount, category, note)
            flash(f"Added R${amount:.2f} in {category} as monthly recurring.", "success")
        else:
            add_expense(amount, category, note, expense_date, origin)
            flash(f"Logged R${amount:.2f} in {category} ({origin}).", "success")
    except (ValueError, KeyError) as e:
        flash(f"Error: {e}", "error")

    # Redirect back to the dashboard after saving.
    return redirect(url_for("dashboard"))


@app.route("/history")
def history():
    """Full expense history, newest first."""
    all_expenses = load_expenses()
    # Attach the real CSV row index to each expense before reversing,
    # so the delete button knows which row to remove.
    for i, e in enumerate(all_expenses):
        e["csv_index"] = i
    expenses = list(reversed(all_expenses))
    return render_template(
        "history.html",
        expenses=expenses,
        category_colors=CATEGORY_COLORS,
    )


@app.route("/report")
def report():
    """Monthly report: spending table + Chart.js bar chart."""
    today = date.today()
    # Read year/month from the URL query string, e.g. /report?year=2026&month=5
    # Defaults to the current month if not provided.
    try:
        year = int(request.args.get("year", today.year))
        month = int(request.args.get("month", today.month))
        if not (1 <= month <= 12):
            raise ValueError
    except ValueError:
        flash("Invalid month or year — showing current month instead.", "error")
        year, month = today.year, today.month

    expenses = get_monthly_expenses(year, month)
    debit_expenses  = [e for e in expenses if e.get("origin", "debit") == "debit"]
    credit_expenses = [e for e in expenses if e.get("origin") == "credit"]

    debit_totals  = summarise_by_category(debit_expenses)
    credit_totals = summarise_by_category(credit_expenses)
    grand_total   = sum(debit_totals.values()) + sum(credit_totals.values())

    def _chart_data(totals_dict):
        labels = list(totals_dict.keys())
        values = [round(v, 2) for v in totals_dict.values()]
        colors = [CATEGORY_COLORS.get(cat, "#94A3B8") for cat in labels]
        return labels, values, colors

    debit_labels,  debit_values,  debit_colors  = _chart_data(debit_totals)
    credit_labels, credit_values, credit_colors = _chart_data(credit_totals)

    recurring = load_recurring()
    recurring_total = sum(float(r["amount"]) for r in recurring)

    return render_template(
        "report.html",
        year=year,
        month=month,
        month_name=date(year, month, 1).strftime("%B %Y"),
        debit_totals=sorted(debit_totals.items(),  key=lambda x: x[1], reverse=True),
        credit_totals=sorted(credit_totals.items(), key=lambda x: x[1], reverse=True),
        debit_total=sum(debit_totals.values()),
        credit_total=sum(credit_totals.values()),
        grand_total=grand_total,
        debit_labels=debit_labels,   debit_values=debit_values,   debit_colors=debit_colors,
        credit_labels=credit_labels, credit_values=credit_values, credit_colors=credit_colors,
        category_colors=CATEGORY_COLORS,
        expense_count=len(expenses),
        recurring=recurring,
        recurring_total=recurring_total,
    )


@app.route("/set_income", methods=["POST"])
def set_income():
    """Add money to the monthly balance for a given month."""
    try:
        amount = float(request.form["income_amount"])
        if amount <= 0:
            raise ValueError("Amount must be positive.")
        year = int(request.form["income_year"])
        month = int(request.form["income_month"])
        current = get_monthly_income(year, month)
        new_total = current + amount
        set_monthly_income(year, month, new_total)
        flash(f"Added R${amount:.2f} — balance is now R${new_total:.2f}.", "success")
    except (ValueError, KeyError) as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("dashboard"))


@app.route("/delete/<int:index>", methods=["POST"])
def delete(index):
    """Delete one expense by its position in the CSV (oldest = 0)."""
    try:
        delete_expense(index)
        flash("Expense deleted.", "success")
    except IndexError as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("history"))


@app.route("/add_recurring", methods=["POST"])
def add_recurring_route():
    """Add a new monthly recurring expense."""
    try:
        amount   = float(request.form["recurring_amount"])
        category = request.form["recurring_category"]
        note     = request.form.get("recurring_note", "")
        origin   = request.form.get("recurring_origin", "debit")
        add_recurring(amount, category, note, origin)
        flash(f"Added recurring R${amount:.2f} in {category} ({origin}).", "success")
    except (ValueError, KeyError) as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("dashboard"))


@app.route("/delete_recurring/<int:index>", methods=["POST"])
def delete_recurring_route(index):
    """Remove a recurring expense by its list index."""
    try:
        delete_recurring(index)
        flash("Recurring expense removed.", "success")
    except IndexError as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("dashboard"))


def _age_label(added_date_str: str) -> str:
    """Return a human-readable age string, or '' if less than a week old."""
    if not added_date_str:
        return ""
    try:
        added = date.fromisoformat(added_date_str)
    except ValueError:
        return ""
    days = (date.today() - added).days
    if days < 7:
        return ""
    if days < 30:
        weeks = days // 7
        return f"{weeks} week{'s' if weeks > 1 else ''} in"
    months = days // 30
    return f"{months} month{'s' if months > 1 else ''} in"


@app.route("/wishlist")
def wishlist():
    """Wishlist page: items grouped by type."""
    items = load_wishlist()
    for i, item in enumerate(items):
        item["index"] = i
        item["age_label"] = _age_label(item.get("added_date", ""))
    total = sum(float(item["price"]) for item in items)
    by_type = {t: [item for item in items if item["type"] == t] for t in VALID_WISH_TYPES}
    type_totals = {t: sum(float(item["price"]) for item in grp) for t, grp in by_type.items()}
    return render_template(
        "wishlist.html",
        items=items,
        total=total,
        by_type=by_type,
        type_totals=type_totals,
        wish_types=VALID_WISH_TYPES,
        wish_priorities=VALID_WISH_PRIORITIES,
    )


@app.route("/add_wish", methods=["POST"])
def add_wish_route():
    """Add a new wishlist item."""
    try:
        name = request.form["wish_name"]
        wish_type = request.form["wish_type"]
        priority = request.form["wish_priority"]
        price = float(request.form["wish_price"])
        note = request.form.get("wish_note", "")
        link = request.form.get("wish_link", "")
        add_wish(name, wish_type, priority, price, note, link)
        flash(f"Added '{name}' to your wishlist.", "success")
    except (ValueError, KeyError) as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("wishlist"))


@app.route("/toggle_wish/<int:index>", methods=["POST"])
def toggle_wish_route(index):
    """Toggle purchased status of a wishlist item."""
    try:
        toggle_wish_purchased(index)
    except IndexError as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("wishlist"))


@app.route("/delete_wish/<int:index>", methods=["POST"])
def delete_wish_route(index):
    """Remove a wishlist item by index."""
    try:
        delete_wish(index)
        flash("Item removed from wishlist.", "success")
    except IndexError as e:
        flash(f"Error: {e}", "error")
    return redirect(url_for("wishlist"))


if __name__ == "__main__":
    # debug=True means Flask auto-reloads when you save a file — useful while developing.
    # Port 5000 is used by macOS AirPlay Receiver — 8080 avoids that conflict.
    app.run(debug=True, port=8080)

"""
tracker.py — Core logic for the expense tracker.

This module has no CLI or UI code — it's just functions that read and write
data. Both log.py and the future web app will import and call these functions.
That way, when you build the web UI, you don't need to rewrite any logic.
"""

import csv
import os
from datetime import date

# The CSV file where all expenses are stored.
# os.path.dirname(__file__) gives the folder this script lives in,
# so the path works no matter where you call it from.
CSV_PATH = os.path.join(os.path.dirname(__file__), "expenses.csv")

# Stores monthly income — one row per month, e.g. {"year": "2026", "month": "5", "amount": "5000.00"}
INCOME_PATH = os.path.join(os.path.dirname(__file__), "income.csv")
INCOME_COLUMNS = ["year", "month", "amount"]

# These are the only valid categories. Keeping a fixed list makes it easier
# to group spending in reports and avoids typos like "foood" vs "food".
VALID_CATEGORIES = [
    "food",
    "grocery",
    "transport",
    "subscriptions",
    "extras",
    "bet",
]

VALID_ORIGINS = ["debit", "credit"]

# The columns in expenses.csv, in order.
CSV_COLUMNS = ["date", "amount", "category", "note", "origin"]


def _ensure_csv_exists():
    """Create expenses.csv with a header row if it doesn't exist yet."""
    if not os.path.exists(CSV_PATH):
        with open(CSV_PATH, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()


def add_expense(amount: float, category: str, note: str = "", expense_date: date = None, origin: str = "debit") -> dict:
    """
    Write one expense to expenses.csv and return it as a dict.

    Parameters
    ----------
    amount   : the amount spent, e.g. 25.50
    category : must be one of VALID_CATEGORIES
    note     : optional short description, e.g. "energy drink"
    expense_date : defaults to today if not provided

    Raises ValueError if amount <= 0, category is not valid, or origin is not valid.
    """
    if amount <= 0:
        raise ValueError(f"Amount must be positive, got {amount}")

    category = category.lower().strip()
    if category not in VALID_CATEGORIES:
        raise ValueError(
            f"'{category}' is not a valid category. Choose from: {', '.join(VALID_CATEGORIES)}"
        )

    origin = origin.lower().strip()
    if origin not in VALID_ORIGINS:
        raise ValueError(
            f"'{origin}' is not a valid origin. Choose from: {', '.join(VALID_ORIGINS)}"
        )

    if expense_date is None:
        expense_date = date.today()

    expense = {
        "date": expense_date.isoformat(),
        "amount": f"{amount:.2f}",
        "category": category,
        "note": note.strip(),
        "origin": origin,
    }

    _ensure_csv_exists()

    # "a" = append mode, so we never overwrite existing expenses.
    with open(CSV_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow(expense)

    return expense


def load_expenses() -> list[dict]:
    """
    Read all rows from expenses.csv and return them as a list of dicts.
    Each dict looks like: {"date": "2026-05-19", "amount": "25.00", ...}
    Returns an empty list if the file doesn't exist yet.
    """
    _ensure_csv_exists()

    with open(CSV_PATH, "r", newline="") as f:
        rows = list(csv.DictReader(f))
    # Rows logged before the origin column was added won't have it — default to debit.
    for row in rows:
        row.setdefault("origin", "debit")
    return rows


def get_monthly_expenses(year: int, month: int) -> list[dict]:
    """
    Filter expenses to a specific year and month.
    Returns a list of expense dicts, same format as load_expenses().
    """
    all_expenses = load_expenses()
    # Keep only rows where the date starts with "YYYY-MM"
    prefix = f"{year}-{month:02d}"
    return [e for e in all_expenses if e["date"].startswith(prefix)]


def delete_expense(index: int) -> None:
    """
    Remove one expense from expenses.csv by its position in the list.

    index=0 means the first expense ever logged (oldest).
    The history page reverses the list, so it passes (total - 1 - display_index)
    to delete the right row.

    Raises IndexError if index is out of range.
    """
    expenses = load_expenses()
    if index < 0 or index >= len(expenses):
        raise IndexError(f"No expense at index {index}")
    expenses.pop(index)

    # Rewrite the whole file — CSV doesn't support deleting a single row in place.
    with open(CSV_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(expenses)


def set_monthly_income(year: int, month: int, amount: float) -> None:
    """
    Save (or update) the income for a given month.

    If an entry for that year/month already exists, it gets replaced.
    This means you can correct your income if you typed it wrong.
    """
    # Load existing entries, remove any for this month, add the new one.
    entries = _load_income()
    entries = [e for e in entries if not (int(e["year"]) == year and int(e["month"]) == month)]
    entries.append({"year": str(year), "month": str(month), "amount": f"{amount:.2f}"})

    with open(INCOME_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=INCOME_COLUMNS)
        writer.writeheader()
        writer.writerows(entries)


def get_monthly_income(year: int, month: int) -> float:
    """Return the income set for a given month, or 0.0 if none has been set."""
    for entry in _load_income():
        if int(entry["year"]) == year and int(entry["month"]) == month:
            return float(entry["amount"])
    return 0.0


def get_carry_forward_balance(year: int, month: int) -> float:
    """Return the leftover debit balance from the previous month."""
    if month == 1:
        prev_year, prev_month = year - 1, 12
    else:
        prev_year, prev_month = year, month - 1

    prev_income = get_monthly_income(prev_year, prev_month)
    prev_expenses = sum(
        float(e["amount"])
        for e in get_monthly_expenses(prev_year, prev_month)
        if e.get("origin", "debit") != "credit"
    )
    return round(prev_income - prev_expenses, 2)


def _load_income() -> list[dict]:
    """Read all rows from income.csv. Returns empty list if file doesn't exist."""
    if not os.path.exists(INCOME_PATH):
        return []
    with open(INCOME_PATH, "r", newline="") as f:
        return list(csv.DictReader(f))


RECURRING_PATH = os.path.join(os.path.dirname(__file__), "recurring.csv")
RECURRING_COLUMNS = ["amount", "category", "note", "origin"]


def load_recurring() -> list[dict]:
    """Return all recurring expenses, or an empty list if none saved yet."""
    if not os.path.exists(RECURRING_PATH):
        return []
    with open(RECURRING_PATH, "r", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row.setdefault("origin", "debit")
    return rows


def add_recurring(amount: float, category: str, note: str = "", origin: str = "debit") -> dict:
    """Append a recurring expense to recurring.csv."""
    if amount <= 0:
        raise ValueError(f"Amount must be positive, got {amount}")
    category = category.lower().strip()
    if category not in VALID_CATEGORIES:
        raise ValueError(f"'{category}' is not a valid category.")
    origin = origin.lower().strip()
    if origin not in VALID_ORIGINS:
        raise ValueError(f"'{origin}' is not a valid origin.")
    row = {"amount": f"{amount:.2f}", "category": category, "note": note.strip(), "origin": origin}
    file_exists = os.path.exists(RECURRING_PATH)
    with open(RECURRING_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RECURRING_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return row


def delete_recurring(index: int) -> None:
    """Remove a recurring expense by its list position."""
    rows = load_recurring()
    if index < 0 or index >= len(rows):
        raise IndexError(f"No recurring expense at index {index}.")
    rows.pop(index)
    with open(RECURRING_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=RECURRING_COLUMNS)
        writer.writeheader()
        writer.writerows(rows)


WISHLIST_PATH = os.path.join(os.path.dirname(__file__), "wishlist.csv")
WISHLIST_COLUMNS = ["name", "type", "priority", "price", "note", "link", "purchased", "added_date"]

VALID_WISH_TYPES = ["utility", "games", "clothes"]
VALID_WISH_PRIORITIES = ["urgent", "really want", "want", "eventually"]


def load_wishlist() -> list[dict]:
    """Return all wishlist items, or an empty list if none saved yet."""
    if not os.path.exists(WISHLIST_PATH):
        return []
    with open(WISHLIST_PATH, "r", newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        row.setdefault("link", "")
        row.setdefault("purchased", "0")
        row.setdefault("added_date", "")
    return rows


def add_wish(name: str, wish_type: str, priority: str, price: float, note: str = "", link: str = "") -> dict:
    """Append a wishlist item to wishlist.csv."""
    if price < 0:
        raise ValueError("Price cannot be negative.")
    wish_type = wish_type.lower().strip()
    if wish_type not in VALID_WISH_TYPES:
        raise ValueError(f"'{wish_type}' is not a valid type.")
    priority = priority.lower().strip()
    if priority not in VALID_WISH_PRIORITIES:
        raise ValueError(f"'{priority}' is not a valid priority.")
    row = {
        "name": name.strip(),
        "type": wish_type,
        "priority": priority,
        "price": f"{price:.2f}",
        "note": note.strip(),
        "link": link.strip(),
        "purchased": "0",
        "added_date": date.today().isoformat(),
    }
    file_exists = os.path.exists(WISHLIST_PATH)
    with open(WISHLIST_PATH, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=WISHLIST_COLUMNS)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)
    return row


def toggle_wish_purchased(index: int) -> None:
    """Flip the purchased flag on a wishlist item."""
    items = load_wishlist()
    if index < 0 or index >= len(items):
        raise IndexError(f"No wishlist item at index {index}.")
    items[index]["purchased"] = "0" if items[index]["purchased"] == "1" else "1"
    with open(WISHLIST_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=WISHLIST_COLUMNS)
        writer.writeheader()
        writer.writerows(items)


def delete_wish(index: int) -> None:
    """Remove a wishlist item by its list position."""
    items = load_wishlist()
    if index < 0 or index >= len(items):
        raise IndexError(f"No wishlist item at index {index}.")
    items.pop(index)
    with open(WISHLIST_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=WISHLIST_COLUMNS)
        writer.writeheader()
        writer.writerows(items)


def summarise_by_category(expenses: list[dict]) -> dict[str, float]:
    """
    Given a list of expense dicts, return total spending per category.
    Example return value: {"food": 120.50, "transport": 45.00}
    """
    totals = {}
    for expense in expenses:
        category = expense["category"]
        amount = float(expense["amount"])
        # dict.get(key, default) returns 0.0 if the category isn't in totals yet
        totals[category] = totals.get(category, 0.0) + amount
    return totals

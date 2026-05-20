"""
log.py — Quick one-liner CLI for logging an expense.

Usage:
    python3 log.py <amount> <category> [--credit] [note words...]

Examples:
    python3 log.py 25 food energy drink
    python3 log.py 12.50 transport metro card
    python3 log.py 9.99 subscriptions spotify --credit

Pass --credit anywhere after the category to log as a credit card expense.
Default origin is debit.
"""

import sys
from tracker import add_expense, VALID_CATEGORIES, VALID_ORIGINS


def main():
    args = sys.argv[1:]

    if len(args) < 2:
        print("Usage: python3 log.py <amount> <category> [--credit] [note...]")
        print(f"Categories: {', '.join(VALID_CATEGORIES)}")
        sys.exit(1)

    try:
        amount = float(args[0])
    except ValueError:
        print(f"Error: '{args[0]}' is not a valid amount. Use a number like 25 or 12.50")
        sys.exit(1)

    category = args[1]

    # Check for --credit flag anywhere in the remaining args, then remove it.
    remaining = args[2:]
    if "--credit" in remaining:
        origin = "credit"
        remaining = [a for a in remaining if a != "--credit"]
    else:
        origin = "debit"

    note = " ".join(remaining)

    try:
        expense = add_expense(amount, category, note, origin=origin)
        print(f"Logged: R${expense['amount']} — {expense['category']} [{expense['origin']}] — {expense['note'] or '(no note)'} [{expense['date']}]")
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

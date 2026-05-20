"""
monthly_report.py — Print a spending summary and show a bar chart for one month.

Usage:
    python3 monthly_report.py           # defaults to the current month
    python3 monthly_report.py 2026 3    # March 2026

Requires: pip install matplotlib
"""

import sys
from datetime import date
from tracker import get_monthly_expenses, summarise_by_category


def print_summary(year: int, month: int, totals: dict[str, float], grand_total: float):
    """Print a simple text table of spending by category."""
    month_name = date(year, month, 1).strftime("%B %Y")  # e.g. "May 2026"
    print(f"\n{'=' * 36}")
    print(f"  Monthly Report — {month_name}")
    print(f"{'=' * 36}")

    if not totals:
        print("  No expenses recorded this month.")
        print(f"{'=' * 36}\n")
        return

    # Sort categories by amount (highest first) so the biggest expenses stand out.
    for category, amount in sorted(totals.items(), key=lambda x: x[1], reverse=True):
        # ljust(12) pads the category name so columns line up neatly.
        print(f"  {category.ljust(12)}  R${amount:>8.2f}")

    print(f"{'─' * 36}")
    print(f"  {'TOTAL'.ljust(12)}  R${grand_total:>8.2f}")
    print(f"{'=' * 36}\n")


def show_chart(year: int, month: int, totals: dict[str, float]):
    """Display a horizontal bar chart of spending by category."""
    # matplotlib is only imported here so the script still runs (for the text
    # summary) even if matplotlib isn't installed — the error is caught below.
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("Chart skipped — install matplotlib with: pip install matplotlib")
        return

    if not totals:
        return

    month_name = date(year, month, 1).strftime("%B %Y")

    # Sort so the longest bar is at the top.
    categories = list(totals.keys())
    amounts = list(totals.values())
    pairs = sorted(zip(amounts, categories), reverse=True)
    amounts, categories = zip(*pairs)

    fig, ax = plt.subplots(figsize=(8, max(3, len(categories) * 0.6)))

    bars = ax.barh(categories, amounts, color="#4C72B0", edgecolor="white")

    # Add the euro amount at the end of each bar.
    for bar, amount in zip(bars, amounts):
        ax.text(
            bar.get_width() + max(amounts) * 0.01,   # a little to the right of the bar
            bar.get_y() + bar.get_height() / 2,
            f"R${amount:.2f}",
            va="center",
            fontsize=10,
        )

    ax.set_xlabel("Amount (R$)")
    ax.set_title(f"Spending by Category — {month_name}")
    ax.invert_yaxis()  # highest bar at the top
    plt.tight_layout()
    plt.show()


def main():
    # Read optional year/month arguments, defaulting to today.
    today = date.today()

    if len(sys.argv) == 3:
        try:
            year = int(sys.argv[1])
            month = int(sys.argv[2])
            if not (1 <= month <= 12):
                raise ValueError
        except ValueError:
            print("Usage: python3 monthly_report.py [year month]")
            print("Example: python3 monthly_report.py 2026 3")
            sys.exit(1)
    elif len(sys.argv) == 1:
        year, month = today.year, today.month
    else:
        print("Usage: python3 monthly_report.py [year month]")
        sys.exit(1)

    expenses = get_monthly_expenses(year, month)
    totals = summarise_by_category(expenses)
    grand_total = sum(totals.values())

    print_summary(year, month, totals, grand_total)
    show_chart(year, month, totals)


if __name__ == "__main__":
    main()

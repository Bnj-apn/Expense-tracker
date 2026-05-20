# C.R.E.A.M — Expense Tracker

Personal expense tracker built in Python. Goal: understand where money goes and spend less.

## Project structure

```
C.R.E.A,M/
├── expenses.csv          # all expense data (auto-created on first log)
├── tracker.py            # core logic — shared by all scripts and the web app
├── log.py                # quick CLI logger
├── monthly_report.py     # text summary + bar chart for one month (terminal)
├── app.py                # Flask web app
├── templates/
│   ├── base.html         # shared layout and sidebar nav
│   ├── index.html        # dashboard: log form + recent expenses
│   ├── history.html      # full expense list with delete buttons
│   └── report.html       # monthly summary table + Chart.js bar chart
└── CLAUDE.md             # this file
```

## How the files relate

```
log.py  ──►  tracker.py  ──►  expenses.csv
app.py  ──►      ▲
monthly_report.py
```

`tracker.py` is the only file that reads and writes `expenses.csv`. All other scripts import its functions — so adding a new interface (CLI, web, anything) never requires touching the core logic.

## expenses.csv format

```
date,amount,category,note
2026-05-19,25.00,food,energy drink
2026-05-19,12.50,transport,metro card
```

- `date` — ISO format: YYYY-MM-DD
- `amount` — always two decimal places
- `category` — one of the valid categories (see below)
- `note` — optional free-text description

## Valid categories

`food`, `grocery`, `transport`, `subscriptions`, `extras`

## Usage

### Web app (recommended)
```bash
python3 app.py
# then open http://127.0.0.1:8080
```

### Log an expense via CLI
```bash
python3 log.py <amount> <category> [note...]

python3 log.py 25 food energy drink
python3 log.py 12.50 transport metro card
python3 log.py 9.99 subscriptions spotify
```

### Monthly report (terminal)
```bash
python3 monthly_report.py           # current month
python3 monthly_report.py 2026 3    # March 2026
```

## Dependencies

- **Python 3.10+** (uses `list[dict]` type hints)
- **Flask** — required for the web app: `pip install flask`
- **matplotlib** — only needed for the terminal chart: `pip install matplotlib`

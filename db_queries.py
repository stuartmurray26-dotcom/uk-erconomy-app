"""Query helpers for the UK Economy Explorer."""
from models import get_db


# ── bank rates ────────────────────────────────────────────────────────────────

def count_bank_rates(db=None):
    c = db or get_db()
    return c.execute("SELECT COUNT(*) FROM bank_rate").fetchone()[0]


def get_latest_bank_rate(db=None):
    c = db or get_db()
    return c.execute(
        "SELECT * FROM bank_rate ORDER BY date_changed DESC LIMIT 1"
    ).fetchone()


def get_bank_rates_page(page, per_page, year=None, db=None):
    c = db or get_db()
    offset = (page - 1) * per_page
    if year:
        total = c.execute(
            "SELECT COUNT(*) FROM bank_rate WHERE strftime('%Y', date_changed) = ?",
            (str(year),)
        ).fetchone()[0]
        rows = c.execute(
            "SELECT * FROM bank_rate WHERE strftime('%Y', date_changed) = ? "
            "ORDER BY date_changed DESC LIMIT ? OFFSET ?",
            (str(year), per_page, offset)
        ).fetchall()
    else:
        total = c.execute("SELECT COUNT(*) FROM bank_rate").fetchone()[0]
        rows = c.execute(
            "SELECT * FROM bank_rate ORDER BY date_changed DESC LIMIT ? OFFSET ?",
            (per_page, offset)
        ).fetchall()
    return rows, total


def get_bank_rate_years(db=None):
    c = db or get_db()
    rows = c.execute(
        "SELECT DISTINCT strftime('%Y', date_changed) AS yr "
        "FROM bank_rate ORDER BY yr DESC"
    ).fetchall()
    return [int(r["yr"]) for r in rows]


def get_bank_rate_by_id(record_id, db=None):
    c = db or get_db()
    return c.execute("SELECT * FROM bank_rate WHERE id = ?", (record_id,)).fetchone()


def get_prev_bank_rate(date_str, db=None):
    c = db or get_db()
    return c.execute(
        "SELECT * FROM bank_rate WHERE date_changed < ? ORDER BY date_changed DESC LIMIT 1",
        (date_str,)
    ).fetchone()


def get_next_bank_rate(date_str, db=None):
    c = db or get_db()
    return c.execute(
        "SELECT * FROM bank_rate WHERE date_changed > ? ORDER BY date_changed ASC LIMIT 1",
        (date_str,)
    ).fetchone()


def get_all_bank_rates(db=None):
    c = db or get_db()
    return c.execute("SELECT * FROM bank_rate ORDER BY date_changed DESC").fetchall()


def get_bank_rates_for_year(year, db=None):
    c = db or get_db()
    return c.execute(
        "SELECT * FROM bank_rate WHERE strftime('%Y', date_changed) = ? "
        "ORDER BY date_changed ASC",
        (str(year),)
    ).fetchall()


def get_rate_in_force_at_year_end(year, db=None):
    """Return the rate in force at 31 Dec of the given year."""
    c = db or get_db()
    return c.execute(
        "SELECT * FROM bank_rate WHERE date_changed <= ? ORDER BY date_changed DESC LIMIT 1",
        (f"{year}-12-31",)
    ).fetchone()


def year_avg_bank_rate(year, db=None):
    """Approximate average bank rate for a year."""
    c = db or get_db()
    rows = get_bank_rates_for_year(year, db=c)
    if rows:
        return round(sum(r["rate"] for r in rows) / len(rows), 2)
    row = get_rate_in_force_at_year_end(year, db=c)
    return row["rate"] if row else None


# ── inflation ─────────────────────────────────────────────────────────────────

def count_inflation(db=None):
    c = db or get_db()
    return c.execute("SELECT COUNT(*) FROM inflation").fetchone()[0]


def get_latest_inflation(db=None):
    c = db or get_db()
    return c.execute("SELECT * FROM inflation ORDER BY year DESC LIMIT 1").fetchone()


def get_all_inflation(db=None):
    c = db or get_db()
    return c.execute("SELECT * FROM inflation ORDER BY year DESC").fetchall()


def get_inflation_by_year(year, db=None):
    c = db or get_db()
    return c.execute("SELECT * FROM inflation WHERE year = ?", (year,)).fetchone()

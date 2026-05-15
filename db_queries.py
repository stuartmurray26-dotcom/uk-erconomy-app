"""Query helpers for the UK Economy Explorer (SQLAlchemy version)."""

from models import db, BankRate, Inflation
from sqlalchemy import extract, func


# ── bank rates ────────────────────────────────────────────────────────────────

def count_bank_rates():
    return db.session.query(func.count(BankRate.id)).scalar()


def get_latest_bank_rate():
    return BankRate.query.order_by(BankRate.date_changed.desc()).first()


def get_bank_rates_page(page, per_page, year=None):
    query = BankRate.query

    if year:
        query = query.filter(extract('year', func.date(BankRate.date_changed)) == year)

    total = query.count()
    rows = query.order_by(BankRate.date_changed.desc()) \
                .offset((page - 1) * per_page) \
                .limit(per_page) \
                .all()

    return rows, total


def get_bank_rate_years():
    years = (
        db.session.query(extract('year', func.date(BankRate.date_changed)).label("yr"))
        .distinct()
        .order_by(func.date(BankRate.date_changed).desc())
        .all()
    )
    return [int(y.yr) for y in years]


def get_bank_rate_by_id(record_id):
    return BankRate.query.get(record_id)


def get_prev_bank_rate(date_str):
    return (
        BankRate.query
        .filter(BankRate.date_changed < date_str)
        .order_by(BankRate.date_changed.desc())
        .first()
    )


def get_next_bank_rate(date_str):
    return (
        BankRate.query
        .filter(BankRate.date_changed > date_str)
        .order_by(BankRate.date_changed.asc())
        .first()
    )


def get_all_bank_rates():
    return BankRate.query.order_by(BankRate.date_changed.desc()).all()


def get_bank_rates_for_year(year):
    return (
        BankRate.query
        .filter(extract('year', func.date(BankRate.date_changed)) == year)
        .order_by(BankRate.date_changed.asc())
        .all()
    )


def get_rate_in_force_at_year_end(year):
    return (
        BankRate.query
        .filter(BankRate.date_changed <= f"{year}-12-31")
        .order_by(BankRate.date_changed.desc())
        .first()
    )


def year_avg_bank_rate(year):
    rows = get_bank_rates_for_year(year)
    if rows:
        return round(sum(r.rate for r in rows) / len(rows), 2)

    row = get_rate_in_force_at_year_end(year)
    return row.rate if row else None


# ── inflation ─────────────────────────────────────────────────────────────────

def count_inflation():
    return db.session.query(func.count(Inflation.id)).scalar()


def get_latest_inflation():
    return Inflation.query.order_by(Inflation.year.desc()).first()


def get_all_inflation():
    return Inflation.query.order_by(Inflation.year.desc()).all()


def get_inflation_by_year(year):
    return Inflation.query.filter_by(year=year).first()

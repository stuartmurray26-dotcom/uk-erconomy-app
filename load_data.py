"""Seed the database from CSV data files."""
import csv
import os
from datetime import datetime

from models import db, BankRate, Inflation

BANK_RATE_FILE = os.path.join(os.path.dirname(__file__), "data", "bank_rate.csv")
INFLATION_FILE = os.path.join(os.path.dirname(__file__), "data", "inflation.csv")


def load_bank_rate():
    loaded = skipped = 0

    with open(BANK_RATE_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                date_obj = datetime.strptime(row["date_changed"].strip(), "%d %b %y").date()
                rate = float(row["rate"].strip())
            except (ValueError, KeyError):
                skipped += 1
                continue

            # Check if exists
            existing = BankRate.query.filter_by(date_changed=date_obj.isoformat()).first()
            if existing:
                skipped += 1
                continue

            entry = BankRate(
                date_changed=date_obj.isoformat(),
                rate=rate
            )
            db.session.add(entry)
            loaded += 1

    db.session.commit()
    print(f"  Bank rates: {loaded} loaded, {skipped} skipped.")
    return loaded


def load_inflation():
    loaded = skipped = 0

    with open(INFLATION_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            try:
                year = int(str(row["year"]).strip().strip('"'))
                rate = float(str(row["rate"]).strip().strip('"'))
            except (ValueError, KeyError):
                skipped += 1
                continue

            existing = Inflation.query.filter_by(year=year).first()
            if existing:
                skipped += 1
                continue

            entry = Inflation(year=year, rate=rate)
            db.session.add(entry)
            loaded += 1

    db.session.commit()
    print(f"  Inflation: {loaded} loaded, {skipped} skipped.")
    return loaded


def seed_all():
    print("Seeding Bank Rate data ...")
    br = load_bank_rate()

    print("Seeding Inflation data ...")
    inf = load_inflation()

    print(f"Done. Total: {br + inf}")

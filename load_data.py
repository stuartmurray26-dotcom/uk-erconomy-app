"""Seed the database from CSV data files."""
import csv
import os
from datetime import datetime

from models import get_db, init_db

BANK_RATE_FILE = os.path.join(os.path.dirname(__file__), "data", "bank_rate.csv")
INFLATION_FILE = os.path.join(os.path.dirname(__file__), "data", "inflation.csv")


def load_bank_rates(conn=None):
    c = conn or get_db()
    loaded = skipped = 0
    with open(BANK_RATE_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                date_obj = datetime.strptime(row["date_changed"].strip(), "%d %b %y").date()
                rate = float(row["rate"].strip())
            except (ValueError, KeyError) as exc:
                skipped += 1
                continue
            date_str = date_obj.isoformat()
            c.execute(
                "INSERT OR IGNORE INTO bank_rate (date_changed, rate) VALUES (?, ?)",
                (date_str, rate),
            )
            loaded += 1
    c.commit()
    print(f"  Bank rates: {loaded} loaded, {skipped} skipped.")
    return loaded


def load_inflation(conn=None):
    c = conn or get_db()
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
            c.execute(
                "INSERT OR IGNORE INTO inflation (year, rate) VALUES (?, ?)",
                (year, rate),
            )
            loaded += 1
    c.commit()
    print(f"  Inflation: {loaded} loaded, {skipped} skipped.")
    return loaded


def seed_all(conn=None):
    init_db()
    c = conn or get_db()
    print("Seeding Bank Rate data ...")
    br = load_bank_rates(conn=c)
    print("Seeding Inflation data ...")
    inf = load_inflation(conn=c)
    print(f"Done. Total: {br + inf}")

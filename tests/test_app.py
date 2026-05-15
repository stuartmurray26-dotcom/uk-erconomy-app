"""Tests for UK Economy Explorer – uses only stdlib + Flask (no pytest required)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import sqlite3
import tempfile
import unittest
from datetime import date

import models  # so we can patch DB_PATH

def _make_test_db():
    """Create a temp SQLite DB with minimal seed data; return (path, conn)."""
    tf = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    path = tf.name
    tf.close()
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE bank_rate (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        date_changed TEXT NOT NULL UNIQUE,
        rate REAL NOT NULL)""")
    conn.execute("""CREATE TABLE inflation (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        year INTEGER NOT NULL UNIQUE,
        rate REAL NOT NULL)""")
    rows_br = [
        ("2023-08-03", 5.25),
        ("2023-06-22", 5.00),
        ("2022-12-15", 3.50),
        ("2009-03-05", 0.50),
    ]
    conn.executemany("INSERT INTO bank_rate (date_changed, rate) VALUES (?,?)", rows_br)
    rows_inf = [(2023, 6.8), (2022, 7.9), (2009, 2.0)]
    conn.executemany("INSERT INTO inflation (year, rate) VALUES (?,?)", rows_inf)
    conn.commit()
    return path, conn


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.db_path, self.db_conn = _make_test_db()
        # Patch the module-level DB_PATH used by models.get_db
        models.DB_PATH = self.db_path
        from app import create_app
        self.flask_app = create_app({"TESTING": True, "DB_PATH": self.db_path})
        self.client = self.flask_app.test_client()

    def tearDown(self):
        self.db_conn.close()
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def get(self, path):
        return self.client.get(path)


# ── Home ──────────────────────────────────────────────────────────────────────
class TestIndex(BaseTestCase):
    def test_returns_200(self):
        r = self.get("/")
        self.assertEqual(r.status_code, 200)

    def test_shows_latest_rate(self):
        r = self.get("/")
        self.assertIn(b"5.25", r.data)

    def test_shows_latest_inflation(self):
        r = self.get("/")
        self.assertIn(b"6.8", r.data)


# ── Bank rate list ─────────────────────────────────────────────────────────────
class TestBankRateList(BaseTestCase):
    def test_returns_200(self):
        self.assertEqual(self.get("/bank-rates").status_code, 200)

    def test_shows_rate(self):
        r = self.get("/bank-rates")
        self.assertIn(b"5.25", r.data)

    def test_filter_by_year(self):
        r = self.get("/bank-rates?year=2023")
        self.assertEqual(r.status_code, 200)
        self.assertIn(b"5.25", r.data)

    def test_filter_no_results(self):
        r = self.get("/bank-rates?year=1800")
        self.assertIn(b"No records found", r.data)

    def test_pagination_page_1(self):
        r = self.get("/bank-rates?page=1")
        self.assertEqual(r.status_code, 200)


# ── Bank rate detail ──────────────────────────────────────────────────────────
class TestBankRateDetail(BaseTestCase):
    def _first_id(self):
        row = self.db_conn.execute("SELECT id FROM bank_rate ORDER BY date_changed DESC LIMIT 1").fetchone()
        return row["id"]

    def test_returns_200(self):
        self.assertEqual(self.get(f"/bank-rates/{self._first_id()}").status_code, 200)

    def test_shows_rate(self):
        r = self.get(f"/bank-rates/{self._first_id()}")
        self.assertIn(b"5.25", r.data)

    def test_shows_inflation_context(self):
        r = self.get(f"/bank-rates/{self._first_id()}")
        self.assertIn(b"6.8", r.data)

    def test_404_for_missing(self):
        self.assertEqual(self.get("/bank-rates/99999").status_code, 404)


# ── Inflation list ────────────────────────────────────────────────────────────
class TestInflationList(BaseTestCase):
    def test_returns_200(self):
        self.assertEqual(self.get("/inflation").status_code, 200)

    def test_shows_years(self):
        r = self.get("/inflation")
        self.assertIn(b"2023", r.data)
        self.assertIn(b"2022", r.data)


# ── Inflation detail ──────────────────────────────────────────────────────────
class TestInflationDetail(BaseTestCase):
    def test_returns_200(self):
        self.assertEqual(self.get("/inflation/2023").status_code, 200)

    def test_404_for_missing(self):
        self.assertEqual(self.get("/inflation/1800").status_code, 404)

    def test_shows_bank_rate_changes(self):
        r = self.get("/inflation/2023")
        self.assertTrue(b"5.25" in r.data or b"5.0" in r.data)

    def test_shows_real_rate(self):
        r = self.get("/inflation/2023")
        self.assertIn(b"Real rate", r.data)


# ── Compare ───────────────────────────────────────────────────────────────────
class TestCompare(BaseTestCase):
    def test_returns_200(self):
        self.assertEqual(self.get("/compare").status_code, 200)

    def test_shows_real_rate_column(self):
        r = self.get("/compare")
        self.assertIn(b"Real Rate", r.data)

    def test_shows_years(self):
        r = self.get("/compare")
        self.assertIn(b"2022", r.data)


# ── API endpoints ─────────────────────────────────────────────────────────────
class TestAPI(BaseTestCase):
    def test_bank_rate_json(self):
        import json
        r = self.get("/api/bank-rates")
        self.assertEqual(r.status_code, 200)
        data = json.loads(r.data)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 4)
        self.assertIn("rate", data[0])
        self.assertIn("date_changed", data[0])

    def test_inflation_json(self):
        import json
        r = self.get("/api/inflation")
        data = json.loads(r.data)
        self.assertEqual(len(data), 3)
        self.assertIn("year", data[0])

    def test_compare_json(self):
        import json
        r = self.get("/api/compare")
        data = json.loads(r.data)
        self.assertIsInstance(data, list)
        for row in data:
            self.assertIn("year", row)
            self.assertIn("inflation", row)
            self.assertIn("bank_rate", row)


# ── Error handlers ────────────────────────────────────────────────────────────
class TestErrors(BaseTestCase):
    def test_404_custom_page(self):
        r = self.get("/this-does-not-exist")
        self.assertEqual(r.status_code, 404)
        self.assertIn(b"404", r.data)


# ── DB / load_data layer ──────────────────────────────────────────────────────
class TestLoadData(BaseTestCase):
    def test_bank_rate_count(self):
        count = self.db_conn.execute("SELECT COUNT(*) FROM bank_rate").fetchone()[0]
        self.assertEqual(count, 4)

    def test_inflation_count(self):
        count = self.db_conn.execute("SELECT COUNT(*) FROM inflation").fetchone()[0]
        self.assertEqual(count, 3)

    def test_no_duplicate_dates(self):
        # Insert a duplicate; OR IGNORE should silently skip
        self.db_conn.execute(
            "INSERT OR IGNORE INTO bank_rate (date_changed, rate) VALUES (?,?)",
            ("2023-08-03", 99.0),
        )
        self.db_conn.commit()
        row = self.db_conn.execute(
            "SELECT rate FROM bank_rate WHERE date_changed = '2023-08-03'"
        ).fetchone()
        self.assertEqual(row["rate"], 5.25)  # original value preserved


# ── DB queries ────────────────────────────────────────────────────────────────
class TestDBQueries(BaseTestCase):
    def test_year_avg_bank_rate_with_changes(self):
        from db_queries import year_avg_bank_rate
        avg = year_avg_bank_rate(2023, db=self.db_conn)
        # Two 2023 changes: 5.25 and 5.00 → avg 5.125
        self.assertAlmostEqual(avg, 5.125, places=2)

    def test_year_avg_bank_rate_fallback(self):
        from db_queries import year_avg_bank_rate
        # 2010: no changes that year; should fall back to rate in force
        avg = year_avg_bank_rate(2010, db=self.db_conn)
        self.assertEqual(avg, 0.50)  # 2009 cut still in force

    def test_get_prev_bank_rate(self):
        from db_queries import get_prev_bank_rate
        prev = get_prev_bank_rate("2023-08-03", db=self.db_conn)
        self.assertEqual(prev["date_changed"], "2023-06-22")

    def test_get_next_bank_rate(self):
        from db_queries import get_next_bank_rate
        nxt = get_next_bank_rate("2023-06-22", db=self.db_conn)
        self.assertEqual(nxt["date_changed"], "2023-08-03")

    def test_count_bank_rate(self):
        from db_queries import count_bank_rate
        self.assertEqual(count_bank_rate(db=self.db_conn), 4)

    def test_count_inflation(self):
        from db_queries import count_inflation
        self.assertEqual(count_inflation(db=self.db_conn), 3)


if __name__ == "__main__":
    unittest.main(verbosity=2)
# tests

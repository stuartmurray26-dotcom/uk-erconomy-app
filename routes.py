"""Flask blueprints / route handlers (SQLAlchemy + PostgreSQL version)."""
import math
from flask import Blueprint, abort, jsonify, render_template, request
from db_queries import (
    count_bank_rate, count_inflation, get_latest_bank_rate, get_latest_inflation,
    get_bank_rate_page, get_bank_rate_years, get_bank_rate_by_id,
    get_prev_bank_rate, get_next_bank_rate, get_all_bank_rate,
    get_bank_rate_for_year, year_avg_bank_rate,
    get_all_inflation, get_inflation_by_year,
)

main = Blueprint("main", __name__)

PER_PAGE = 25


# ── index ──────────────────────────────────────────────────────────────────────
@main.route("/")
def index():
    return render_template(
        "index.html",
        total_br=count_bank_rate(),
        total_inf=count_inflation(),
        latest_br=get_latest_bank_rate(),
        latest_inf=get_latest_inflation(),
    )


# ── bank rates ─────────────────────────────────────────────────────────────────
@main.route("/bank-rate")
def bank_rate():
    page = request.args.get("page", 1, type=int)
    year = request.args.get("year", type=int)

    records, total = get_bank_rate_page(page, PER_PAGE, year=year)
    total_pages = max(1, math.ceil(total / PER_PAGE))
    years = get_bank_rate_years()

    return render_template(
        "bank_rate.html",
        records=records,
        page=page,
        total=total,
        total_pages=total_pages,
        years=years,
        selected_year=year,
    )


@main.route("/bank-rates/<int:record_id>")
def bank_rate_detail(record_id):
    record = get_bank_rate_by_id(record_id)
    if not record:
        abort(404)

    prev_rate = get_prev_bank_rate(record.date_changed)
    next_rate = get_next_bank_rate(record.date_changed)

    change = None
    if prev_rate:
        change = round(record.rate - prev_rate.rate, 2)

    year = int(record.date_changed[:4])
    inflation = get_inflation_by_year(year)

    all_rates = [r.rate for r in get_all_bank_rate()]
    avg_rate = round(sum(all_rates) / len(all_rates), 2) if all_rates else None
    rank = sum(1 for r in all_rates if r > record.rate) + 1

    return render_template(
        "bank_rate_detail.html",
        record=record,
        prev_rate=prev_rate,
        next_rate=next_rate,
        change=change,
        inflation=inflation,
        avg_rate=avg_rate,
        rank=rank,
        total=len(all_rates),
    )


# ── inflation ──────────────────────────────────────────────────────────────────
@main.route("/inflation")
def inflation_list():
    records = get_all_inflation()
    avg = round(sum(r.rate for r in records) / len(records), 2) if records else 0
    return render_template("inflation.html", records=records, avg=avg)


@main.route("/inflation/<int:year>")
def inflation_detail(year):
    record = get_inflation_by_year(year)
    if not record:
        abort(404)

    all_records = get_all_inflation()
    avg = round(sum(r.rate for r in all_records) / len(all_records), 2)

    sorted_by_rate = sorted(all_records, key=lambda r: r.rate, reverse=True)
    rank = next((i + 1 for i, r in enumerate(sorted_by_rate) if r.year == year), None)

    br_changes = get_bank_rate_for_year(year)
    avg_br = year_avg_bank_rate(year)

    return render_template(
        "inflation_detail.html",
        record=record,
        avg=avg,
        rank=rank,
        total=len(all_records),
        br_changes=br_changes,
        avg_br=avg_br,
    )


# ── compare ────────────────────────────────────────────────────────────────────
@main.route("/compare")
def compare():
    inf_records = list(reversed(get_all_inflation()))  # oldest first
    data = []

    for inf in inf_records:
        avg_br = year_avg_bank_rate(inf.year)
        data.append({
            "year": inf.year,
            "inflation": inf.rate,
            "bank_rate": avg_br,
            "real_rate": round((avg_br or 0) - inf.rate, 2),
        })

    return render_template("compare.html", data=data)


# ── API ────────────────────────────────────────────────────────────────────────
@main.route("/api/bank-rates")
def api_bank_rate():
    records = get_all_bank_rate()
    return jsonify([
        {
            "id": r.id,
            "date_changed": r.date_changed,
            "rate": r.rate
        }
        for r in records
    ])


@main.route("/api/inflation")
def api_inflation():
    records = list(reversed(get_all_inflation()))
    return jsonify([
        {
            "id": r.id,
            "year": r.year,
            "rate": r.rate
        }
        for r in records
    ])


@main.route("/api/compare")
def api_compare():
    inf_records = list(reversed(get_all_inflation()))
    out = []

    for inf in inf_records:
        out.append({
            "year": inf.year,
            "inflation": inf.rate,
            "bank_rate": year_avg_bank_rate(inf.year),
        })

    return jsonify(out)


# ── error handlers ─────────────────────────────────────────────────────────────
@main.app_errorhandler(404)
def not_found(e):
    return render_template("error.html", code=404, message="Page not found."), 404


@main.app_errorhandler(500)
def server_error(e):
    return render_template("error.html", code=500, message="Internal server error."), 500

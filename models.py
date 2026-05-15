from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

class BankRate(db.Model):
    __tablename__ = "bank_rate"

    id = db.Column(db.Integer, primary_key=True)
    date_changed = db.Column(db.String, unique=True, nullable=False)
    rate = db.Column(db.Float, nullable=False)

class Inflation(db.Model):
    __tablename__ = "inflation"

    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, unique=True, nullable=False)
    rate = db.Column(db.Float, nullable=False)

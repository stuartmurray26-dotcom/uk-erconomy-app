"""UK Economy Explorer – Flask application factory."""
import os
from flask import Flask
from models import db
from routes import main

def create_app(config=None):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ["DATABASE_URL"]
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    with app.app_context():
        db.create_all()

    # Initialize SQLAlchemy
    db.init_app(app)

    if config:
        app.config.update(config)
        
    # Register routes
    app.register_blueprint(main)

    # Seed command
    @app.cli.command("seed")
    def seed_command():
        """Load open data into the database."""
        from load_data import seed_all
        seed_all()

    return app


if __name__ == "__main__":
    application = create_app()

    # Auto-seed on first run (SQLAlchemy version)
    with application.app_context():
        from models import BankRate
        from load_data import seed_all

        count = BankRate.query.count()
        if count == 0:
            print("Empty database – seeding now ...")
            seed_all()

    application.run(debug=True)

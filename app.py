"""UK Economy Explorer – Flask application factory."""
import os
from flask import Flask
from models import init_db
from routes import main


def create_app(config=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-in-prod")
    app.config["TESTING"] = False
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL")
    SQLALCHAMEY_TRACK_MODIFICATIONS = False

    if config:
        app.config.update(config)
        # Allow test to override DB path
        if "DB_PATH" in config:
            import models
            models.DB_PATH = config["DB_PATH"]

    app.register_blueprint(main)

    @app.cli.command("seed")
    def seed_command():
        """Load open data into the database."""
        from load_data import seed_all
        seed_all()

    return app


if __name__ == "__main__":
    application = create_app()
    init_db()
    # Auto-seed on first run if DB is empty
    from models import get_db
    db = get_db()
    count = db.execute("SELECT COUNT(*) FROM bank_rate").fetchone()[0]
    if count == 0:
        print("Empty database – seeding now ...")
        from load_data import seed_all
        seed_all(conn=db)
    application.run(debug=True)

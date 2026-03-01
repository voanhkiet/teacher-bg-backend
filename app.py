from dotenv import load_dotenv
load_dotenv()

from flask import Flask
from flask_cors import CORS
from config import Config
from extensions import db
from routes import register_routes
from admin import admin_bp
from flask_migrate import Migrate
import os


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret")

    CORS(app)

    db.init_app(app)
    migrate = Migrate(app, db)

    register_routes(app)
    app.register_blueprint(admin_bp)

    # =========================
    # AUTO CREATE DEFAULT ADMIN
    # =========================
    with app.app_context():
        from models import User

        admin_email = os.getenv("DEFAULT_ADMIN_EMAIL")
        admin_password = os.getenv("DEFAULT_ADMIN_PASSWORD")

        if admin_email and admin_password:
            existing_admin = User.query.filter_by(email=admin_email).first()

            if not existing_admin:
                admin = User(
                    email=admin_email,
                    is_admin=True
                )
                admin.set_password(admin_password)

                db.session.add(admin)
                db.session.commit()

                print("✅ Default admin created:", admin_email)
        else:
            print("⚠️ No DEFAULT_ADMIN_EMAIL or PASSWORD set")

        print("=== ROUTES ===")
        for rule in app.url_map.iter_rules():
            print(rule)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
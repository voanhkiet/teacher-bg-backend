import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///local.db"  # local dev fallback
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

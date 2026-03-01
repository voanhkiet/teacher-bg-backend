import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///teacher_bg.db"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
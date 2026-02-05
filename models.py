from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)
class Pack(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title_vi = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    price_vnd = db.Column(db.Integer, nullable=False)
    description_vi = db.Column(db.Text)
    description_en = db.Column(db.Text)
    cover_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pack_id = db.Column(db.Integer, db.ForeignKey("pack.id"))
    image_url = db.Column(db.String(255), nullable=False)
    preview_url = db.Column(db.String(255), nullable=False)

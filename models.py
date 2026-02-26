from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

# ---------------- USER ----------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)  # ✅ ADD THIS

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    owned_packs = db.relationship("Ownership", backref="user", lazy=True)

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


# ---------------- PACK ----------------

class Pack(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    title_vi = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=False)

    subject = db.Column(db.String(100), nullable=False)

    price_vnd = db.Column(db.Integer, nullable=False)  # 0 = free

    description_vi = db.Column(db.Text)
    description_en = db.Column(db.Text)

    cover_image = db.Column(db.String(255))

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship("Image", backref="pack", lazy=True)
    owners = db.relationship("Ownership", backref="pack", lazy=True)

    @property
    def is_free(self):
        return self.price_vnd == 0


# ---------------- IMAGE ----------------

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    pack_id = db.Column(
        db.Integer,
        db.ForeignKey("pack.id"),
        nullable=False
    )

    image_url = db.Column(db.String(255), nullable=False)
    preview_url = db.Column(db.String(255), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# ---------------- OWNERSHIP ----------------

class Ownership(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    pack_id = db.Column(
        db.Integer,
        db.ForeignKey("pack.id"),
        nullable=False
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint("user_id", "pack_id", name="unique_user_pack"),
    )
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    pack_id = db.Column(db.Integer, nullable=False)
    provider = db.Column(db.String(20))  # momo_manual
    amount_vnd = db.Column(db.Integer)
    status = db.Column(db.String(20), default="pending")
    note = db.Column(db.String(255))  # admin reason (optional)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


    # Phase 4.2 – audit fields
    processed_at = db.Column(db.DateTime)
    processed_by = db.Column(db.Integer)


# ---------------- ADMIN ACTION LOG ----------------

class AdminActionLog(db.Model):
    __tablename__ = "admin_action_log"

    id = db.Column(db.Integer, primary_key=True)

    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True   # ✅ MUST be True
    )

    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

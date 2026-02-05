from flask import Blueprint, request
from extensions import db
from models import User

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email and password required"}, 400

    if User.query.filter_by(email=email).first():
        return {"error": "Email already registered"}, 409

    user = User(email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return {"message": "User created successfully"}, 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"error": "Email and password required"}, 400

    user = User.query.filter_by(email=email).first()

    if not user or not user.check_password(password):
        return {"error": "Invalid credentials"}, 401

    return {
        "message": "Login successful",
        "user_id": user.id,
        "email": user.email,
    }, 200

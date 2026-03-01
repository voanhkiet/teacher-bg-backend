from flask import Blueprint, request, render_template, session, redirect
from extensions import db
from models import User
from utils.jwt import create_access_token
from utils.auth import login_required


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


from utils.jwt import create_access_token

@auth_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template("login.html", error="Email and password required")

        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return render_template("login.html", error="Invalid credentials")

        session["user_id"] = user.id
        session["user_email"] = user.email

        return redirect("/my-packs")

    return render_template("login.html")
    
@auth_bp.route("/me", methods=["GET"])
@login_required
def me():
    user = User.query.get(request.user_id)
    return {
        "id": user.id,
        "email": user.email,
        "created_at": user.created_at.isoformat(),
    }
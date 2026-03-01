from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory, abort
from models import Ownership, Pack
from extensions import db

root_bp = Blueprint("root", __name__)

@root_bp.route("/")
def index():
    return render_template("product.html")

@root_bp.route("/buy/<int:pack_id>")
def buy_page(pack_id):
    return render_template("buy.html", pack_id=pack_id)

@root_bp.route("/my-packs")
def my_packs():

    if "user_id" not in session:
        return redirect("/auth/login")

    user_id = session["user_id"]

    rows = (
        db.session.query(Ownership, Pack)
        .join(Pack, Pack.id == Ownership.pack_id)
        .filter(Ownership.user_id == user_id)
        .all()
    )

    packs = [
        {
            "id": pack.id,
            "title": pack.title_vi,
            "granted_at": o.created_at
        }
        for o, pack in rows
    ]

    return render_template("my_packs.html", packs=packs)
@root_bp.route("/download/<int:pack_id>")
def download_pack(pack_id):

    user_id = session.get("user_id")

    if not user_id:
        abort(401)

    ownership = Ownership.query.filter_by(
        user_id=user_id,
        pack_id=pack_id
    ).first()

    if not ownership:
        abort(403)

    return send_from_directory(
        "private_files",
        "modern-vol1.zip",
        as_attachment=True
    )
from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory, abort, send_file,request
from models import Ownership, Pack
from extensions import db
import os
from utils.auth import login_required, admin_required
from utils.storage import generate_download_url

root_bp = Blueprint("root", __name__)

@root_bp.route("/")
def index():
    packs = Pack.query.all()
    return render_template("product.html", packs=packs)

@root_bp.route("/buy/<int:pack_id>")
def buy_page(pack_id):
    return render_template("buy.html", pack_id=pack_id)

@root_bp.route("/my-packs")
def my_packs():

    if "user_id" not in session:
        return redirect(url_for("auth.login", next=request.path))

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
@login_required
def download_pack(pack_id):
    user_id = session.get("user_id")

    ownership = Ownership.query.filter_by(
        user_id=user_id,
        pack_id=pack_id
    ).first()

    if not ownership:
        return abort(403)

    pack = Pack.query.get_or_404(pack_id)

    if not pack.file_path:
        return abort(404)

    signed_url = generate_download_url(pack.file_path)

    return redirect(signed_url)

@root_bp.route("/pack/<int:pack_id>")
def pack_detail(pack_id):
    pack = Pack.query.get_or_404(pack_id)

    owned = False
    user_id = session.get("user_id")

    if user_id:
        ownership = Ownership.query.filter_by(
            user_id=user_id,
            pack_id=pack.id
        ).first()

        owned = ownership is not None

    return render_template(
        "pack_detail.html",
        pack=pack,
        owned=owned
    )
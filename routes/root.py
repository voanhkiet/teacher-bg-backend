from flask import Blueprint, render_template, session, redirect, url_for, send_from_directory, abort, send_file,request
from models import Ownership, Pack
from extensions import db
import os
from utils.auth import login_required, admin_required

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
def download_pack(pack_id):

    if "user_id" not in session:
        return redirect(url_for("auth.login", next=request.path))

    user_id = session["user_id"]

    ownership = Ownership.query.filter_by(
        user_id=user_id,
        pack_id=pack_id
    ).first()

    if not ownership:
        return abort(403)

    pack = Pack.query.get_or_404(pack_id)

    if not pack.file_path:
        return abort(404)

    base_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "protected_files")
    )

    safe_path = os.path.normpath(os.path.join(base_dir, pack.file_path))

    if not safe_path.startswith(base_dir):
        return abort(403)

    if not os.path.exists(safe_path):
        return abort(404)

    return send_file(
        safe_path,
        as_attachment=True,
        download_name=f"{pack.title_en}.zip"
    )
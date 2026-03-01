from flask import Blueprint, render_template, request, redirect
from models import Payment
from extensions import db
from datetime import datetime

buy_bp = Blueprint("buy", __name__)

@buy_bp.route("/buy/<int:pack_id>", methods=["GET", "POST"])
def buy_pack(pack_id):

    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        transfer_code = request.form.get("transfer_code")

        payment = Payment(
            user_id=None,
            pack_id=pack_id,
            amount_vnd=69000,
            status="pending",
            note=f"Name: {name}, Email: {email}, Code: {transfer_code}",
            created_at=datetime.utcnow()
        )

        db.session.add(payment)
        db.session.commit()

        return render_template("waiting.html")

    return render_template("buy.html", pack_id=pack_id)
from flask import Blueprint, request, jsonify
from extensions import db
from models import Pack, Payment, Ownership, User
from utils.auth import login_required, admin_required
from datetime import datetime

payments_bp = Blueprint("payments", __name__, url_prefix="/api/payments")

# ======================================================
# CREATE PAYMENT (USER)
# ======================================================
@payments_bp.route("/create", methods=["POST"])
@login_required
def create_payment():
    data = request.get_json() or {}
    pack_id = data.get("pack_id")
    provider = data.get("provider")

    if provider != "momo_manual":
        return {"error": "Only momo_manual supported"}, 400

    pack = Pack.query.get_or_404(pack_id)

    if pack.is_free:
        return {"error": "Pack is free"}, 400

    # already owned
    if Ownership.query.filter_by(
        user_id=request.user_id,
        pack_id=pack.id
    ).first():
        return {"error": "Already owned"}, 400

    # prevent duplicate pending payments
    pending = Payment.query.filter_by(
        user_id=request.user_id,
        pack_id=pack.id,
        status="pending"
    ).first()

    if pending:
        return {
            "error": "Pending payment already exists",
            "payment_id": pending.id
        }, 409

    payment = Payment(
        user_id=request.user_id,
        pack_id=pack.id,
        provider="momo_manual",
        amount_vnd=pack.price_vnd,
        status="pending"
    )

    db.session.add(payment)
    db.session.commit()

    return {
        "payment_id": payment.id,
        "status": "pending",
        "amount_vnd": payment.amount_vnd,
        "instructions": {
            "wallet": "MoMo",
            "phone": "0939742254",
            "content": f"PAY PACK {payment.id}",
            "note": "Transfer and wait for admin approval"
        }
    }, 201


# ======================================================
# LIST MY PAYMENTS (USER)
# ======================================================
@payments_bp.route("/me", methods=["GET"])
@login_required
def my_payments():
    payments = (
        Payment.query
        .filter_by(user_id=request.user_id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return jsonify([
        {
            "payment_id": p.id,
            "pack_id": p.pack_id,
            "status": p.status,
            "amount_vnd": p.amount_vnd,
            "note": p.note,
            "created_at": p.created_at.isoformat()
        }
        for p in payments
    ])


# ======================================================
# ADMIN: LIST ALL PAYMENTS
# ======================================================
@payments_bp.route("", methods=["GET"])
@admin_required
def list_payments():
    rows = (
        db.session.query(Payment, Pack, User)
        .join(Pack, Pack.id == Payment.pack_id)
        .join(User, User.id == Payment.user_id)
        .order_by(Payment.created_at.desc())
        .all()
    )

    return jsonify([
        {
            "payment_id": p.id,
            "user_email": u.email,
            "pack_id": pack.id,
            "pack_title": pack.title_vi,
            "amount_vnd": p.amount_vnd,
            "provider": p.provider,
            "status": p.status,
            "note": p.note,
            "created_at": p.created_at.isoformat(),
            "processed_by": p.processed_by,
            "processed_at": p.processed_at.isoformat() if p.processed_at else None
        }
        for p, pack, u in rows
    ])


# ======================================================
# ADMIN: PENDING PAYMENTS
# ======================================================
@payments_bp.route("/pending", methods=["GET"])
@admin_required
def pending_payments():
    rows = (
        db.session.query(Payment, Pack, User)
        .join(Pack, Pack.id == Payment.pack_id)
        .join(User, User.id == Payment.user_id)
        .filter(Payment.status == "pending")
        .order_by(Payment.created_at.asc())
        .all()
    )

    return jsonify([
        {
            "payment_id": p.id,
            "user_email": u.email,
            "pack_title": pack.title_vi,
            "amount_vnd": p.amount_vnd,
            "created_at": p.created_at.isoformat()
        }
        for p, pack, u in rows
    ])


# ======================================================
# APPROVE PAYMENT (ADMIN)
# ======================================================
@payments_bp.route("/<int:payment_id>/approve", methods=["POST"])
@admin_required
def approve_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)

    if payment.status != "pending":
        return {"error": "Payment already processed"}, 400

    with db.session.begin():
        payment.status = "approved"
        payment.processed_by = request.user_id
        payment.processed_at = datetime.utcnow()

        exists = Ownership.query.filter_by(
            user_id=payment.user_id,
            pack_id=payment.pack_id
        ).first()

        if not exists:
            db.session.add(
                Ownership(
                    user_id=payment.user_id,
                    pack_id=payment.pack_id
                )
            )

    return {
        "message": "Payment approved",
        "payment_id": payment.id
    }


# ======================================================
# REJECT PAYMENT (ADMIN)
# ======================================================
@payments_bp.route("/<int:payment_id>/reject", methods=["POST"])
@admin_required
def reject_payment(payment_id):
    data = request.get_json() or {}
    note = data.get("note")

    if not note:
        return {"error": "Rejection reason is required"}, 400

    payment = Payment.query.get_or_404(payment_id)

    if payment.status != "pending":
        return {"error": "Payment already processed"}, 400

    payment.status = "rejected"
    payment.note = note
    payment.processed_by = request.user_id
    payment.processed_at = datetime.utcnow()

    db.session.commit()

    return {
        "message": "Payment rejected",
        "payment_id": payment.id,
        "note": note
    }


# ======================================================
# REVOKE PAYMENT (ADMIN)
# ======================================================
@payments_bp.route("/<int:payment_id>/revoke", methods=["POST"])
@admin_required
def revoke_payment(payment_id):
    data = request.get_json() or {}
    note = data.get("note")

    if not note:
        return {"error": "Revoke reason required"}, 400

    payment = Payment.query.get_or_404(payment_id)

    if payment.status != "approved":
        return {"error": "Only approved payments can be revoked"}, 400

    with db.session.begin():
        payment.status = "revoked"
        payment.note = note
        payment.processed_by = request.user_id
        payment.processed_at = datetime.utcnow()

        Ownership.query.filter_by(
            user_id=payment.user_id,
            pack_id=payment.pack_id
        ).delete()

    return {
        "message": "Payment revoked",
        "payment_id": payment.id,
        "note": note
    }

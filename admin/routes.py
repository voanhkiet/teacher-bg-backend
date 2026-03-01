from flask import  request, jsonify, render_template, redirect, session, url_for
from datetime import datetime
from sqlalchemy import func

from extensions import db
from models import User, Pack, Payment, Ownership, AdminActionLog
from utils.auth import admin_required
from . import admin_bp 
from utils.admin_session import admin_session_required
from werkzeug.security import check_password_hash
from datetime import datetime, timedelta

MAX_FAILED_ATTEMPTS = 5
FAILED_WINDOW_MINUTES = 5
LOCK_MINUTES = 10
# =========================
# ADMIN DASHBOARD SUMMARY
# =========================
@admin_bp.route("/dashboard", methods=["GET"])
@admin_session_required
def dashboard():
    revenue = (
        db.session.query(func.sum(Payment.amount_vnd))
        .filter(Payment.status == "approved")
        .scalar()
        or 0
    )

    stats = {
        "users": User.query.count(),
        "packs": Pack.query.count(),
        "payments": {
            "total": Payment.query.count(),
            "pending": Payment.query.filter_by(status="pending").count(),
            "approved": Payment.query.filter_by(status="approved").count(),
            "rejected": Payment.query.filter_by(status="rejected").count(),
            "revoked": Payment.query.filter_by(status="revoked").count(),
        },
        "revenue_vnd": revenue
    }

    return render_template("dashboard.html", stats=stats)


# =========================
# ADMIN: LIST ALL PAYMENTS
# =========================
@admin_bp.route("/payments", methods=["GET"])
@admin_session_required
def admin_payments():
    # ---- query params ----
    status = request.args.get("status")
    email = request.args.get("email")
    sort = request.args.get("sort", "newest")
    page = int(request.args.get("page", 1))
    per_page = 10

    query = (
        db.session.query(Payment, Pack, User)
        .join(Pack, Pack.id == Payment.pack_id)
        .join(User, User.id == Payment.user_id)
    )

    # ---- filters ----
    if status:
        query = query.filter(Payment.status == status)

    if email:
        query = query.filter(User.email.ilike(f"%{email}%"))

    # ---- sorting ----
    if sort == "oldest":
        query = query.order_by(Payment.created_at.asc())
    elif sort == "amount":
        query = query.order_by(Payment.amount_vnd.desc())
    else:
        query = query.order_by(Payment.created_at.desc())

    total = query.count()

    rows = (
        query
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return render_template(
        "payments.html",
        payments=[
            {
                "payment_id": p.id,
                "user_email": u.email,
                "pack_title": pack.title_vi,
                "amount_vnd": p.amount_vnd,
                "status": p.status,
                "note": p.note,
            }
            for p, pack, u in rows
        ],
        page=page,
        total_pages=(total + per_page - 1) // per_page,
        filters={
            "status": status,
            "email": email,
            "sort": sort,
        }
    )



# =========================
# ADMIN: PENDING PAYMENTS
# =========================
@admin_bp.route("/payments/pending", methods=["GET"])
@admin_session_required
def pending_payments():
    rows = (
        db.session.query(Payment, User, Pack)
        .join(User, User.id == Payment.user_id)
        .join(Pack, Pack.id == Payment.pack_id)
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
        for p, u, pack in rows
    ])


# =========================
# ADMIN: PAYMENT DETAIL
# =========================
@admin_bp.route("/payments/<int:payment_id>", methods=["GET"])
@admin_session_required
def payment_detail(payment_id):
    row = (
        db.session.query(Payment, User, Pack)
        .join(User, User.id == Payment.user_id)
        .join(Pack, Pack.id == Payment.pack_id)
        .filter(Payment.id == payment_id)
        .first_or_404()
    )

    p, u, pack = row

    return jsonify({
        "payment_id": p.id,
        "user_email": u.email,
        "pack_title": pack.title_vi,
        "amount_vnd": p.amount_vnd,
        "status": p.status,
        "note": p.note,
        "created_at": p.created_at.isoformat(),
        "processed_by": p.processed_by,
        "processed_at": p.processed_at.isoformat() if p.processed_at else None
    })


# =========================
# ADMIN: USER OWNED PACKS
# =========================
@admin_bp.route("/users/<int:user_id>/packs", methods=["GET"])
@admin_session_required
def user_packs(user_id):
    rows = (
        db.session.query(Ownership, Pack)
        .join(Pack, Pack.id == Ownership.pack_id)
        .filter(Ownership.user_id == user_id)
        .all()
    )

    return jsonify([
        {
            "pack_id": pack.id,
            "pack_title": pack.title_vi,
            "granted_at": o.created_at.isoformat()
        }
        for o, pack in rows
    ])


# =========================
# ADMIN: REVOKE OWNERSHIP
# =========================
@admin_bp.route("/ownership/revoke", methods=["POST"])
@admin_session_required
def revoke_ownership():
    data = request.get_json() or {}
    user_id = data.get("user_id")
    pack_id = data.get("pack_id")

    if not user_id or not pack_id:
        return {"error": "user_id and pack_id required"}, 400

    Ownership.query.filter_by(
        user_id=user_id,
        pack_id=pack_id
    ).delete()

    db.session.commit()

    return {"message": "Ownership revoked"}

@admin_bp.route("/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")
        ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)
        now = datetime.utcnow()

        # =============================
        # CONFIG
        # =============================
        MAX_FAILED_ATTEMPTS = 5
        FAILED_WINDOW_MINUTES = 10
        LOCK_MINUTES = 15

        # =============================
        # 1️⃣ CHECK IF IP IS LOCKED
        # =============================
        lock_time = now - timedelta(minutes=LOCK_MINUTES)

        recent_lock = (
            AdminActionLog.query
            .filter(
                AdminActionLog.action == "IP Locked",
                AdminActionLog.ip_address == ip_address,
                AdminActionLog.created_at >= lock_time
            )
            .first()
        )

        if recent_lock:
            return render_template(
                "login.html",
                error="Too many failed attempts. Try again later."
            )

        # =============================
        # 2️⃣ NORMAL LOGIN CHECK
        # =============================
        user = User.query.filter_by(email=email, is_admin=1).first()

        if not user or not user.check_password(password):

            # Log failed login
            db.session.add(AdminActionLog(
                admin_id=user.id if user else None,
                action="Failed Login",
                target_type="system",
                target_id=None,
                description="Invalid admin credentials",
                ip_address=ip_address,
                user_agent=request.headers.get("User-Agent")
            ))
            db.session.commit()

            # =============================
            # 3️⃣ COUNT FAILED ATTEMPTS
            # =============================
            window_time = now - timedelta(minutes=FAILED_WINDOW_MINUTES)

            failed_count = (
                AdminActionLog.query
                .filter(
                    AdminActionLog.action == "Failed Login",
                    AdminActionLog.ip_address == ip_address,
                    AdminActionLog.created_at >= window_time
                )
                .count()
            )

            if failed_count >= MAX_FAILED_ATTEMPTS:

                db.session.add(AdminActionLog(
                    admin_id=None,
                    action="IP Locked",
                    target_type="system",
                    target_id=0,
                    description=f"IP locked after {failed_count} failed attempts",
                    ip_address=ip_address
                ))
                db.session.commit()

            return render_template(
                "login.html",
                error="Invalid admin credentials"
            )

        # =============================
        # 4️⃣ SUCCESS LOGIN
        # =============================
        session["admin_id"] = user.id
        session["admin_email"] = user.email

        db.session.add(AdminActionLog(
            admin_id=user.id,
            action="Login",
            target_type="system",
            target_id=user.id,
            ip_address=ip_address,
            user_agent=request.headers.get("User-Agent")
        ))

        # =============================
        # 5️⃣ DETECT NEW IP
        # =============================
        previous_ips = (
            db.session.query(AdminActionLog.ip_address)
            .filter(
                AdminActionLog.admin_id == user.id,
                AdminActionLog.action == "Login"
            )
            .distinct()
            .all()
        )

        known_ips = [ip[0] for ip in previous_ips if ip[0]]

        if ip_address not in known_ips:
            db.session.add(AdminActionLog(
                admin_id=user.id,
                action="Suspicious Login",
                target_type="system",
                target_id=user.id,
                description=f"New IP detected: {ip_address}",
                ip_address=ip_address
            ))

        db.session.commit()

        return redirect("/admin/dashboard")

    return render_template("login.html")



@admin_bp.route("/payments/<int:payment_id>/approve", methods=["POST"])
@admin_session_required
def admin_approve_payment(payment_id):
    payment = Payment.query.get_or_404(payment_id)

    if payment.status != "pending":
        return redirect("/admin/payments")

    # Grant ownership
    exists = Ownership.query.filter_by(
        user_id=payment.user_id,
        pack_id=payment.pack_id
    ).first()

    if not exists:
        db.session.add(Ownership(
            user_id=payment.user_id,
            pack_id=payment.pack_id
        ))

    payment.status = "approved"
    payment.processed_by = session.get("admin_id")
    payment.processed_at = datetime.utcnow()
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

# ✅ LOG ACTION
    db.session.add(AdminActionLog(
        admin_id=session.get("admin_id"),
        action="Approve Payment",
        target_type="payment",
        target_id=payment.id,
        description=f"Approved payment {payment.id} for user {payment.user_id}",
        ip_address = ip_address
    ))
    db.session.commit()
    return redirect("/admin/payments")


@admin_bp.route("/payments/<int:payment_id>/reject", methods=["POST"])
@admin_session_required
def admin_reject_payment(payment_id):
    note = request.form.get("note")

    payment = Payment.query.get_or_404(payment_id)

    if payment.status != "pending":
        return redirect("/admin/payments")

    payment.status = "rejected"
    payment.note = note
    payment.processed_by = request.admin_id
    payment.processed_at = datetime.utcnow()
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

 # ✅ LOG ACTION
    db.session.add(AdminActionLog(
        admin_id=request.admin_id,
        action="Reject Payment",
        target_type="payment",
        target_id=payment.id,
        description=f"Rejected payment {payment.id}: {note}",
        ip_address=ip_address
    ))
    db.session.commit()
    return redirect("/admin/payments")
@admin_bp.route("/payments/<int:payment_id>/revoke", methods=["POST"])
@admin_session_required
def admin_revoke_payment(payment_id):
    note = request.form.get("note", "Revoked by admin")
    payment = Payment.query.get_or_404(payment_id)
    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

    if payment.status != "approved":
        return redirect("/admin/payments")

    Ownership.query.filter_by(
        user_id=payment.user_id,
        pack_id=payment.pack_id
    ).delete()

    payment.status = "revoked"
    payment.note = note
    payment.processed_by = request.admin_id
    payment.processed_at = datetime.utcnow()
     # ✅ LOG ACTION
    db.session.add(AdminActionLog(
        admin_id=request.admin_id,
        action="Revoke Payment",
        target_type="payment",
        target_id=payment.id,
        description=f"Revoked payment {payment.id}",
        ip_address = ip_address
    ))
    db.session.commit()
    return redirect("/admin/payments")

@admin_bp.route("/logout")
@admin_session_required
def admin_logout():

    from models import AdminActionLog

    ip_address = request.headers.get("X-Forwarded-For", request.remote_addr)

    db.session.add(AdminActionLog(
        admin_id=session.get("admin_id"),
        action="Logout",
        target_type="system",
        target_id=session.get("admin_id"),
        description="Admin logged out",
        ip_address=ip_address
    ))

    db.session.commit()

    session.clear()
    return redirect("/admin/login")


# =========================
# ADMIN: VIEW ACTION LOGS
# =========================
@admin_bp.route("/logs", methods=["GET"])
@admin_session_required
def admin_logs():
    page = int(request.args.get("page", 1))
    per_page = 10

    action = request.args.get("action")
    admin_email = request.args.get("admin")
    
    query = (
        db.session.query(AdminActionLog, User)
        .outerjoin(User, User.id == AdminActionLog.admin_id)
    )

    # Filters
    if action:
        query = query.filter(AdminActionLog.action.ilike(f"%{action}%"))

    if admin_email:
        query = query.filter(User.email.ilike(f"%{admin_email}%"))

    query = query.order_by(AdminActionLog.created_at.desc())

    total = query.count()

    rows = (
        query
        .offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    return render_template(
        "logs.html",
        logs=[
            {
                "admin_email": u.email,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                "ip_address": log.ip_address
            }
            for log, u in rows
        ],
        page=page,
        total_pages=(total + per_page - 1) // per_page,
        filters={
            "action": action,
            "admin": admin_email
        }
    )


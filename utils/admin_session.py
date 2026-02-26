from functools import wraps
from flask import session, redirect, request

def admin_session_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        admin_id = session.get("admin_id")

        if not admin_id:
            return redirect("/admin/login")

        # ✅ attach admin info to request
        request.admin_id = admin_id
        request.admin_email = session.get("admin_email")

        return fn(*args, **kwargs)

    return wrapper

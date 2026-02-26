# utils/admin.py
from functools import wraps
from flask import request, jsonify
from models import User
from extensions import db
from utils.jwt import decode_token

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return {"error": "Unauthorized"}, 401

        token = auth.split(" ", 1)[1]

        try:
            payload = decode_token(token)
        except Exception:
            return {"error": "Invalid token"}, 401

        user_id = payload.get("sub")
        user = db.session.get(User, user_id)

        if not user or not getattr(user, "is_admin", False):
            return {"error": "Admin access required"}, 403

        request.user_id = user.id
        request.user = user

        return fn(*args, **kwargs)

    return wrapper

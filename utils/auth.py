from functools import wraps
from flask import request, jsonify
import jwt
from config import Config
from models import User
from extensions import db


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return {"error": "Missing token"}, 401

        token = auth.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                Config.SECRET_KEY,
                algorithms=["HS256"]
            )
            request.user_id = int(payload["sub"])
        except Exception:
            return {"error": "Invalid token"}, 401

        return fn(*args, **kwargs)

    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return {"error": "Missing token"}, 401

        token = auth.split(" ")[1]

        try:
            payload = jwt.decode(
                token,
                Config.SECRET_KEY,
                algorithms=["HS256"]
            )
            user_id = int(payload["sub"])
        except Exception:
            return {"error": "Invalid token"}, 401

        user = User.query.get(user_id)
        if not user or not getattr(user, "is_admin", False):
            return {"error": "Unauthorized"}, 403

        request.user_id = user_id
        return fn(*args, **kwargs)

    return wrapper

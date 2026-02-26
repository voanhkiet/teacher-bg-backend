import jwt
from datetime import datetime, timedelta
from flask import current_app

def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id),  # ✅ MUST be string
        "exp": datetime.utcnow() + timedelta(days=7),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(
        payload,
        current_app.config["SECRET_KEY"],
        algorithm="HS256"
    )

def decode_token(token: str) -> dict:
    return jwt.decode(
        token,
        current_app.config["SECRET_KEY"],
        algorithms=["HS256"],
        options={"verify_aud": False}
    )

from flask import Blueprint, jsonify, request, abort
from models import Pack, Image, Ownership
from constants.subjects import SUBJECTS
from utils.auth import login_required
import jwt
from utils.jwt import decode_token
from extensions import db

packs_bp = Blueprint("packs", __name__, url_prefix="/api/packs")

def get_user_id_if_logged_in():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None

    token = auth.split(" ", 1)[1]
    try:
        payload = decode_token(token)
        return int(payload["sub"])
    except jwt.InvalidTokenError:
        return None
    
@packs_bp.route("", methods=["GET"])
def get_packs():
    lang = request.args.get("lang", "vi")
    subject = request.args.get("subject")

    query = Pack.query

    if subject:
        query = query.filter_by(subject=subject)

    packs = query.order_by(Pack.created_at.desc()).all()

    return jsonify([
        {
            "id": p.id,
            "title": p.title_vi if lang == "vi" else p.title_en,
            "subject": p.subject,
            "subject_label": SUBJECTS[p.subject][lang],
            "price_vnd": p.price_vnd,
            "is_free": p.price_vnd == 0,
            "cover_image": p.cover_image,
            "created_at": p.created_at.isoformat(),
        }
        for p in packs
    ])
@packs_bp.route("/<int:pack_id>", methods=["GET"])
def get_pack_detail(pack_id):
    lang = request.args.get("lang", "vi")

    pack = Pack.query.get_or_404(pack_id)

    user_id = get_user_id_if_logged_in()

    owned = False
    if user_id:
        owned = Ownership.query.filter_by(
            user_id=user_id,
            pack_id=pack.id
        ).first() is not None

    unlocked = pack.is_free or owned

    images = []
    for img in pack.images:
        images.append({
            "id": img.id,
            "preview_url": img.preview_url,
            "image_url": img.image_url if unlocked else None,
            "locked": not unlocked
        })

    return {
        "id": pack.id,
        "title": pack.title_vi if lang == "vi" else pack.title_en,
        "description": pack.description_vi if lang == "vi" else pack.description_en,
        "subject": pack.subject,
        "subject_label": SUBJECTS[pack.subject][lang],
        "price_vnd": pack.price_vnd,
        "is_free": pack.is_free,
        "owned": owned,
        "images": images,
        "cover_image": pack.cover_image,
        "created_at": pack.created_at.isoformat()
    }
@packs_bp.route("/<int:pack_id>/purchase", methods=["POST"])
@login_required
def purchase_pack(pack_id):
    pack = Pack.query.get_or_404(pack_id)

    if pack.is_free:
        return {"message": "Pack is free"}, 400

    exists = Ownership.query.filter_by(
        user_id=request.user_id,
        pack_id=pack.id
    ).first()

    if exists:
        return {"message": "Already owned"}, 200

    ownership = Ownership(
        user_id=request.user_id,
        pack_id=pack.id
    )
    db.session.add(ownership)
    db.session.commit()

    return {"message": "Purchase successful"}, 201

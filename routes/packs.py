from flask import Blueprint, jsonify
from models import Pack

packs_bp = Blueprint("packs", __name__, url_prefix="/api/packs")

@packs_bp.route("", methods=["GET"])
def get_packs():
    packs = Pack.query.all()
    return jsonify([
        {
            "id": p.id,
            "title_vi": p.title_vi,
            "title_en": p.title_en,
            "price_vnd": p.price_vnd,
            "cover_image": p.cover_image
        } for p in packs
    ])

from .root import root_bp
from .packs import packs_bp

def register_routes(app):
    app.register_blueprint(root_bp)
    app.register_blueprint(packs_bp)

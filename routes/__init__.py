from .root import root_bp
from .packs import packs_bp
from .auth import auth_bp


def register_routes(app):
    app.register_blueprint(root_bp)
    app.register_blueprint(packs_bp)
    app.register_blueprint(auth_bp)

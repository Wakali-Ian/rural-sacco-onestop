from flask import Flask
from app.config import Config
from app.models import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)

    from app.routes.mpesa import mpesa_bp
    from app.routes.ussd import ussd_bp
    from app.routes.voice import voice_bp
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.members import members_bp

    app.register_blueprint(mpesa_bp)
    app.register_blueprint(ussd_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(members_bp)

    return app

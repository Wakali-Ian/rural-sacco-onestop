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
    from app.routes.reports import reports_bp
    from app.routes.admin import admin_bp
    from app.routes.rewards import rewards_bp

    for bp in (mpesa_bp, ussd_bp, voice_bp, auth_bp,
               dashboard_bp, members_bp, reports_bp,
               admin_bp, rewards_bp):
        app.register_blueprint(bp)

    return app

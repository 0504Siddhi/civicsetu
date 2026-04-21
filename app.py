"""
CivicSetu — Smart Civic Issue Reporting & Resolution System
Main Flask application entry point
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
import os

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app():
    app = Flask(__name__)

    # ── Configuration ──────────────────────────────────────────
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'civicsetu_secret_key_2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
        'DATABASE_URL', 'sqlite:///civicsetu.db'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5 MB
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg'}

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # ── Init extensions ────────────────────────────────────────
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # ── Register blueprints ────────────────────────────────────
    from routes.auth import auth_bp
    from routes.citizen import citizen_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(citizen_bp, url_prefix='/citizen')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')

    # ── Create DB tables & seed data ──────────────────────────
    with app.app_context():
        db.create_all()
        _seed_data()

    return app


def _seed_data():
    """Seed issue types and a default admin if they don't exist."""
    from models.models import IssueType, Admin

    try:
        count = db.session.query(IssueType).count()
    except Exception:
        count = 0

    if count == 0:
        types = [
            IssueType(type_name='pothole',        description='Road potholes and surface damage',      priority_level='High'),
            IssueType(type_name='garbage',         description='Garbage dumping or uncollected waste',  priority_level='Medium'),
            IssueType(type_name='water_leakage',   description='Water pipeline leaks or flooding',      priority_level='Critical'),
            IssueType(type_name='streetlight',     description='Broken or non-functional streetlights', priority_level='Medium'),
            IssueType(type_name='sewage',          description='Sewage overflow or blocked drains',     priority_level='High'),
            IssueType(type_name='tree_fall',       description='Fallen trees blocking roads/paths',     priority_level='High'),
            IssueType(type_name='electricity',     description='Electrical hazards or power outages',   priority_level='Critical'),
            IssueType(type_name='other',           description='Other civic issues',                    priority_level='Low'),
        ]
        db.session.add_all(types)

    if db.session.query(Admin).count() == 0:
        from app import bcrypt as _bcrypt
        hashed = _bcrypt.generate_password_hash('admin123').decode('utf-8')
        admin = Admin(username='admin', email='admin@civicsetu.in',
                      password_hash=hashed, role='super_admin')
        db.session.add(admin)

    db.session.commit()


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

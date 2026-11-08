"""
CivicSetu — Smart Civic Issue Reporting & Resolution System
Main Flask application entry point
"""

import os
import secrets
import hmac
from flask import Flask, session, request, abort, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()
login_manager = LoginManager()
bcrypt = Bcrypt()


def normalize_database_url(raw_url=None, is_production=False):
    """
    Safely normalizes database connection strings for SQLAlchemy 2.0+ compatibility.
    - Explicitly enforces the 'postgresql+psycopg2://' driver scheme for PostgreSQL,
      matching the installed psycopg2-binary package and preventing SQLAlchemy from
      attempting to import Psycopg 3 ('psycopg').
    - Preserves local SQLite database support when DATABASE_URL is omitted or set to SQLite.
    - Gracefully handles missing or empty DATABASE_URL in production with a clear error.
    """
    url = (raw_url or '').strip()
    if not url:
        if is_production:
            raise RuntimeError(
                "CRITICAL: DATABASE_URL environment variable is missing or empty in production. "
                "Render PostgreSQL requires a valid connection string. "
                "Please configure DATABASE_URL in your Render Web Service dashboard."
            )
        return 'sqlite:///civicsetu.db'

    # Normalise all PostgreSQL URL variants to explicit postgresql+psycopg2://
    postgres_prefixes = (
        'postgresql+psycopg2://',
        'postgresql+psycopg://',
        'postgresql://',
        'postgres+psycopg2://',
        'postgres+psycopg://',
        'postgres://',
    )
    for prefix in postgres_prefixes:
        if url.startswith(prefix):
            return 'postgresql+psycopg2://' + url[len(prefix):]

    return url


def create_app():
    app = Flask(__name__)

    # ── Automatically load .env if available ────────────────────
    try:
        from dotenv import load_dotenv
        env_path = os.path.join(app.root_path, '.env')
        if os.path.exists(env_path):
            load_dotenv(env_path)
        else:
            load_dotenv()
    except ImportError:
        pass

    # ── Environment & Production Checks ────────────────────────
    is_production = os.environ.get('FLASK_ENV') == 'production' or bool(os.environ.get('RENDER'))

    # ── Configuration ──────────────────────────────────────────
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        if is_production:
            raise RuntimeError(
                "CRITICAL: SECRET_KEY environment variable must be set in production environments."
            )
        secret_key = 'civicsetu_dev_secret_key_change_in_production'

    app.config['SECRET_KEY'] = secret_key

    # Database URL: safely normalize PostgreSQL connection strings for psycopg2 driver
    raw_db_url = os.environ.get('DATABASE_URL')
    app.config['SQLALCHEMY_DATABASE_URI'] = normalize_database_url(raw_db_url, is_production=is_production)

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

    # ── CSRF Protection ────────────────────────────────────────
    @app.context_processor
    def inject_csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(32)
        return dict(csrf_token=lambda: session['_csrf_token'])

    @app.before_request
    def validate_csrf():
        if request.method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            # Allow API routes to handle their own session/token validation
            if request.path.startswith('/api/'):
                return
            session_token = session.get('_csrf_token')
            request_token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
            if not session_token or not request_token or not hmac.compare_digest(session_token, request_token):
                abort(400, description="CSRF validation failed: Missing or invalid CSRF token.")

    # ── HTTP Error Handlers ────────────────────────────────────
    @app.errorhandler(413)
    def request_entity_too_large(e):
        flash('Uploaded file is too large. Maximum allowed file size is 5 MB.', 'danger')
        return redirect(request.referrer or url_for('citizen.submit'))

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
        _seed_data(is_production)

    return app


def _seed_data(is_production=False):
    """Seed default issue types and admin user if they don't exist."""
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
        admin_email = os.environ.get('ADMIN_EMAIL', 'admin@civicsetu.in')
        admin_pw = os.environ.get('ADMIN_PASSWORD')
        if not admin_pw:
            if is_production:
                print("[Security Warning] No ADMIN_PASSWORD provided in production; skipping default admin seeding.")
            else:
                admin_pw = 'admin123'

        if admin_pw:
            from app import bcrypt as _bcrypt
            hashed = _bcrypt.generate_password_hash(admin_pw).decode('utf-8')
            admin = Admin(username='admin', email=admin_email,
                          password_hash=hashed, role='super_admin')
            db.session.add(admin)

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

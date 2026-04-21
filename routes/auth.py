"""
routes/auth.py — Authentication routes for CivicSetu
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from models.models import User, Admin

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return _redirect_by_role()
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role()

    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        role     = request.form.get('role', 'citizen')

        if role == 'admin':
            user = Admin.query.filter_by(email=email).first()
        else:
            user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash('Welcome back! Logged in successfully.', 'success')
            return _redirect_by_role()
        else:
            flash('Invalid email or password. Please try again.', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return _redirect_by_role()

    if request.method == 'POST':
        name     = request.form.get('name', '').strip()
        email    = request.form.get('email', '').strip().lower()
        phone    = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')

        if not name or not email or not password:
            flash('Name, email, and password are required.', 'warning')
        elif len(password) < 6:
            flash('Password must be at least 6 characters.', 'warning')
        elif password != confirm:
            flash('Passwords do not match.', 'warning')
        elif User.query.filter_by(email=email).first():
            flash('This email is already registered. Please log in.', 'info')
        else:
            hashed = bcrypt.generate_password_hash(password).decode('utf-8')
            user = User(name=name, email=email, phone=phone, password_hash=hashed)
            db.session.add(user)
            db.session.commit()
            flash('Account created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out. See you soon!', 'info')
    return redirect(url_for('auth.login'))


def _redirect_by_role():
    if hasattr(current_user, 'admin_id'):
        return redirect(url_for('admin.dashboard'))
    return redirect(url_for('citizen.dashboard'))

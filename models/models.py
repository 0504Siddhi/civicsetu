"""
models/models.py
All SQLAlchemy ORM models for CivicSetu
"""

from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith('admin_'):
        return Admin.query.get(int(user_id[6:]))
    return User.query.get(int(user_id))


class IssueType(db.Model):
    __tablename__ = 'issue_types'

    type_id        = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type_name      = db.Column(db.String(50), unique=True, nullable=False)
    description    = db.Column(db.String(255))
    priority_level = db.Column(db.String(20), default='Medium')

    complaints = db.relationship('Complaint', backref='issue_type', lazy=True)

    def __repr__(self):
        return f'<IssueType {self.type_name}>'


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    user_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name          = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    phone         = db.Column(db.String(15))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    complaints = db.relationship('Complaint', backref='citizen', lazy=True)

    def get_id(self):
        return str(self.user_id)

    def __repr__(self):
        return f'<User {self.email}>'


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'

    admin_id      = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username      = db.Column(db.String(80), unique=True, nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role          = db.Column(db.String(20), default='moderator')

    status_updates = db.relationship('StatusLog', backref='admin', lazy=True)

    def get_id(self):
        return 'admin_' + str(self.admin_id)

    def __repr__(self):
        return f'<Admin {self.username}>'


class Complaint(db.Model):
    __tablename__ = 'complaints'

    complaint_id  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    type_id       = db.Column(db.Integer, db.ForeignKey('issue_types.type_id'), nullable=False)
    image_path    = db.Column(db.String(300), nullable=True)
    location      = db.Column(db.String(255), nullable=False)
    description   = db.Column(db.Text)
    status        = db.Column(db.String(20), default='Pending', nullable=False)
    ai_confidence = db.Column(db.Float)
    submitted_at  = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at   = db.Column(db.DateTime, nullable=True)

    status_history = db.relationship('StatusLog', backref='complaint', lazy=True)

    def __repr__(self):
        return f'<Complaint #{self.complaint_id} [{self.status}]>'

    @property
    def image_url(self):
        """Resolves image reference to a browser-accessible URL."""
        if not self.image_path:
            return None
        from utils.storage import resolve_image_url
        return resolve_image_url(self.image_path)


class StatusLog(db.Model):
    __tablename__ = 'status_log'

    log_id       = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id'), nullable=False)
    admin_id     = db.Column(db.Integer, db.ForeignKey('admins.admin_id'), nullable=False)
    old_status   = db.Column(db.String(20))
    new_status   = db.Column(db.String(20), nullable=False)
    changed_at   = db.Column(db.DateTime, default=datetime.utcnow)
    remarks      = db.Column(db.Text)

    def __repr__(self):
        return f'<StatusLog {self.old_status}→{self.new_status}>'


# ── NEW: Likes / Dislikes per complaint per user ──────────────────
class ComplaintReaction(db.Model):
    __tablename__ = 'complaint_reactions'

    reaction_id  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id', ondelete='CASCADE'), nullable=False)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.user_id',      ondelete='CASCADE'), nullable=False)
    reaction     = db.Column(db.String(10), nullable=False)   # 'like' or 'dislike'
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('complaint_id', 'user_id', name='uq_reaction_user_complaint'),)

    def __repr__(self):
        return f'<Reaction {self.reaction} on #{self.complaint_id}>'


# ── NEW: Public comments on complaints ───────────────────────────
class ComplaintComment(db.Model):
    __tablename__ = 'complaint_comments'

    comment_id   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    complaint_id = db.Column(db.Integer, db.ForeignKey('complaints.complaint_id', ondelete='CASCADE'), nullable=False)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.user_id',      ondelete='CASCADE'), nullable=False)
    body         = db.Column(db.Text, nullable=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='comments', lazy=True)

    def __repr__(self):
        return f'<Comment #{self.comment_id} on complaint #{self.complaint_id}>'

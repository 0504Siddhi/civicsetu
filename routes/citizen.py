"""
routes/citizen.py — Citizen-facing routes for CivicSetu
"""

import os
import uuid
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from app import db, bcrypt
from models.models import Complaint, IssueType, ComplaintReaction, ComplaintComment

citizen_bp = Blueprint('citizen', __name__)
ALLOWED = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


@citizen_bp.route('/dashboard')
@login_required
def dashboard():
    if hasattr(current_user, 'admin_id'):
        return redirect(url_for('admin.dashboard'))
    complaints = (Complaint.query
                  .filter_by(user_id=current_user.user_id)
                  .order_by(Complaint.submitted_at.desc())
                  .all())
    stats = {
        'total':       len(complaints),
        'pending':     sum(1 for c in complaints if c.status == 'Pending'),
        'in_progress': sum(1 for c in complaints if c.status == 'In Progress'),
        'resolved':    sum(1 for c in complaints if c.status == 'Resolved'),
    }
    return render_template('citizen/dashboard.html', complaints=complaints, stats=stats)


@citizen_bp.route('/submit', methods=['GET', 'POST'])
@login_required
def submit():
    if hasattr(current_user, 'admin_id'):
        return redirect(url_for('admin.dashboard'))

    issue_types = IssueType.query.filter(IssueType.type_name != 'other').all()

    from sqlalchemy import func
    counts_raw = (db.session.query(Complaint.type_id, func.count(Complaint.complaint_id).label('cnt'))
                  .group_by(Complaint.type_id).all())
    count_map = {row.type_id: row.cnt for row in counts_raw}

    if request.method == 'POST':
        file     = request.files.get('image')
        location = request.form.get('location', '').strip()
        desc     = request.form.get('description', '').strip()
        type_id  = request.form.get('type_id')
        form_data = {'location': location, 'description': desc, 'type_id': type_id}

        if not location:
            flash('Location is required.', 'warning')
            return render_template('citizen/submit.html', issue_types=issue_types, count_map=count_map, form_data=form_data)
        if not type_id:
            flash('Please select an issue category.', 'warning')
            return render_template('citizen/submit.html', issue_types=issue_types, count_map=count_map, form_data=form_data)

        image_path = None
        if file and file.filename:
            if not allowed_file(file.filename):
                flash('Invalid image format. Allowed formats: PNG, JPG, JPEG.', 'danger')
                return render_template('citizen/submit.html', issue_types=issue_types, count_map=count_map, form_data=form_data)

            try:
                from utils.storage import upload_complaint_image
                image_path = upload_complaint_image(file)
            except Exception as upload_err:
                current_app.logger.error("Complaint image upload failed [%s]", type(upload_err).__name__)
                flash('Image upload failed. Your complaint was not submitted. Please try again.', 'danger')
                return render_template('citizen/submit.html', issue_types=issue_types, count_map=count_map, form_data=form_data)

        # Validate optional AI confidence metadata if provided
        ai_conf_raw = request.form.get('ai_confidence')
        ai_confidence = None
        if ai_conf_raw is not None and ai_conf_raw != '':
            try:
                val = float(ai_conf_raw)
                if 0.0 <= val <= 1.0:
                    ai_confidence = round(val, 4)
            except (ValueError, TypeError):
                ai_confidence = None

        complaint = Complaint(
            user_id=current_user.user_id, type_id=int(type_id),
            image_path=image_path, location=location,
            description=desc, ai_confidence=ai_confidence,
        )

        try:
            db.session.add(complaint)
            db.session.commit()
        except Exception as db_err:
            db.session.rollback()
            current_app.logger.error("Database commit error [%s]", type(db_err).__name__)
            if image_path:
                try:
                    from utils.storage import delete_complaint_image
                    delete_complaint_image(image_path)
                except Exception as cleanup_err:
                    current_app.logger.warning("Failed to clean up image after database error [%s]", type(cleanup_err).__name__)
            flash('An error occurred while saving your complaint. Please try again.', 'danger')
            return render_template('citizen/submit.html', issue_types=issue_types, count_map=count_map, form_data=form_data)

        flash(f'✅ Complaint #{complaint.complaint_id} submitted successfully!', 'success')
        return redirect(url_for('citizen.dashboard'))

    return render_template('citizen/submit.html', issue_types=issue_types, count_map=count_map)


@citizen_bp.route('/complaint/<int:complaint_id>')
@login_required
def complaint_detail(complaint_id):
    complaint = Complaint.query.filter_by(
        complaint_id=complaint_id, user_id=current_user.user_id
    ).first_or_404()

    likes    = ComplaintReaction.query.filter_by(complaint_id=complaint_id, reaction='like').count()
    dislikes = ComplaintReaction.query.filter_by(complaint_id=complaint_id, reaction='dislike').count()
    my_reaction = ComplaintReaction.query.filter_by(
        complaint_id=complaint_id, user_id=current_user.user_id).first()
    comments = (ComplaintComment.query.filter_by(complaint_id=complaint_id)
                .order_by(ComplaintComment.created_at.asc()).all())

    return render_template('citizen/complaint_detail.html',
                           complaint=complaint,
                           likes=likes, dislikes=dislikes,
                           my_reaction=my_reaction.reaction if my_reaction else None,
                           comments=comments)


@citizen_bp.route('/complaint/<int:complaint_id>/react', methods=['POST'])
@login_required
def react(complaint_id):
    reaction_type = request.form.get('reaction')
    if reaction_type not in ('like', 'dislike'):
        flash('Invalid reaction.', 'danger')
        return redirect(url_for('citizen.complaint_detail', complaint_id=complaint_id))
    existing = ComplaintReaction.query.filter_by(
        complaint_id=complaint_id, user_id=current_user.user_id).first()
    if existing:
        if existing.reaction == reaction_type:
            db.session.delete(existing)
        else:
            existing.reaction = reaction_type
    else:
        db.session.add(ComplaintReaction(
            complaint_id=complaint_id, user_id=current_user.user_id, reaction=reaction_type))
    db.session.commit()
    return redirect(url_for('citizen.complaint_detail', complaint_id=complaint_id))


@citizen_bp.route('/complaint/<int:complaint_id>/comment', methods=['POST'])
@login_required
def add_comment(complaint_id):
    body = request.form.get('body', '').strip()
    if not body:
        flash('Comment cannot be empty.', 'warning')
        return redirect(url_for('citizen.complaint_detail', complaint_id=complaint_id))
    if len(body) > 500:
        flash('Comment too long (max 500 characters).', 'warning')
        return redirect(url_for('citizen.complaint_detail', complaint_id=complaint_id))
    db.session.add(ComplaintComment(
        complaint_id=complaint_id, user_id=current_user.user_id, body=body))
    db.session.commit()
    flash('Comment posted!', 'success')
    return redirect(url_for('citizen.complaint_detail', complaint_id=complaint_id))


@citizen_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if hasattr(current_user, 'admin_id'):
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'update_profile':
            name  = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            if name:
                current_user.name  = name
                current_user.phone = phone
                db.session.commit()
                flash('Profile updated successfully!', 'success')
            else:
                flash('Name cannot be empty.', 'warning')
        elif action == 'change_password':
            old_pw  = request.form.get('old_password', '')
            new_pw  = request.form.get('new_password', '')
            conf_pw = request.form.get('confirm_password', '')
            if not bcrypt.check_password_hash(current_user.password_hash, old_pw):
                flash('Current password is incorrect.', 'danger')
            elif len(new_pw) < 6:
                flash('New password must be at least 6 characters.', 'warning')
            elif new_pw != conf_pw:
                flash('New passwords do not match.', 'warning')
            else:
                current_user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
                db.session.commit()
                flash('Password changed successfully!', 'success')
        elif action == 'set_language':
            session['lang'] = request.form.get('language', 'en')
            flash('Language updated!', 'success')
        return redirect(url_for('citizen.profile'))

    complaints = Complaint.query.filter_by(user_id=current_user.user_id).all()
    total    = len(complaints)
    resolved = sum(1 for c in complaints if c.status == 'Resolved')
    pending  = sum(1 for c in complaints if c.status == 'Pending')

    # Honor score: 10pts per complaint, 20pts per resolved
    honor_score = min(total * 10 + resolved * 20, 1000)

    # Badges
    badges = []
    if total >= 1:
        badges.append({'icon': '🏙️', 'name': 'Civic Hero',      'desc': 'Reported your first issue'})
    if resolved >= 3:
        badges.append({'icon': '🛡️', 'name': 'Area Guardian',   'desc': '3+ complaints resolved'})
    if total >= 5:
        badges.append({'icon': '⭐', 'name': 'Top Contributor', 'desc': 'Reported 5+ issues'})

    current_lang = session.get('lang', 'en')
    return render_template('citizen/profile.html',
                           stats=dict(total=total, resolved=resolved, pending=pending),
                           honor_score=honor_score,
                           badges=badges,
                           current_lang=current_lang)

"""
routes/admin.py — Admin-facing routes for CivicSetu
"""

import csv
import io
from datetime import datetime
from functools import wraps
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, make_response)
from flask_login import login_required, current_user
from app import db
from models.models import Complaint, IssueType, User, Admin, StatusLog

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not hasattr(current_user, 'admin_id'):
            flash('Admin access required.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total    = Complaint.query.count()
    pending  = Complaint.query.filter_by(status='Pending').count()
    in_prog  = Complaint.query.filter_by(status='In Progress').count()
    resolved = Complaint.query.filter_by(status='Resolved').count()
    rejected = Complaint.query.filter_by(status='Rejected').count()

    recent = (Complaint.query
              .order_by(Complaint.submitted_at.desc())
              .limit(10).all())

    # ── Dynamic Priority: rank issue types by complaint count ──
    from sqlalchemy import func
    type_counts = (db.session.query(IssueType, func.count(Complaint.complaint_id).label('cnt'))
                   .outerjoin(Complaint, Complaint.type_id == IssueType.type_id)
                   .group_by(IssueType.type_id)
                   .order_by(func.count(Complaint.complaint_id).desc())
                   .all())

    # Assign dynamic priority labels based on rank
    priority_map = {}
    for i, (issue_type, cnt) in enumerate(type_counts):
        if i == 0:
            priority_map[issue_type.type_id] = ('Critical', cnt)
        elif i == 1:
            priority_map[issue_type.type_id] = ('High', cnt)
        elif i <= 3:
            priority_map[issue_type.type_id] = ('Medium', cnt)
        else:
            priority_map[issue_type.type_id] = ('Low', cnt)

    stats = dict(total=total, pending=pending, in_progress=in_prog,
                 resolved=resolved, rejected=rejected)
    return render_template('admin/dashboard.html', stats=stats, recent=recent,
                           type_counts=type_counts, priority_map=priority_map)


@admin_bp.route('/complaints')
@login_required
@admin_required
def complaints():
    status_filter = request.args.get('status', '')
    type_filter   = request.args.get('type_id', '')

    query = Complaint.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if type_filter:
        query = query.filter_by(type_id=int(type_filter))

    all_complaints = query.order_by(Complaint.submitted_at.desc()).all()
    issue_types    = IssueType.query.all()

    # ── Dynamic Priority: rank by live complaint count ──
    from sqlalchemy import func
    type_counts = (db.session.query(IssueType, func.count(Complaint.complaint_id).label('cnt'))
                   .outerjoin(Complaint, Complaint.type_id == IssueType.type_id)
                   .group_by(IssueType.type_id)
                   .order_by(func.count(Complaint.complaint_id).desc())
                   .all())
    priority_map = {}
    for i, (issue_type, cnt) in enumerate(type_counts):
        if i == 0:
            priority_map[issue_type.type_id] = ('Critical', cnt)
        elif i == 1:
            priority_map[issue_type.type_id] = ('High', cnt)
        elif i <= 3:
            priority_map[issue_type.type_id] = ('Medium', cnt)
        else:
            priority_map[issue_type.type_id] = ('Low', cnt)

    return render_template('admin/complaints.html',
                           complaints=all_complaints,
                           issue_types=issue_types,
                           status_filter=status_filter,
                           type_filter=type_filter,
                           priority_map=priority_map)


@admin_bp.route('/complaints/<int:complaint_id>')
@login_required
@admin_required
def complaint_detail(complaint_id):
    complaint = Complaint.query.get_or_404(complaint_id)
    return render_template('admin/complaint_detail.html', complaint=complaint)


@admin_bp.route('/complaints/<int:complaint_id>/update', methods=['POST'])
@login_required
@admin_required
def update_status(complaint_id):
    complaint  = Complaint.query.get_or_404(complaint_id)
    new_status = request.form.get('status')
    remarks    = request.form.get('remarks', '')

    valid_statuses = {'Pending', 'In Progress', 'Resolved', 'Rejected'}
    if new_status not in valid_statuses:
        flash('Invalid status value.', 'danger')
        return redirect(url_for('admin.complaints'))

    log = StatusLog(
        complaint_id = complaint.complaint_id,
        admin_id     = current_user.admin_id,
        old_status   = complaint.status,
        new_status   = new_status,
        remarks      = remarks,
    )
    db.session.add(log)

    complaint.status = new_status
    if new_status == 'Resolved':
        complaint.resolved_at = datetime.utcnow()

    db.session.commit()
    flash(f'Complaint #{complaint_id} updated to "{new_status}".', 'success')

    # Return to wherever we came from
    next_page = request.form.get('next', url_for('admin.complaints'))
    return redirect(next_page)


@admin_bp.route('/complaints/export')
@login_required
@admin_required
def export_csv():
    all_complaints = (Complaint.query
                      .join(User).join(IssueType)
                      .order_by(Complaint.submitted_at.desc()).all())

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Citizen', 'Email', 'Issue Type', 'Location',
                     'Status', 'Submitted At', 'Resolved At'])

    for c in all_complaints:
        writer.writerow([
            c.complaint_id,
            c.citizen.name,
            c.citizen.email,
            c.issue_type.type_name,
            c.location,
            c.status,
            c.submitted_at.strftime('%Y-%m-%d %H:%M'),
            c.resolved_at.strftime('%Y-%m-%d %H:%M') if c.resolved_at else '',
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=civicsetu_export.csv'
    return response

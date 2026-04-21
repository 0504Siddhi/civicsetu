"""
routes/api.py — JSON REST API for CivicSetu
AI uses Google Gemini (FREE TIER).
"""

import json
import urllib.request
import urllib.error
import os
import time
from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app import db
from models.models import Complaint, IssueType, StatusLog

api_bp = Blueprint('api', __name__)

@api_bp.route('/complaints', methods=['GET'])
@login_required
def get_complaints():
    user_id = request.args.get('user_id', type=int)
    status  = request.args.get('status')
    type_id = request.args.get('type_id', type=int)
    query = Complaint.query
    if user_id: query = query.filter_by(user_id=user_id)
    if status:  query = query.filter_by(status=status)
    if type_id: query = query.filter_by(type_id=type_id)
    items = query.order_by(Complaint.submitted_at.desc()).all()
    return jsonify([{
        'complaint_id': c.complaint_id,
        'type':         c.issue_type.type_name,
        'location':     c.location,
        'status':       c.status,
        'submitted_at': c.submitted_at.isoformat(),
        'image_url':    f'/static/{c.image_path}' if c.image_path else None,
    } for c in items])

@api_bp.route('/complaints/<int:cid>', methods=['PATCH'])
@login_required
def patch_complaint(cid):
    if not hasattr(current_user, 'admin_id'):
        return jsonify({'error': 'Forbidden'}), 403
    data       = request.get_json()
    complaint  = Complaint.query.get_or_404(cid)
    new_status = data.get('status')
    if new_status not in {'Pending', 'In Progress', 'Resolved', 'Rejected'}:
        return jsonify({'error': 'Invalid status'}), 400
    log = StatusLog(
        complaint_id=cid, admin_id=current_user.admin_id,
        old_status=complaint.status, new_status=new_status,
        remarks=data.get('remarks', ''),
    )
    db.session.add(log)
    complaint.status = new_status
    db.session.commit()
    return jsonify({'message': 'Updated', 'new_status': new_status}), 200

@api_bp.route('/issue-types', methods=['GET'])
def get_issue_types():
    types = IssueType.query.all()
    return jsonify([{'type_id': t.type_id, 'type_name': t.type_name} for t in types])

@api_bp.route('/stats', methods=['GET'])
@login_required
def stats():
    return jsonify({
        'total':       Complaint.query.count(),
        'pending':     Complaint.query.filter_by(status='Pending').count(),
        'in_progress': Complaint.query.filter_by(status='In Progress').count(),
        'resolved':    Complaint.query.filter_by(status='Resolved').count(),
    })

# ── Gemini AI Detection ──────────────────────────────────────
def _call_gemini(api_key, model, payload):
    """
    Makes one HTTP call to Gemini. Returns (result_dict, None) on success,
    or (None, http_error_code) on failure.
    """
    url = (
        f"https://generativelanguage.googleapis.com/v1beta"
        f"/models/{model}:generateContent?key={api_key}"
    )
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode('utf-8')), None
    except urllib.error.HTTPError as e:
        body = ""
        try:
            body = e.read().decode('utf-8', errors='replace')
        except Exception:
            pass
        print(f"[Gemini] Model={model} HTTP {e.code}: {body[:300]}")
        return None, e.code
    except Exception as e:
        print(f"[Gemini] Model={model} Exception: {e}")
        return None, -1


@api_bp.route('/ai-classify', methods=['POST'])
@login_required
def ai_classify():
    data       = request.get_json()
    image_b64  = data.get('image_b64', '')
    media_type = data.get('media_type', 'image/jpeg')

    api_key = os.environ.get('GEMINI_API_KEY', '')
    if not api_key:
        return jsonify({'error': 'GEMINI_API_KEY not set in .env'}), 500

    issue_types = IssueType.query.all()
    type_names  = [t.type_name for t in issue_types]

    try:
        b64 = image_b64.split(',')[1] if ',' in image_b64 else image_b64
        b64 = b64.strip().replace("\n", "").replace("\r", "")
    except Exception:
        return jsonify({'error': 'Invalid image format'}), 400

    prompt = (
        f"You are a civic issue analyzer for CivicSetu India.\n"
        f"Classify this image into EXACTLY ONE of these categories: {', '.join(type_names)}\n\n"
        f'Output ONLY valid JSON (no markdown, no extra text):\n'
        f'{{"category": "category_name", "confidence": 0.95, "reason": "Short explanation"}}'
    )

    payload = {
        "contents": [{"parts": [
            {"inline_data": {"mime_type": media_type, "data": b64}},
            {"text": prompt}
        ]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 200,
        }
    }

    # Free-tier models as of 2026 — 1.5 models are SHUT DOWN (404). Use 2.5 series.
    MODELS = [
        "gemini-3.1-flash-lite-preview",  # FASTEST: 1000+ req/day (New 2026 standard)
    "gemini-3-flash-preview",       # PhD-level reasoning, very high limits
    "gemini-2.5-flash",             # Stable fallback (No suffix needed)
    "gemini-2.5-pro"                       # 100 req/day free, most capable
    ]

    last_error_code = None

    for model in MODELS:
        # Each model gets up to 2 attempts (1 retry on 503/429)
        for attempt in range(2):
            result, err_code = _call_gemini(api_key, model, payload)

            if result is not None:
                # ── Success: parse the AI response ──
                try:
                    parts = result['candidates'][0]['content']['parts']
                    raw_text = parts[0]['text'].strip()
                    # Strip markdown code fences if model added them
                    if raw_text.startswith("```"):
                        raw_text = raw_text.split("```")[1]
                        if raw_text.startswith("json"):
                            raw_text = raw_text[4:]
                        raw_text = raw_text.strip()
                    ai = json.loads(raw_text)
                except (KeyError, IndexError, json.JSONDecodeError) as parse_err:
                    print(f"[Gemini] Parse error on model={model}: {parse_err}")
                    break  # try next model

                cat     = ai.get('category', 'other')
                conf    = float(ai.get('confidence', 0.5))
                reason  = ai.get('reason', '')
                matched = next(
                    (t for t in issue_types if t.type_name.lower() == cat.lower()),
                    None
                )
                return jsonify({
                    'category':   cat,
                    'type_id':    matched.type_id if matched else None,
                    'confidence': conf,
                    'reason':     reason,
                    'model':      model,
                })

            # ── Error handling ──
            last_error_code = err_code

            if err_code in (503, 429) and attempt == 0:
                # Overloaded / rate-limited — wait and retry same model once
                wait = 4 if err_code == 429 else 2
                print(f"[Gemini] {err_code} on {model}, waiting {wait}s then retrying...")
                time.sleep(wait)
                continue  # retry same model

            if err_code == 404:
                # Model doesn't exist for this key — skip immediately
                break

            if err_code == 400:
                # Bad request (wrong image format, etc.) — no point retrying
                return jsonify({'error': 'Bad request to Gemini (check image format)'}), 400

            if err_code == 403:
                return jsonify({'error': 'Gemini API key is invalid or expired. Get a new one at https://aistudio.google.com/'}), 403

            # Any other error — try next model
            break

    # All models failed
    return jsonify({
        'error': f'Gemini AI unavailable (last error: {last_error_code}). Check your GEMINI_API_KEY or try again later.',
        'hint': 'Get a free key at https://aistudio.google.com/'
    }), 503

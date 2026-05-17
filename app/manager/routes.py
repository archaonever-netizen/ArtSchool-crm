from flask import render_template, session, redirect, url_for, jsonify
from app.manager import manager_bp
from app import db
from app.models import Student, Lesson, Payment, AdjustmentRequest, User, Notification

@manager_bp.route('/')
def dashboard():
    if session.get('role') != 'manager':
        return redirect(url_for('auth.login'))
    return render_template('manager/dashboard.html')


@manager_bp.route('/api/dashboard')
def dashboard_api():
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401
    total_students = Student.query.count()
    active_lessons = Lesson.query.filter(Lesson.status == 'planned').count()
    income = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0.0)).filter(Payment.type == 'income').scalar() or 0.0
    expense = db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0.0)).filter(Payment.type == 'expense').scalar() or 0.0
    profit = income - expense
    return jsonify({
        'total_students': total_students,
        'active_lessons': active_lessons,
        'income': round(float(income), 2),
        'expense': round(float(expense), 2),
        'profit': round(float(profit), 2)
    })


@manager_bp.route('/api/adjustment-requests', methods=['GET'])
def manager_adjustment_requests_api():
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401
    reqs = AdjustmentRequest.query.order_by(AdjustmentRequest.created_at.desc()).all()
    out = []
    for r in reqs:
        student = Student.query.get(r.student_id) if r.student_id else None
        creator = User.query.get(r.created_by) if r.created_by else None
        out.append({
            'id': r.id,
            'student_id': r.student_id,
            'student_name': student.full_name if student else None,
            'type': r.type,
            'amount': r.amount,
            'reason': r.reason,
            'status': r.status,
            'created_by': r.created_by,
            'created_by_name': creator.username if creator else None,
            'created_at': r.created_at.isoformat()
        })
    return jsonify(out)


@manager_bp.route('/api/adjustment-requests/<int:req_id>/approve', methods=['POST'])
def manager_approve_request(req_id):
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401
    req = AdjustmentRequest.query.get(req_id)
    if not req:
        return jsonify({'error': 'Not found'}), 404
    if req.status != 'pending':
        return jsonify({'error': 'Already processed'}), 400
    student = Student.query.get(req.student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404
    # apply adjustment
    if req.type == 'add':
        student.lessons_remaining = (student.lessons_remaining or 0) + (req.amount or 0)
    else:
        try:
            student.lessons_remaining = (student.lessons_remaining or 0) - (req.amount or 0)
        except Exception:
            student.lessons_remaining = 0
    req.status = 'approved'
    db.session.commit()

    # notify creator
    if req.created_by:
        note = Notification(user_id=req.created_by, message=f'Запрос корректировки #{req.id} был одобрен.')
        db.session.add(note)
    # notify student
    if student and student.user_id:
        note2 = Notification(user_id=student.user_id, message=f'Вашему аккаунту зачислено {req.amount} занятий (запрос #{req.id}).')
        db.session.add(note2)
    db.session.commit()
    return jsonify({'status': 'ok'})


@manager_bp.route('/api/adjustment-requests/<int:req_id>/reject', methods=['POST'])
def manager_reject_request(req_id):
    if session.get('role') != 'manager':
        return jsonify({'error': 'Unauthorized'}), 401
    req = AdjustmentRequest.query.get(req_id)
    if not req:
        return jsonify({'error': 'Not found'}), 404
    if req.status != 'pending':
        return jsonify({'error': 'Already processed'}), 400
    req.status = 'rejected'
    db.session.commit()
    if req.created_by:
        note = Notification(user_id=req.created_by, message=f'Запрос корректировки #{req.id} был отклонён.')
        db.session.add(note)
        db.session.commit()
    return jsonify({'status': 'ok'})


@manager_bp.route('/adjustments')
def adjustments_page():
    if session.get('role') != 'manager':
        return redirect(url_for('auth.login'))
    return render_template('manager/adjustments.html')

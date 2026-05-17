from flask import render_template, session, redirect, url_for, jsonify
from app.manager import manager_bp
from app import db
from app.models import Student, Lesson, Payment

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

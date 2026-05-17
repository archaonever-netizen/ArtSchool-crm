from flask import render_template, session, redirect, url_for
from app.teacher import teacher_bp

@teacher_bp.route('/')
def dashboard():
    if session.get('role') != 'teacher':
        return redirect(url_for('auth.login'))
    return render_template('teacher/dashboard.html')

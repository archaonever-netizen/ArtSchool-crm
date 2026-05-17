from flask import render_template, session, redirect, url_for
from app.student import student_bp

@student_bp.route('/')
def dashboard():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))
    return render_template('student/dashboard.html')

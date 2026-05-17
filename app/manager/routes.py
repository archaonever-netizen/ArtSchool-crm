from flask import render_template, session, redirect, url_for
from app.manager import manager_bp

@manager_bp.route('/')
def dashboard():
    if session.get('role') != 'manager':
        return redirect(url_for('auth.login'))
    return render_template('manager/dashboard.html')

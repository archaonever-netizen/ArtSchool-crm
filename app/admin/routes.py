from flask import render_template, session, redirect, url_for
from app.admin import admin_bp

@admin_bp.route('/')
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin/dashboard.html')

# app/admin/__init__.py
from flask import Blueprint, session, redirect, url_for
admin_bp = Blueprint('admin', __name__, template_folder='../templates/admin')

@admin_bp.before_request
def require_admin_role():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
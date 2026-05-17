from flask import Blueprint, session, redirect, url_for
manager_bp = Blueprint('manager', __name__, template_folder='../templates/manager')

@manager_bp.before_request
def require_manager_role():
    if session.get('role') != 'manager':
        return redirect(url_for('auth.login'))

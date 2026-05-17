from flask import Blueprint, session, redirect, url_for
teacher_bp = Blueprint('teacher', __name__, template_folder='../templates/teacher')

@teacher_bp.before_request
def require_teacher_role():
    if session.get('role') != 'teacher':
        return redirect(url_for('auth.login'))

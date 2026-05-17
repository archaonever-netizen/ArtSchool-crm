from flask import Blueprint, session, redirect, url_for
student_bp = Blueprint('student', __name__, template_folder='../templates/student')

@student_bp.before_request
def require_student_role():
    if session.get('role') != 'student':
        return redirect(url_for('auth.login'))

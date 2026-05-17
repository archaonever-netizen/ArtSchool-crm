from flask import render_template, request, redirect, url_for, session, flash
from werkzeug.security import check_password_hash
from app import db
from app.models import User
from app.auth import auth_bp

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.id
            session['role'] = user.role
            role_redirects = {
                'admin': 'admin.dashboard',
                'manager': 'manager.dashboard',
                'teacher': 'teacher.dashboard',
                'student': 'student.dashboard'
            }
            return redirect(url_for(role_redirects.get(user.role, 'index')))
        flash('Неверный логин или пароль')
    return render_template('auth/login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

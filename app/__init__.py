import os
from flask import Flask, session, redirect, url_for, render_template, request
from flask_sqlalchemy import SQLAlchemy
from config import Config
from supabase import create_client, Client
from werkzeug.security import generate_password_hash

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    supabase: Client = create_client(app.config['SUPABASE_URL'], app.config['SUPABASE_SERVICE_ROLE_KEY'])
    app.supabase = supabase

    # Регистрация blueprint'ов
    from app.auth.routes import auth_bp
    app.register_blueprint(auth_bp, url_prefix='/auth')

    from app.admin.routes import admin_bp
    app.register_blueprint(admin_bp, url_prefix='/admin')

    from app.manager.routes import manager_bp
    app.register_blueprint(manager_bp, url_prefix='/manager')

    from app.teacher.routes import teacher_bp
    app.register_blueprint(teacher_bp, url_prefix='/teacher')

    from app.student.routes import student_bp
    app.register_blueprint(student_bp, url_prefix='/student')

    # Главная страница выбора ролей
    @app.route('/')
    def index():
        return render_template('index.html')

    # Автоматическое создание таблиц и админа по умолчанию
    with app.app_context():
        db.create_all()
        from app.models import User
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                password_hash=generate_password_hash('admin123'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()

    # Вспомогательный декоратор для проверки входа
    @app.before_request
    def check_authentication():
        public_endpoints = ['auth.login', 'index', 'static']
        if request.endpoint in public_endpoints:
            return
        if 'user_id' not in session:
            return redirect(url_for('auth.login'))

    return app
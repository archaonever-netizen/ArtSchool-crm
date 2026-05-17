from flask import render_template, session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash
from app.admin import admin_bp
from app import db
from app.models import User, Student, Tariff


@admin_bp.route('/')
def dashboard():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin/dashboard.html')


@admin_bp.route('/students')
def students_page():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin/students.html')


@admin_bp.route('/api/students', methods=['GET', 'POST'])
def students_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        students = Student.query.all()
        result = []
        for s in students:
            user = User.query.get(s.user_id)
            tariff = None
            if s.tariff_id:
                tariff = Tariff.query.get(s.tariff_id)
            result.append({
                'id': s.id,
                'full_name': s.full_name,
                'phone': s.phone,
                'tariff': tariff.name if tariff else None,
                'tariff_id': s.tariff_id,
                'lessons_remaining': s.lessons_remaining,
                'coins': s.coins,
                'user_id': s.user_id
            })
        return jsonify(result)

    data = request.get_json() or request.form
    phone = data.get('phone')
    full_name = data.get('full_name')
    tariff_id = data.get('tariff_id')
    initial_lessons = int(data.get('initial_lessons') or 0)
    password = data.get('password')

    if not phone or not password:
        return jsonify({'error': 'phone and password required'}), 400

    if User.query.filter_by(username=phone).first():
        return jsonify({'error': 'User with this phone already exists'}), 400

    user = User(username=phone, password_hash=generate_password_hash(password), role='student')
    db.session.add(user)
    db.session.flush()

    student = Student(user_id=user.id, full_name=full_name, phone=phone, tariff_id=tariff_id or None, lessons_remaining=initial_lessons)
    db.session.add(student)
    db.session.commit()

    return jsonify({'status': 'ok', 'id': student.id})


@admin_bp.route('/api/students/<int:student_id>', methods=['PUT', 'PATCH', 'DELETE'])
def student_detail_api(student_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Not found'}), 404

    if request.method in ('PUT', 'PATCH'):
        data = request.get_json() or request.form
        student.full_name = data.get('full_name', student.full_name)
        student.tariff_id = data.get('tariff_id', student.tariff_id)
        db.session.commit()
        return jsonify({'status': 'ok'})

    # DELETE
    user = User.query.get(student.user_id) if student.user_id else None
    if user:
        db.session.delete(student)
        db.session.delete(user)
    else:
        db.session.delete(student)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@admin_bp.route('/api/tariffs', methods=['GET'])
def tariffs_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    tariffs = Tariff.query.filter_by(is_archived=False).all()
    return jsonify([{'id': t.id, 'name': t.name, 'lessons_count': t.lessons_count, 'price': t.price} for t in tariffs])

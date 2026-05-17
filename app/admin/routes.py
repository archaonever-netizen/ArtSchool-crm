from flask import render_template, session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash
from app.admin import admin_bp
from app import db
from app.models import User, Student, Tariff
from app.models import Lesson, Enrollment, Teacher, LessonTemplate, Notification
from datetime import datetime


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


@admin_bp.route('/api/teachers', methods=['GET'])
def teachers_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    teachers = Teacher.query.all()
    return jsonify([{'id': t.id, 'full_name': t.full_name, 'phone': t.phone} for t in teachers])


@admin_bp.route('/schedule')
def schedule_page():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin/schedule.html')


@admin_bp.route('/api/lessons', methods=['GET'])
def lessons_list_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    lessons = Lesson.query.all()
    out = []
    for l in lessons:
        out.append({
            'id': l.id,
            'title': l.title,
            'start': l.datetime_start.isoformat(),
            'end': l.datetime_end.isoformat(),
            'teacher_id': l.teacher_id,
            'max_students': l.max_students,
            'status': l.status,
            'enrolled_count': l.enrollments.count()
        })
    return jsonify(out)


@admin_bp.route('/api/lesson/add', methods=['POST'])
def lesson_add_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or request.form
    title = data.get('title')
    lesson_template_id = data.get('lesson_template_id')
    start = data.get('datetime_start')
    end = data.get('datetime_end')
    teacher_id = data.get('teacher_id')
    max_students = int(data.get('max_students') or 10)
    if not title or not start or not end:
        return jsonify({'error': 'Missing fields'}), 400
    try:
        dt_start = datetime.fromisoformat(start)
        dt_end = datetime.fromisoformat(end)
    except Exception:
        return jsonify({'error': 'Invalid datetime format'}), 400
    lesson = Lesson(lesson_template_id=lesson_template_id or None, title=title, datetime_start=dt_start, datetime_end=dt_end, teacher_id=teacher_id or None, max_students=max_students)
    db.session.add(lesson)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': lesson.id})


@admin_bp.route('/api/lesson/<int:lesson_id>', methods=['PUT', 'PATCH', 'DELETE', 'GET'])
def lesson_detail_api(lesson_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({'error': 'Not found'}), 404
    if request.method == 'GET':
        return jsonify({
            'id': lesson.id,
            'title': lesson.title,
            'start': lesson.datetime_start.isoformat(),
            'end': lesson.datetime_end.isoformat(),
            'teacher_id': lesson.teacher_id,
            'max_students': lesson.max_students,
            'status': lesson.status,
            'enrolled_count': lesson.enrollments.count()
        })
    if request.method in ('PUT', 'PATCH'):
        data = request.get_json() or request.form
        lesson.title = data.get('title', lesson.title)
        if data.get('datetime_start'):
            lesson.datetime_start = datetime.fromisoformat(data.get('datetime_start'))
        if data.get('datetime_end'):
            lesson.datetime_end = datetime.fromisoformat(data.get('datetime_end'))
        lesson.teacher_id = data.get('teacher_id', lesson.teacher_id)
        lesson.max_students = int(data.get('max_students', lesson.max_students))
        lesson.status = data.get('status', lesson.status)
        db.session.commit()
        return jsonify({'status': 'ok'})
    # DELETE
    # delete enrollments first
    Enrollment.query.filter_by(lesson_id=lesson.id).delete()
    db.session.delete(lesson)
    db.session.commit()
    return jsonify({'status': 'deleted'})


@admin_bp.route('/api/lesson/<int:lesson_id>/students', methods=['GET'])
def lesson_students_api(lesson_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({'error': 'Not found'}), 404
    result = []
    for e in lesson.enrollments:
        student = Student.query.get(e.student_id)
        result.append({'enrollment_id': e.id, 'student_id': student.id, 'full_name': student.full_name, 'phone': student.phone, 'status': e.status})
    return jsonify(result)


@admin_bp.route('/api/lesson/<int:lesson_id>/attendance', methods=['POST'])
def lesson_attendance_api(lesson_id):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json() or request.form
    enrollment_id = data.get('enrollment_id')
    status = data.get('status')  # attended / missed
    enrollment = Enrollment.query.get(enrollment_id)
    if not enrollment or enrollment.lesson_id != lesson_id:
        return jsonify({'error': 'Not found'}), 404
    student = Student.query.get(enrollment.student_id)
    if status == 'attended':
        enrollment.status = 'attended'
        student.coins = (student.coins or 0) + 1
        note = Notification(user_id=student.user_id, message=f'Вы отмечены как пришедший на занятие "{enrollment.lesson.title}". +1 монета.')
        db.session.add(note)
    elif status == 'missed':
        enrollment.status = 'missed'
        try:
            student.lessons_remaining = (student.lessons_remaining or 0) - 1
        except Exception:
            student.lessons_remaining = 0
        note = Notification(user_id=student.user_id, message=f'Вам списано занятие за пропуск на "{enrollment.lesson.title}".')
        db.session.add(note)
    db.session.commit()
    return jsonify({'status': 'ok'})

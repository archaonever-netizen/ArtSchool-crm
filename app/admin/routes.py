from flask import render_template, session, redirect, url_for, request, jsonify
from werkzeug.security import generate_password_hash
from app.admin import admin_bp
from app import db
from app.models import User, Student, Tariff
from app.models import Lesson, Enrollment, Teacher, LessonTemplate, Notification, Program, AdjustmentRequest, Payment, Regulation
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


@admin_bp.route('/api/adjustment-requests', methods=['GET', 'POST'])
def admin_adjustment_requests_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        reqs = AdjustmentRequest.query.order_by(AdjustmentRequest.created_at.desc()).all()
        out = []
        for r in reqs:
            student = Student.query.get(r.student_id) if r.student_id else None
            creator = User.query.get(r.created_by) if r.created_by else None
            out.append({
                'id': r.id,
                'student_id': r.student_id,
                'student_name': student.full_name if student else None,
                'type': r.type,
                'amount': r.amount,
                'reason': r.reason,
                'status': r.status,
                'created_by': r.created_by,
                'created_by_name': creator.username if creator else None,
                'created_at': r.created_at.isoformat()
            })
        return jsonify(out)

    # POST - create new request (admin creates on behalf)
    data = request.get_json() or request.form
    student_id = data.get('student_id')
    rtype = data.get('type')
    amount = int(data.get('amount') or 0)
    reason = data.get('reason')
    creator_id = session.get('user_id')
    if not student_id or not rtype or amount == 0:
        return jsonify({'error': 'student_id, type and amount required'}), 400
    req = AdjustmentRequest(student_id=student_id, type=rtype, amount=amount, reason=reason, created_by=creator_id)
    db.session.add(req)
    db.session.commit()

    # notify first manager
    mgr = User.query.filter_by(role='manager').first()
    if mgr:
        note = Notification(user_id=mgr.id, message=f'Новый запрос на корректировку для ученика ID {student_id}: {rtype} {amount}.')
        db.session.add(note)
        db.session.commit()

    return jsonify({'status': 'ok', 'id': req.id})


@admin_bp.route('/api/teachers', methods=['GET'])
def teachers_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    teachers = Teacher.query.all()
    return jsonify([{'id': t.id, 'full_name': t.full_name, 'phone': t.phone} for t in teachers])


@admin_bp.route('/api/lesson-templates', methods=['GET'])
def lesson_templates_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    templates = LessonTemplate.query.all()
    result = []
    for item in templates:
        program = Program.query.get(item.program_id) if item.program_id else None
        result.append({
            'id': item.id,
            'title': item.title,
            'program_id': item.program_id,
            'program_name': program.name if program else None
        })
    return jsonify(result)


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
        teacher_name = l.teacher.full_name if l.teacher else None
        template = LessonTemplate.query.get(l.lesson_template_id) if l.lesson_template_id else None
        out.append({
            'id': l.id,
            'title': l.title,
            'start': l.datetime_start.isoformat(),
            'end': l.datetime_end.isoformat(),
            'teacher_id': l.teacher_id,
            'teacher_name': teacher_name,
            'lesson_template_id': l.lesson_template_id,
            'lesson_template_title': template.title if template else None,
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
        template = LessonTemplate.query.get(lesson.lesson_template_id) if lesson.lesson_template_id else None
        return jsonify({
            'id': lesson.id,
            'title': lesson.title,
            'start': lesson.datetime_start.isoformat(),
            'end': lesson.datetime_end.isoformat(),
            'teacher_id': lesson.teacher_id,
            'teacher_name': lesson.teacher.full_name if lesson.teacher else None,
            'lesson_template_id': lesson.lesson_template_id,
            'lesson_template_title': template.title if template else None,
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


# ----------------- PAYMENTS (Admin) -----------------
@admin_bp.route('/payments')
def payments_page():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin/payments.html')


@admin_bp.route('/api/payments', methods=['GET', 'POST'])
def payments_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        payments = Payment.query.order_by(Payment.date.desc()).all()
        out = []
        for p in payments:
            creator = User.query.get(p.created_by) if p.created_by else None
            out.append({
                'id': p.id,
                'type': p.type,
                'amount': p.amount,
                'description': p.description,
                'date': p.date.isoformat(),
                'created_by': p.created_by,
                'created_by_name': creator.username if creator else None
            })
        return jsonify(out)

    # POST
    data = request.get_json() or request.form
    ptype = data.get('type')
    amount = float(data.get('amount') or 0)
    description = data.get('description')
    date_str = data.get('date')
    try:
        dt = datetime.fromisoformat(date_str).date() if date_str else datetime.utcnow().date()
    except Exception:
        dt = datetime.utcnow().date()
    creator_id = session.get('user_id')
    if ptype not in ('income', 'expense') or amount == 0:
        return jsonify({'error': 'type (income|expense) and amount required'}), 400
    p = Payment(type=ptype, amount=amount, description=description, date=dt, created_by=creator_id)
    db.session.add(p)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': p.id})


@admin_bp.route('/api/payments/<int:pid>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def payment_detail_api(pid):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    p = Payment.query.get(pid)
    if not p:
        return jsonify({'error': 'Not found'}), 404
    if request.method == 'GET':
        creator = User.query.get(p.created_by) if p.created_by else None
        return jsonify({
            'id': p.id,
            'type': p.type,
            'amount': p.amount,
            'description': p.description,
            'date': p.date.isoformat(),
            'created_by': p.created_by,
            'created_by_name': creator.username if creator else None
        })
    if request.method in ('PUT', 'PATCH'):
        data = request.get_json() or request.form
        p.type = data.get('type', p.type)
        p.amount = float(data.get('amount', p.amount))
        p.description = data.get('description', p.description)
        if data.get('date'):
            try:
                p.date = datetime.fromisoformat(data.get('date')).date()
            except Exception:
                pass
        db.session.commit()
        return jsonify({'status': 'ok'})
    # DELETE
    db.session.delete(p)
    db.session.commit()
    return jsonify({'status': 'deleted'})


# ----------------- REGULATIONS -----------------
@admin_bp.route('/regulations')
def regulations_page():
    if session.get('role') != 'admin':
        return redirect(url_for('auth.login'))
    return render_template('admin/regulations.html')


@admin_bp.route('/api/regulations', methods=['GET', 'POST'])
def regulations_api():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    if request.method == 'GET':
        regs = Regulation.query.order_by(Regulation.updated_at.desc()).all()
        return jsonify([{'id': r.id, 'title': r.title, 'content': r.content, 'updated_at': r.updated_at.isoformat()} for r in regs])
    data = request.get_json() or request.form
    title = data.get('title')
    content = data.get('content')
    if not title:
        return jsonify({'error': 'title required'}), 400
    reg = Regulation(title=title, content=content)
    db.session.add(reg)
    db.session.commit()
    return jsonify({'status': 'ok', 'id': reg.id})


@admin_bp.route('/api/regulations/<int:rid>', methods=['GET', 'PUT', 'PATCH', 'DELETE'])
def regulation_detail_api(rid):
    if session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    r = Regulation.query.get(rid)
    if not r:
        return jsonify({'error': 'Not found'}), 404
    if request.method == 'GET':
        return jsonify({'id': r.id, 'title': r.title, 'content': r.content, 'updated_at': r.updated_at.isoformat()})
    if request.method in ('PUT', 'PATCH'):
        data = request.get_json() or request.form
        r.title = data.get('title', r.title)
        r.content = data.get('content', r.content)
        r.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'status': 'ok'})
    db.session.delete(r)
    db.session.commit()
    return jsonify({'status': 'deleted'})

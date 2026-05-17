from flask import current_app, request, jsonify
from app import db
from app.models import Lesson, Enrollment, Student, Notification, User
from datetime import datetime

from . import cron_bp

@cron_bp.route('/auto-attendance', methods=['POST','GET'])
def auto_attendance():
    # Simple secret key check
    key = request.args.get('key') or request.headers.get('X-CRON-KEY')
    secret = current_app.config.get('CRON_SECRET')
    if not secret or key != secret:
        return jsonify({'error': 'Unauthorized'}), 401

    now = datetime.utcnow()
    lessons = Lesson.query.filter(Lesson.datetime_end < now, Lesson.status == 'planned').all()
    processed = 0
    for lesson in lessons:
        enrollments = Enrollment.query.filter_by(lesson_id=lesson.id, status='enrolled').all()
        for e in enrollments:
            student = Student.query.get(e.student_id)
            e.status = 'missed'
            try:
                student.lessons_remaining = (student.lessons_remaining or 0) - 1
            except Exception:
                student.lessons_remaining = 0
            note = Notification(user_id=student.user_id, message=f'Вам списано занятие за пропуск на "{lesson.title}".')
            db.session.add(note)
        lesson.status = 'completed'
        processed += 1
    db.session.commit()
    # notify first admin about processed lessons
    admin_user = User.query.filter_by(role='admin').first()
    if admin_user and processed>0:
        n = Notification(user_id=admin_user.id, message=f'Авто-списание: обработано {processed} занятий.')
        db.session.add(n)
        db.session.commit()
    return jsonify({'status': 'ok', 'processed': processed})

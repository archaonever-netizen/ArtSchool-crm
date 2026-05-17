from app import db
from datetime import datetime

# ---------- ПОЛЬЗОВАТЕЛИ ----------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)  # для ученика = телефон
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # admin, manager, teacher, student
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с профилем ученика
    student_profile = db.relationship('Student', backref='user', uselist=False)
    # Связь с преподавателем (если роль teacher)
    teacher_profile = db.relationship('Teacher', backref='user', uselist=False)


class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')

# ---------- УЧЕНИК ----------
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20), unique=True, nullable=False)
    tariff_id = db.Column(db.Integer, db.ForeignKey('tariff.id'))
    lessons_remaining = db.Column(db.Integer, default=0)
    coins = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tariff = db.relationship('Tariff', backref='students')
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic')

# ---------- ПРЕПОДАВАТЕЛЬ ----------
class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True)
    full_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    specialization = db.Column(db.String(200))

# ---------- ТАРИФЫ И ПРОГРАММЫ ----------
class Tariff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    lessons_count = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    program = db.relationship('Program', backref='tariff', uselist=False, cascade="all, delete-orphan")

class Program(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tariff_id = db.Column(db.Integer, db.ForeignKey('tariff.id'), unique=True)
    name = db.Column(db.String(200))
    lessons = db.relationship('LessonTemplate', backref='program', lazy=True, order_by='LessonTemplate.order')

class LessonTemplate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    program_id = db.Column(db.Integer, db.ForeignKey('program.id'))
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    order = db.Column(db.Integer)

# ---------- ЗАНЯТИЯ ----------
class Lesson(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    lesson_template_id = db.Column(db.Integer, db.ForeignKey('lesson_template.id'))
    title = db.Column(db.String(200))
    datetime_start = db.Column(db.DateTime, nullable=False)
    datetime_end = db.Column(db.DateTime, nullable=False)
    max_students = db.Column(db.Integer, default=10)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teacher.id'))
    status = db.Column(db.String(20), default='planned')  # planned, completed, cancelled

    teacher = db.relationship('Teacher', backref='lessons')
    enrollments = db.relationship('Enrollment', backref='lesson', lazy='dynamic')

class Enrollment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'))
    status = db.Column(db.String(20), default='enrolled')  # enrolled, attended, missed
    enrolled_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- ПЛАТЕЖИ И P&L ----------
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(10), nullable=False)  # income / expense
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))

# ---------- ЗАПРОСЫ НА КОРРЕКТИРОВКУ ----------
class AdjustmentRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    type = db.Column(db.String(10))  # add / deduct
    amount = db.Column(db.Integer)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- ЗАДАЧИ ----------
class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    due_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='open')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- РЕГЛАМЕНТЫ ----------
class Regulation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------- РАЗВИТИЕ (Roadmap / MindMap) ----------
class Roadmap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200))
    content = db.Column(db.Text)  # Mermaid-код или текст
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

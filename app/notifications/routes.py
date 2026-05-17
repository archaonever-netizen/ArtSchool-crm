from flask import Blueprint, jsonify, request, session
from app import db
from app.models import Notification
from datetime import datetime

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('/', methods=['GET'])
def get_notifications():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.created_at.desc()).limit(20).all()
    return jsonify([
        {
            'id': item.id,
            'message': item.message,
            'read': item.read,
            'created_at': item.created_at.isoformat()
        }
        for item in notifications
    ])

@notifications_bp.route('/read', methods=['POST'])
def mark_all_read():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    user_id = session['user_id']
    Notification.query.filter_by(user_id=user_id, read=False).update({'read': True})
    db.session.commit()
    return jsonify({'status': 'ok'})

@notifications_bp.route('/<int:notification_id>/read', methods=['PATCH'])
def mark_notification_read(notification_id):
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    notification = Notification.query.filter_by(id=notification_id, user_id=session['user_id']).first()
    if not notification:
        return jsonify({'error': 'Not found'}), 404
    notification.read = True
    db.session.commit()
    return jsonify({'status': 'ok'})

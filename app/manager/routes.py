# app/manager/__init__.py
from flask import Blueprint
manager_bp = Blueprint('manager', __name__, template_folder='../templates/manager')
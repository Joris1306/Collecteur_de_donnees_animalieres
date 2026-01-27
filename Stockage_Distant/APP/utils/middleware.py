# auth.py
"""
Authentication module for the application
Handles user login, session management, and login required decorators
"""
import json
import os
from functools import wraps
from flask import redirect, url_for, session, request, render_template
from utlitaires import app, logging

BASE_PATH = os.path.dirname(__file__)
JSON_USERS = os.path.join(BASE_PATH, 'JSON', 'users.json')

# Session secret key - change this to something random in production
app.secret_key = 'your-secret-key-change-this-in-production'


def load_users():
    """Load users from JSON file"""
    if os.path.exists(JSON_USERS):
        with open(JSON_USERS) as f:
            return json.load(f)
    return {}


def get_user_role(user):
    """Get user role from the loaded users"""
    users = load_users()
    return users.get(user, {}).get('role', 'user')  # Default to 'user' if not found


def role_required(role):
    """Decorator to check user role"""
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if 'user' not in session or get_user_role(session['user']) != role:
                return redirect(url_for('unauthorized'))  # Redirect to unauthorized page
            return f(*args, **kwargs)
        return wrapper
    return decorator

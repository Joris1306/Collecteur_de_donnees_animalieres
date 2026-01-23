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
        with open(JSON_USERS, 'r') as f:
            return json.load(f)
    return {}


def save_users(users):
    """Save users to JSON file"""
    os.makedirs(os.path.dirname(JSON_USERS), exist_ok=True)
    with open(JSON_USERS, 'w') as f:
        json.dump(users, f, indent=2)


def verify_password(username, password):
    """Verify username and password"""
    users = load_users()
    if username in users:
        # Check if user is blocked
        if users[username].get('blocked', False):
            logging.warning(f"Login attempt for blocked user '{username}'")
            return False
        # Simple password check (in production, use proper hashing with bcrypt)
        return users[username].get('password') == password
    return False


def add_user(username, password):
    """Add a new user (admin function)"""
    users = load_users()
    if username not in users:
        users[username] = {'password': password}
        save_users(users)
        logging.info(f"User '{username}' created")
        return True
    logging.warning(f"User '{username}' already exists")
    return False


def change_password(username, old_password, new_password):
    """Change user password"""
    if not verify_password(username, old_password):
        return False
    users = load_users()
    if username in users:
        users[username]['password'] = new_password
        save_users(users)
        logging.info(f"Password changed for user '{username}'")
        return True
    return False


def is_logged_in():
    """Check if user is logged in"""
    return 'user' in session and session['user'] is not None


def login_required(f):
    """Decorator to require login for a route"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in():
            return redirect(url_for('login_page', next=request.url))
        
        # Check if user is still valid (not blocked)
        current_user = session.get('user')
        if is_user_blocked(current_user):
            logging.warning(f"Access denied: User '{current_user}' is blocked")
            session.clear()
            return redirect(url_for('login_page'))
        
        return f(*args, **kwargs)
    return decorated_function


# ===== FORCE LOGOUT FUNCTIONS =====

def block_user(username):
    """
    Block a user by marking them as blocked in users.json
    This prevents them from logging in and forces logout on next action
    """
    users = load_users()
    if username in users:
        users[username]['blocked'] = True
        save_users(users)
        logging.warning(f"User '{username}' has been blocked")
        return True
    logging.error(f"Cannot block user '{username}' - user not found")
    return False


def unblock_user(username):
    """Unblock a user so they can login again"""
    users = load_users()
    if username in users:
        users[username]['blocked'] = False
        save_users(users)
        logging.info(f"User '{username}' has been unblocked")
        return True
    logging.error(f"Cannot unblock user '{username}' - user not found")
    return False


def is_user_blocked(username):
    """Check if a user is blocked"""
    users = load_users()
    return users.get(username, {}).get('blocked', False)


def get_user_info(username):
    """Get user information including status"""
    users = load_users()
    if username in users:
        user_data = users[username].copy()
        user_data['blocked'] = is_user_blocked(username)
        return user_data
    return None

"""
Authentication module for the application
Handles user login, session management, and login required decorators
"""
import json
import os
from functools import wraps
from flask import redirect, url_for, session, request, render_template
import logging

# App root directory (parent of utils)
APP_ROOT = os.path.dirname(os.path.dirname(__file__))
JSON_USERS = os.path.join(APP_ROOT, 'JSON', 'users.json')

# Note: Do not import the Flask app here to avoid circular imports.
# Set the Flask secret key in the app initialization (utlitaires.py).


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


# ===== ROLES / ACCESS CONTROL =====
ROLE_ORDER = [
    'user',   # default/basic user
    'dev',    # developer/support level
    'admin'   # administrator
]


def get_user_role(username: str) -> str:
    """Return the role for a username, defaulting to 'user'."""
    users = load_users()
    return users.get(username, {}).get('role', 'user')


def _role_level(role: str) -> int:
    try:
        return ROLE_ORDER.index(role)
    except ValueError:
        return ROLE_ORDER.index('user')


def role_required(min_role: str):
    """
    Decorator enforcing that the current user's role is >= min_role.
    Redirects to 'unauthorized' if not permitted, or login if not authenticated.
    """
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login_page', next=request.url))
            current_user = session.get('user')
            if not current_user:
                return redirect(url_for('login_page', next=request.url))
            if is_user_blocked(current_user):
                session.clear()
                return redirect(url_for('login_page'))
            user_role = get_user_role(current_user)
            if _role_level(user_role) < _role_level(min_role):
                return redirect(url_for('unauthorized'))
            return f(*args, **kwargs)
        return wrapped
    return decorator


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

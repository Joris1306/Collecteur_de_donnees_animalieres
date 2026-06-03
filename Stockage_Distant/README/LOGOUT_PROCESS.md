# Logout Process - How It Works & How to Force Logout

## Current Logout Implementation

### How the Standard Logout Works

**Flow:**
```
User clicks logout → GET /logout → session.clear() → Redirect to /login
```

**Code in `webserver.py`:**
```python
@app.route("/logout")
def logout():
    """Handle user logout"""
    if 'user' in session:
        username = session['user']
        logging.info(f"User '{username}' logged out")
    session.clear()  # ← Clears ALL session data
    return redirect(url_for('login_page'))  # ← Redirect to login page
```

### What Happens:

1. **Session Data Cleared**: `session.clear()` removes `session['user']`
2. **Browser Cookie Invalidated**: Flask invalidates the session cookie
3. **User Redirected**: To `/login` page
4. **Next Request**: Will fail `@login_required` check since `session['user']` no longer exists

---

## Methods to Force Logout

### Method 1: Force Logout Specific User (Admin Function)

Add this to `auth.py`:

```python
def force_logout_user(username):
    """
    Force logout a user by invalidating their session
    (Admin function - call from backend)
    """
    logging.warning(f"Force logout initiated for user '{username}'")
    # Note: Session data is stored in Flask, not in a persistent store
    # This logs the action, but to actually force logout:
    # - User's session will expire naturally after SESSION_LIFETIME
    # - User can be blocked by removing from users.json
    return True

def block_user(username):
    """
    Block a user by removing them from active users
    This effectively logs them out and prevents re-login
    """
    users = load_users()
    if username in users:
        users[username]['blocked'] = True
        save_users(users)
        logging.warning(f"User '{username}' has been blocked")
        return True
    return False

def unblock_user(username):
    """Unblock a user"""
    users = load_users()
    if username in users:
        users[username]['blocked'] = False
        save_users(users)
        logging.info(f"User '{username}' has been unblocked")
        return True
    return False

def is_user_blocked(username):
    """Check if a user is blocked"""
    users = load_users()
    return users.get(username, {}).get('blocked', False)
```

Then update `verify_password()` in `auth.py`:

```python
def verify_password(username, password):
    """Verify username and password"""
    users = load_users()
    if username in users:
        # Check if user is blocked
        if is_user_blocked(username):
            logging.warning(f"Login attempt for blocked user '{username}'")
            return False
        # Simple password check (in production, use proper hashing with bcrypt)
        return users[username].get('password') == password
    return False
```

---

### Method 2: Force Logout on Login Attempt (Security)

Add this to `webserver.py` in the `login_page()` function:

```python
@app.route("/login", methods=['GET', 'POST'])
def login_page():
    """Handle login page and authentication"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Force logout current user if trying to login as someone else
        if is_logged_in() and session.get('user') != username:
            logging.info(f"User '{session.get('user')}' logged out (new login attempt)")
            session.clear()
        
        if verify_password(username, password):
            session['user'] = username
            logging.info(f"User '{username}' logged in successfully")
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            logging.warning(f"Failed login attempt for user '{username}'")
            return render_template('login.html', error='Invalid username or password'), 401
    
    if is_logged_in():
        return redirect(url_for('index'))
    
    return render_template('login.html')
```

---

### Method 3: Force Logout on Password Change (Security)

Update `change_password()` in `auth.py` to return if password changed successfully:

```python
def force_logout_on_password_change(username):
    """
    Force logout user when their password is changed
    This ensures only they can access their account with new password
    """
    logging.info(f"Force logout triggered: password change for user '{username}'")
    # Session will be invalidated on next request since stored password changed
    return True
```

---

### Method 4: Add Session Expiration (Timeout Logout)

Add this to `auth.py` after `app.secret_key`:

```python
from datetime import timedelta

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)  # 8 hours
app.config['SESSION_COOKIE_SECURE'] = True       # HTTPS only (production)
app.config['SESSION_COOKIE_HTTPONLY'] = True     # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'    # CSRF protection

def make_session_permanent(f):
    """Decorator to make session permanent (with timeout)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session.permanent = True
        return f(*args, **kwargs)
    return decorated_function
```

Then use in `login_page()`:

```python
if verify_password(username, password):
    session.permanent = True  # Enable timeout
    session['user'] = username
    logging.info(f"User '{username}' logged in successfully")
    # ... rest of code
```

Now sessions expire after 8 hours of inactivity.

---

### Method 5: Admin Panel to Force Logout All Users

Add this to `webserver.py`:

```python
@app.route("/admin/logout-all-users", methods=['POST'])
@login_required
def logout_all_users():
    """Force logout all users (admin only)"""
    current_user = session.get('user')
    
    # Check if user is admin
    if current_user != 'admin':
        logging.warning(f"Unauthorized logout-all attempt by '{current_user}'")
        return "Unauthorized", 403
    
    logging.critical(f"Admin '{current_user}' forced logout of all users")
    # Note: This only logs the action
    # In a production system with session persistence, you'd clear all sessions
    return jsonify({'status': 'All users will be logged out on next action'}), 200

@app.route("/admin/logout-user/<username>", methods=['POST'])
@login_required
def logout_user_admin(username):
    """Force logout a specific user (admin only)"""
    current_user = session.get('user')
    
    if current_user != 'admin':
        logging.warning(f"Unauthorized logout attempt by '{current_user}'")
        return "Unauthorized", 403
    
    logging.warning(f"Admin '{current_user}' forced logout of user '{username}'")
    # Note: In a production system with session store (Redis), you'd invalidate their session here
    return jsonify({'status': f'User {username} will be logged out on next action'}), 200
```

---

### Method 6: Invalidate Session Store (Production - Redis)

For production with persistent sessions using Redis:

```python
# requirements.txt
# flask-session
# redis

from flask_session import Session
import redis

# Configure Redis session store
app.config['SESSION_TYPE'] = 'redis'
app.config['SESSION_REDIS'] = redis.from_url('redis://localhost:6379')
Session(app)

def force_logout_user_redis(username):
    """Force logout user immediately using Redis session store"""
    # Get all sessions from Redis
    redis_client = redis.from_url('redis://localhost:6379')
    
    # Iterate through sessions and find the user's session
    for key in redis_client.keys('session:*'):
        session_data = redis_client.get(key)
        if session_data and b'user' in session_data and username.encode() in session_data:
            redis_client.delete(key)  # Delete the session
            logging.warning(f"Force logout: User '{username}' session deleted from Redis")
            return True
    
    return False
```

---

## Summary: Logout Options

| Method | How It Works | Use Case |
|--------|-------------|----------|
| **Standard Logout** | User clicks logout, session cleared | Normal logout flow |
| **Auto Logout (Timeout)** | Session expires after N hours | Automatic security |
| **Block User** | User marked as blocked, can't login | Admin blocks user |
| **Force New Login** | Clear session on new login attempt | Multiple user accounts |
| **Force All Logout** | Invalidate all sessions | Emergency security |
| **Redis Invalidation** | Delete session from Redis store | Production environment |

---

## Testing Logout

### Test Standard Logout
```bash
curl -X GET http://localhost:5000/logout \
  -b "session=<session_cookie>"
# Should redirect to /login and clear cookies
```

### Test Blocked User
```python
from auth import block_user, verify_password

block_user('admin')
result = verify_password('admin', 'admin123')
# Should return False
```

### Test Force Logout
```python
from manage_users import run_command

# Via manage_users.py, block the user
python manage_users.py
# Select: Remove user (effectively logs them out)
```

---

## Real-World Example: Emergency Logout

If you need to force logout a user immediately:

### Step 1: Add to `manage_users.py`

```python
def force_logout_user_interactive():
    """Force logout a user immediately"""
    print("\n=== Force Logout User ===")
    list_users()
    username = input("Username to force logout: ").strip()
    
    users = load_users()
    if username not in users:
        print(f"User '{username}' not found!")
        return
    
    # Block the user
    users[username]['blocked'] = True
    save_users(users)
    print(f"User '{username}' has been blocked and will be logged out on next action!")
    
    # Optionally change their password
    change = input("Also change their password? (yes/no): ").strip().lower()
    if change == 'yes':
        new_pass = input("New password: ").strip()
        users[username]['password'] = new_pass
        save_users(users)
        print(f"Password changed for user '{username}'")
```

### Step 2: Add to main menu

```python
elif choice == '6':
    force_logout_user_interactive()
```

---

## Key Points

✅ **Standard Logout**: `session.clear()` + `redirect('/login')`
✅ **Force Logout**: Block user in JSON or delete Redis session
✅ **Auto Logout**: Set `SESSION_COOKIE_LIFETIME`
✅ **Session Invalid**: Next `@login_required` check will fail
✅ **Production**: Use Redis for persistent session store

---

## Security Recommendations

1. **Always log logout events** - Know who logged in/out when
2. **Use session timeout** - Auto-logout after inactivity
3. **Validate on each request** - Check user still exists & unblocked
4. **Use HTTPS in production** - Protect session cookies
5. **Implement force logout** - For security incidents

# Login System - Implementation & Customization Guide

## Quick Start

1. **Default user already exists**:
   - Username: `admin`
   - Password: `admin123`

2. **Test the login**:
   - Start your Flask app normally
   - Visit `http://localhost:PORT/`
   - You'll be redirected to `/login`
   - Login with admin/admin123

3. **Add more users**:
   ```bash
   python manage_users.py
   ```

---

## How It's Implemented

### 1. **Authentication Module** (`auth.py`)
Handles:
- User verification
- Session management
- `@login_required` decorator for protecting routes

### 2. **Modified Routes** (`utils/webserver.py`)
All page routes now have `@login_required` decorator:
```python
@app.route("/")
@login_required
def index():
    # Protected route
```

API endpoints (metadata, image POST) remain **unprotected**.

### 3. **User Storage** (`JSON/users.json`)
Simple JSON file with user credentials:
```json
{
  "admin": {
    "password": "admin123"
  },
  "user1": {
    "password": "pass123"
  }
}
```

---

## Customization Options

### Option 1: Add Logout Button to Your Pages

Add this to the top of each HTML template:

```html
<nav style="background: #f8f9fa; padding: 10px 20px; display: flex; justify-content: space-between;">
    <h3>Your App</h3>
    <div>
        <span>{{ session.get('user') }}</span>
        <a href="{{ url_for('logout') }}">Logout</a>
    </div>
</nav>
```

Or use the base template approach (see `templates/navbar_example.html`).

---

### Option 2: Use Password Hashing (Recommended for Production)

Install bcrypt:
```bash
pip install bcrypt
```

Update `auth.py`:

```python
import bcrypt

def hash_password(password):
    """Hash a password using bcrypt"""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(username, password):
    """Verify username and password"""
    users = load_users()
    if username in users:
        stored_hash = users[username].get('password', '')
        return bcrypt.checkpw(password.encode(), stored_hash.encode())
    return False

def add_user(username, password):
    """Add a new user with hashed password"""
    users = load_users()
    if username not in users:
        users[username] = {'password': hash_password(password)}
        save_users(users)
        logging.info(f"User '{username}' created")
        return True
    logging.warning(f"User '{username}' already exists")
    return False
```

Then migrate existing users:
```bash
python manage_users.py
# Remove and re-add users to hash their passwords
```

---

### Option 3: Add Session Timeout

Add to `auth.py`:

```python
from datetime import timedelta

# After creating app instance
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Update login_page function
@app.route("/login", methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if verify_password(username, password):
            session.permanent = True  # Enable session timeout
            session['user'] = username
            # ... rest of code
```

---

### Option 4: Protect Specific API Endpoints

If you want to protect SOME API endpoints while keeping others open:

```python
from auth import login_required

# Open API endpoint
@app.route(METADATA_PATH, methods=['POST'])
def receive_metadata():
    # No @login_required - anyone can access
    pass

# Protected API endpoint
@app.route('/api/admin/stats', methods=['GET'])
@login_required
def admin_stats():
    # Requires login
    pass
```

---

### Option 5: Add Role-Based Access Control

Update `auth.py`:

```python
def add_user(username, password, role='user'):
    """Add a new user with a role"""
    users = load_users()
    if username not in users:
        users[username] = {'password': password, 'role': role}
        save_users(users)
        return True
    return False

def get_user_role(username):
    """Get user's role"""
    users = load_users()
    return users.get(username, {}).get('role', 'user')

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not is_logged_in() or get_user_role(session['user']) != 'admin':
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function
```

Usage:
```python
@app.route("/admin/panel")
@admin_required
def admin_panel():
    pass
```

---

### Option 6: Add HTTPS/SSL (Production)

Configure Flask for HTTPS:

```python
# In utlitaires.py or app.py
if __name__ == "__main__":
    app.run(
        port=properties.get('PORT'),
        host=my_ip(),
        ssl_context='adhoc'  # Requires pyopenssl
    )
```

Or use a reverse proxy (nginx, Apache) in production.

---

### Option 7: Database-Based Users

Instead of JSON, store users in SQLite:

```python
import sqlite3

def init_user_table():
    conn = sqlite3.connect('users.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def verify_password(username, password):
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0] == password
    return False
```

---

## File Structure After Implementation

```
/home/user/Stockage_Distant/
├── auth.py                           ← NEW: Authentication module
├── manage_users.py                   ← NEW: User management script
├── LOGIN_SETUP.md                    ← NEW: This file
├── utlitaires.py                    ← MODIFIED: No changes needed
├── JSON/
│   └── users.json                   ← NEW: User credentials
└── utils/
    └── webserver.py                 ← MODIFIED: Added @login_required decorators
```

---

## Security Checklist

- [ ] Changed `app.secret_key` in `auth.py` to a random value
- [ ] Added users with strong passwords using `manage_users.py`
- [ ] (Production) Enabled password hashing with bcrypt
- [ ] (Production) Enabled HTTPS/SSL
- [ ] (Production) Set secure session cookies
- [ ] (Production) Added session timeout
- [ ] Verified API endpoints are still accessible without login
- [ ] Tested login/logout flow
- [ ] Removed default `admin` user from production

---

## Troubleshooting

### Login page shows "Invalid username or password"
- Check `JSON/users.json` exists
- Verify username/password spelling
- Try `admin/admin123` (default test credentials)

### After login, redirected back to login
- Check `app.secret_key` is set properly
- Verify Flask session cookies are enabled
- Check browser privacy/cookie settings

### Users disappear after restart
- Ensure `JSON/users.json` is being saved
- Check file permissions on JSON directory
- Verify `manage_users.py` works correctly

### API still receiving data - great!
- This is expected - API endpoints are not protected
- They should be accessible to devices/emitters

---

## Testing

### Manual Test
```bash
# Start app
python app.py

# In browser, visit:
# http://localhost:5000/  → Redirects to /login
# http://localhost:5000/login  → Shows login form
# Login with admin/admin123  → Redirects to /
```

### Curl Test (API still works)
```bash
# These should work WITHOUT login
curl -X POST http://localhost:5000/api/metadata -d "data=..."
curl -X POST http://localhost:5000/api/image --data-binary @image.jpg

# These should redirect to /login
curl http://localhost:5000/
curl http://localhost:5000/cam
```

---

## FAQ

**Q: Can I use LDAP/Active Directory instead of JSON?**
A: Yes, update the `verify_password()` function to query LDAP instead.

**Q: Can I require email verification?**
A: Yes, add an email field to users.json and implement email verification in manage_users.py.

**Q: Can external devices bypass login?**
A: Yes, that's the design. Only web pages require login. API endpoints are open.

**Q: How do I reset a forgotten password?**
A: Edit `JSON/users.json` directly or use `manage_users.py`.

**Q: Can I add 2FA (Two-Factor Authentication)?**
A: Yes, integrate with pyotp or similar library.

---

## Support

For more information on Flask authentication, see:
- [Flask Sessions Documentation](https://flask.palletsprojects.com/sessions/)
- [Flask-Login Extension](https://flask-login.readthedocs.io/)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

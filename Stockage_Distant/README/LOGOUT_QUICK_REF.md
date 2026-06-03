# Logout Process - Quick Reference

## Standard Logout

**How It Works:**
```
User clicks "Logout" → session.clear() → Redirect to /login
```

**Code:**
```python
@app.route("/logout")
def logout():
    if 'user' in session:
        username = session['user']
        logging.info(f"User '{username}' logged out")
    session.clear()
    return redirect(url_for('login_page'))
```

**Result**: Session destroyed, user redirected to login page

---

## Force Logout Methods

### Method 1: Block User ⭐ (Recommended)

```bash
# CLI
python manage_users.py → Select 5 → Enter username

# API
curl -X POST http://localhost:5000/admin/block-user/john \
  -b "session=<admin_session>"
```

**Effect**:
- ✓ User immediately logged out
- ✗ Cannot login anymore
- **Status**: `"blocked": true` in JSON

**When to use**: Security incident, unauthorized access

---

### Method 2: Remove User (Permanent Delete)

```bash
python manage_users.py → Select 3 → Enter username
```

**Effect**:
- ✓ User completely deleted from system
- ✗ Cannot login anymore
- **Status**: User removed from JSON

**When to use**: Employee left, old test account

---

### Method 3: Change Password

```bash
python manage_users.py → Select 4 → Enter username
```

**Effect**:
- ✓ User must login again with new password
- ✓ Old password no longer works
- **Status**: Password updated

**When to use**: Password compromise, password reset

---

### Method 4: Session Timeout (Auto Logout)

**Configuration** (add to [auth.py](auth.py)):

```python
from datetime import timedelta

app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
```

**Effect**:
- ✓ Auto logout after 8 hours inactivity
- ✓ User must login again

**When to use**: Security best practice

---

### Method 5: Unblock User (Undo Block)

```bash
python manage_users.py → Select 6 → Enter username
```

**Effect**:
- ✓ User can login again
- **Status**: `"blocked": false` in JSON

**When to use**: Mistaken block, user trusted again

---

## Admin API Endpoints

### Block User
```bash
POST /admin/block-user/<username>
Authorization: Admin login required

curl -X POST http://localhost:5000/admin/block-user/john
```

**Response**: `{"status": "success", "message": "User john has been blocked"}`

---

### Unblock User
```bash
POST /admin/unblock-user/<username>

curl -X POST http://localhost:5000/admin/unblock-user/john
```

**Response**: `{"status": "success", "message": "User john has been unblocked"}`

---

### Check User Status
```bash
GET /admin/user-status/<username>

curl http://localhost:5000/admin/user-status/john
```

**Response**:
```json
{
  "username": "john",
  "blocked": false,
  "status": "active"
}
```

---

## Session Validation

### On Login
```python
def verify_password(username, password):
    users = load_users()
    if username in users:
        if users[username].get('blocked', False):  # ← Check blocked
            return False
        return users[username].get('password') == password
    return False
```

### On Page Access
```python
@login_required
def protected_page():
    current_user = session.get('user')
    if is_user_blocked(current_user):  # ← Check blocked
        session.clear()
        return redirect(url_for('login_page'))
```

---

## Force Logout Workflow

```
┌─────────────────────────────────────┐
│  User Needs to Be Logged Out        │
└──────────────┬──────────────────────┘
               │
        ┌──────▼────────┐
        │ What's the    │
        │ situation?    │
        └──┬────────┬───┘
           │        │
    ┌──────▼─┐  ┌───▼──────────┐
    │Security│  │User Left or  │
    │Issue   │  │Test Account  │
    └──┬─────┘  └───┬──────────┘
       │            │
       ▼            ▼
   Block User    Remove User
   (Temporary)   (Permanent)
```

---

## Blocking Mechanics

**User Blocked = JSON Update:**
```json
{
  "john": {
    "password": "secret123",
    "blocked": true  ← Added when blocked
  }
}
```

**What Happens When Blocked:**

1. **Can't login**: `verify_password()` returns `False`
2. **Logged out immediately**: Next request to protected page
3. **Still in system**: Can be unblocked later
4. **Password unchanged**: When unblocked, old password works

---

## Logout Event Logging

Every logout is logged:

```python
# Standard logout
logging.info(f"User 'john' logged out")

# Force block
logging.warning(f"User 'john' is blocked")

# Admin action
logging.critical(f"Admin 'admin' blocked user 'john'")
```

Check logs for audit trail of logout events.

---

## Command Cheatsheet

```bash
# List all users with status
python manage_users.py → 7

# Block user immediately
python manage_users.py → 5 → username

# Unblock user
python manage_users.py → 6 → username

# Change password (forces re-login)
python manage_users.py → 4 → username

# Remove user permanently
python manage_users.py → 3 → username

# Check user status via API
curl http://localhost:5000/admin/user-status/username
```

---

## Security Comparison

| Method | Speed | Reversible | Session Impact |
|--------|-------|-----------|---|
| **Block** | Immediate ⚡ | Yes ✓ | Cleared on next access |
| **Remove** | Immediate ⚡ | No ✗ | Cleared on next access |
| **Change PW** | On re-login | Yes ✓ | Session still valid |
| **Timeout** | Auto ⏱️ | N/A | Expires after hours |

---

## Emergency Logout Procedure

**If user's account is compromised:**

1. **Immediately block the user**:
   ```bash
   python manage_users.py → 5 → john
   ```

2. **Check if still logged in**:
   ```bash
   curl http://localhost:5000/admin/user-status/john
   # Shows blocked: true
   ```

3. **Force new password when unblocked**:
   ```bash
   python manage_users.py → 4 → john
   # Change to secure password
   ```

4. **Unblock to allow new login**:
   ```bash
   python manage_users.py → 6 → john
   ```

---

## How Session Clearing Works

```python
session.clear()  # Removes all session data

# Before:
session = {
    'user': 'john',
    'login_time': '2024-01-21 10:30:00'
}

# After:
session = {}  # Empty!

# Browser effect:
# Set-Cookie: session=; Max-Age=0  ← Cookie deleted
```

---

## Verification

**Is user really logged out?**

```bash
# Try to access protected page
curl http://localhost:5000/ -c cookies.txt

# If redirected to /login with 302 status → ✓ Logged out
# If returns page with 200 status → ✗ Still logged in
```

---

## Notes

- ⚠️ **Cannot logout from API**: Force logout is admin-only for security
- ⚠️ **API endpoints still work**: Data reception endpoints don't require login
- ⚠️ **Only admin can block**: Prevent user from blocking themselves
- ✓ **Blocking is logged**: All force logouts are recorded
- ✓ **Reversible**: Users can be unblocked and re-activated

---

See [LOGOUT_IMPLEMENTATION.md](LOGOUT_IMPLEMENTATION.md) for detailed explanations.

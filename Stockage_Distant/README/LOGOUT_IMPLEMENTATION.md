# Logout Process - Complete Implementation Guide

## How Logout Works (Current Implementation)

### Standard Logout Flow

```
1. User clicks "Logout" button
                ↓
2. GET /logout request sent
                ↓
3. Server logs the event: "User 'username' logged out"
                ↓
4. session.clear() - Removes session['user']
                ↓
5. Browser cookie invalidated
                ↓
6. Redirect to /login
                ↓
7. Next request to protected page → @login_required check fails
                ↓
8. Redirected to /login page again
```

**Code Location**: [utils/webserver.py#L46-L51](utils/webserver.py#L46-L51)

```python
@app.route("/logout")
def logout():
    """Handle user logout"""
    if 'user' in session:
        username = session['user']
        logging.info(f"User '{username}' logged out")
    session.clear()
    return redirect(url_for('login_page'))
```

---

## Force Logout - 5 Methods

### Method 1: Block User (Recommended) ⭐

**What It Does**: Marks user as blocked in `JSON/users.json`. They're immediately logged out and can't login.

**Usage**:
```bash
python manage_users.py
# Select option 5: Block user
```

**Or via API (Admin Only)**:
```bash
curl -X POST http://localhost:5000/admin/block-user/john \
  -H "Cookie: session=<admin_session>"
```

**How It Works**:
```
Block User
    ↓
JSON: {"blocked": true}
    ↓
verify_password() returns False → Can't login
    ↓
@login_required decorator checks is_user_blocked()
    ↓
User logged out immediately on next access
```

**Code Location**: [auth.py#L73-L90](auth.py#L73-L90)

---

### Method 2: Remove User (Permanent)

**What It Does**: Deletes user from system completely.

**Usage**:
```bash
python manage_users.py
# Select option 3: Remove user
```

**Result**: User account is deleted - they can't login anymore.

**Code Location**: [manage_users.py](manage_users.py) - `remove_user()`

---

### Method 3: Change User Password (Forces Re-login)

**What It Does**: Changes user password. They must login again with new password.

**Usage**:
```bash
python manage_users.py
# Select option 4: Change password
```

**Security Benefit**: Forces user to re-authenticate, invalidates stale sessions.

**Code Location**: [auth.py#L49-L57](auth.py#L49-L57)

---

### Method 4: Auto Logout with Session Timeout

**What It Does**: Automatically logs out users after inactivity period (e.g., 8 hours).

**Currently Not Implemented** - To enable:

Add to [auth.py](auth.py) after imports:

```python
from datetime import timedelta

# Session configuration
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)  # 8 hour timeout
app.config['SESSION_COOKIE_SECURE'] = True       # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True     # No JavaScript access
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'    # CSRF protection
```

Then in login_page():

```python
if verify_password(username, password):
    session.permanent = True  # Enable timeout
    session['user'] = username
    # ...
```

Now sessions expire after 8 hours of inactivity.

---

### Method 5: Admin API Endpoints

**Route 1: Block User**
```bash
curl -X POST http://localhost:5000/admin/block-user/username \
  -H "Cookie: session=<admin_session>"
```

Response:
```json
{"status": "success", "message": "User username has been blocked"}
```

**Route 2: Unblock User**
```bash
curl -X POST http://localhost:5000/admin/unblock-user/username \
  -H "Cookie: session=<admin_session>"
```

**Route 3: Check User Status**
```bash
curl http://localhost:5000/admin/user-status/username \
  -H "Cookie: session=<admin_session>"
```

Response:
```json
{
  "username": "username",
  "blocked": false,
  "status": "active"
}
```

**Code Location**: [utils/webserver.py#L279-L330](utils/webserver.py#L279-L330)

---

## Force Logout Implementation Details

### How Blocking Works

**Step 1: Block the User**
```python
# In JSON/users.json
{
  "john": {
    "password": "john_password",
    "blocked": true  ← ✓ Added by block_user()
  }
}
```

**Step 2: Login Check**
```python
def verify_password(username, password):
    users = load_users()
    if username in users:
        # Check if user is blocked
        if users[username].get('blocked', False):
            return False  # ← Login fails
        return users[username].get('password') == password
    return False
```

**Step 3: Access Check**
```python
@login_required
def protected_route():
    # Check if user still valid
    current_user = session.get('user')
    if is_user_blocked(current_user):
        session.clear()  # ← Force logout
        return redirect(url_for('login_page'))
```

---

## Practical Examples

### Example 1: Emergency Logout

User's account compromised? Block them immediately:

```bash
python manage_users.py
# Enter: 5 (Block user)
# Enter: john
# ✓ User john has been blocked!
```

John will be logged out on their next page access.

---

### Example 2: Admin Blocking via API

```python
import requests

session = requests.Session()

# Admin logs in
session.post('http://localhost:5000/login', data={
    'username': 'admin',
    'password': 'admin123'
})

# Admin blocks user
response = session.post('http://localhost:5000/admin/block-user/john')
print(response.json())
# {'status': 'success', 'message': 'User john has been blocked'}

# Check user status
response = session.get('http://localhost:5000/admin/user-status/john')
print(response.json())
# {'username': 'john', 'blocked': true, 'status': 'blocked'}
```

---

### Example 3: Unblock User

```bash
python manage_users.py
# Enter: 6 (Unblock user)
# Shows blocked users list
# Enter: john
# ✓ User john has been unblocked!
```

---

## Logout Behavior Summary

| Action | Effect | Session | Login Possible |
|--------|--------|---------|---|
| Click Logout | Session cleared | ❌ Invalid | ✓ Yes (with password) |
| Block User | User marked blocked | ❌ Cleared on next access | ✗ No |
| Remove User | User deleted | ❌ Cleared on next access | ✗ No |
| Password Change | Requires re-login | ⚠️ Still valid until expires | ✓ Yes (with new password) |
| Session Timeout | Inactive 8+ hours | ❌ Expires | ✓ Yes (with password) |

---

## Security Verification

### Check User Status
```bash
python manage_users.py
# Select 7: Show user status
```

Output:
```
Username             | Status
admin                | ACTIVE
john                 | BLOCKED
alice                | ACTIVE
```

### Log Logout Events

Check application logs for logout events:

```python
# In logs, you'll see:
logging.info(f"User '{username}' logged out")
logging.warning(f"User '{username}' is blocked")
logging.critical(f"Admin '{admin}' blocked user '{username}'")
```

---

## Testing Logout Methods

### Test 1: Standard Logout
```bash
# Step 1: Login
curl -c cookies.txt http://localhost:5000/login \
  -d "username=admin&password=admin123"

# Step 2: Verify logged in (should work)
curl -b cookies.txt http://localhost:5000/

# Step 3: Logout
curl -b cookies.txt http://localhost:5000/logout

# Step 4: Verify logged out (should redirect to /login)
curl -b cookies.txt http://localhost:5000/
```

### Test 2: Force Block
```bash
# Block a user
python manage_users.py
# Select 5, then enter username

# Try to login as blocked user
curl http://localhost:5000/login \
  -d "username=john&password=john_password"
# Should fail with "Invalid username or password"
```

### Test 3: Unblock
```bash
# Unblock
python manage_users.py
# Select 6, then enter username

# Try to login again
curl http://localhost:5000/login \
  -d "username=john&password=john_password"
# Should succeed
```

---

## Files Modified/Created

| File | Change | Purpose |
|------|--------|---------|
| [auth.py](auth.py) | Added block_user() | Force logout functionality |
| [auth.py](auth.py) | Updated verify_password() | Check if blocked |
| [auth.py](auth.py) | Updated @login_required | Check if blocked on access |
| [utils/webserver.py](utils/webserver.py) | Added admin routes | API force logout |
| [manage_users.py](manage_users.py) | Added block/unblock menu | CLI force logout |

---

## Quick Reference

```bash
# Standard logout - User clicks button
GET /logout → Redirect to /login

# Force logout - Admin via CLI
python manage_users.py → 5 → username

# Force logout - Admin via API
POST /admin/block-user/username

# Check status
GET /admin/user-status/username

# Unblock
POST /admin/unblock-user/username
```

---

## Best Practices

✅ **Do**:
- Log all logout events
- Use block_user() for emergencies
- Check user status regularly
- Unblock user when safe again

❌ **Don't**:
- Block admin user unless necessary
- Leave users blocked indefinitely
- Forget to log why a user was blocked
- Use password change as primary logout method

---

## Troubleshooting

**Q: Blocked user can still access site?**
A: They were already logged in. Session expires on:
- Next page reload
- Next request to protected route
- Session timeout (if configured)

**Q: Can't unblock user?**
A: Make sure username is correct. Check with:
```bash
python manage_users.py → 7 (Show status)
```

**Q: User blocked but still in JSON?**
A: Yes, they're still in the system but marked `"blocked": true`. 
- To completely remove, use option 3: Remove user
- To re-enable, use option 6: Unblock user

---

## Implementation Status

✅ **Implemented**:
- Standard logout
- Block/unblock users
- Admin API routes
- CLI management
- Logout logging
- Session validation

⏳ **Optional**:
- Session timeout (8 hours)
- Redis session store
- Rate limiting on login
- 2FA/MFA support


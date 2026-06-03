# Login System Implementation Guide

## Overview

A secure login system has been added to protect all web pages while keeping API endpoints open for data reception.

### What's Protected
✅ All web pages (/, /map, /cam, /battery, etc.) - **Require login**
✅ /events endpoint - **Requires login**

### What's Open
✅ API data reception endpoints (metadata/image POST routes) - **No authentication needed**

---

## Setup Instructions

### 1. **Default Credentials**
The system comes with a default test user:
- **Username**: `admin`
- **Password**: `admin123`

**⚠️ IMPORTANT**: Change these credentials immediately in production!

### 2. **Manage Users**

Run the user management script:
```bash
python manage_users.py
```

This interactive script allows you to:
- List all users
- Add new users
- Remove users
- Change passwords

### 3. **Configuration**

**Change the secret key** in [auth.py](auth.py#L13):
```python
app.secret_key = 'your-secret-key-change-this-in-production'
```

Change this to a random, secure string for production use.

---

## How It Works

### Authentication Flow
1. User visits any protected page (e.g., `/`)
2. If not logged in → Redirected to `/login`
3. User enters credentials
4. On successful login → Session is created → Redirected to requested page
5. Session stored in browser cookies (secure)

### Logout
- Click logout button on any page, or visit `/logout`
- Session is cleared
- User is redirected to login page

### API Access
The following endpoints remain **publicly accessible** for data reception:
- `POST {METADATA_PATH}` - Receive metadata
- `POST {IMAGE_PATH}` - Receive images
- `POST {TEST_PATH}` - Test endpoint

These paths are configured in `JSON/settings.json`

---

## File Structure

```
├── auth.py                    # Authentication logic
├── manage_users.py            # User management CLI
├── JSON/users.json            # User credentials (auto-created)
└── templates/
    └── login.html             # Login page
```

---

## Security Notes

### Current Implementation
- ✅ Session-based authentication
- ✅ Login page with user/password
- ✅ Logout functionality
- ✅ Protected routes with @login_required decorator
- ✅ Open API endpoints for data reception

### Production Recommendations

1. **Password Hashing**
   Install and use bcrypt for secure password storage:
   ```bash
   pip install bcrypt
   ```
   
   Update [auth.py](auth.py) to use bcrypt:
   ```python
   import bcrypt
   
   def hash_password(password):
       return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
   
   def verify_password(username, password):
       users = load_users()
       if username in users:
           return bcrypt.checkpw(password.encode(), users[username]['password'].encode())
       return False
   ```

2. **HTTPS**
   - Use HTTPS in production
   - Set secure session cookies:
   ```python
   app.config.update(
       SESSION_COOKIE_SECURE=True,
       SESSION_COOKIE_HTTPONLY=True,
       SESSION_COOKIE_SAMESITE='Lax'
   )
   ```

3. **Session Timeout**
   Add session timeout configuration:
   ```python
   from datetime import timedelta
   
   app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
   ```

4. **Rate Limiting**
   Consider adding rate limiting to login endpoint to prevent brute force attacks.

5. **Change Secret Key**
   Generate a secure random key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

---

## API Integration Example

Your external devices/emitters can still POST data without authentication:

```bash
# Metadata endpoint (no auth needed)
curl -X POST http://your-server:port/api/metadata \
  -d "IMG.TYPE=jpeg&IMG.WIDTH=640&..."

# Image endpoint (no auth needed)
curl -X POST http://your-server:port/api/image \
  --data-binary @image.jpg
```

---

## Troubleshooting

### "No users found" error
- Check that `JSON/users.json` exists
- Run `python manage_users.py` to add a user

### "Invalid username or password"
- Ensure username and password are correct
- Reset by editing `JSON/users.json` directly or using manage_users.py

### Logout not working
- Check browser cookie settings
- Verify session configuration in [auth.py](auth.py)

---

## Routes Summary

| Route | Method | Protected | Purpose |
|-------|--------|-----------|---------|
| `/login` | GET/POST | ❌ | Login page |
| `/logout` | GET | ✅ | Logout (clears session) |
| `/` | GET | ✅ | Home page |
| `/image/<id>` | GET | ✅ | Image viewer |
| `/map` | GET | ✅ | Map view |
| `/cam` | GET | ✅ | Camera list |
| `/battery/<id>/graph` | GET | ✅ | Battery graph |
| `/battery/<id>/data` | GET | ✅ | Battery data |
| `/events` | GET | ✅ | Server-Sent Events |
| `{METADATA_PATH}` | POST | ❌ | API: Receive metadata |
| `{IMAGE_PATH}` | POST | ❌ | API: Receive images |

---

## Next Steps

1. ✅ Test login with `admin` / `admin123`
2. ✅ Add your own users with `python manage_users.py`
3. ✅ Update `app.secret_key` in [auth.py](auth.py#L13)
4. ✅ (Optional) Implement password hashing with bcrypt
5. ✅ (Optional) Add HTTPS and session security settings
6. ✅ Test API endpoints still work without authentication

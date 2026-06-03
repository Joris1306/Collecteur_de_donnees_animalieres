# Login System - Quick Reference Card

## 🚀 Get Started in 30 Seconds

```bash
# 1. Check default user works
# Visit: http://localhost:PORT/
# Username: admin
# Password: admin123

# 2. Add your own users
python manage_users.py

# 3. Change the secret key in auth.py (line 13)
app.secret_key = 'your-random-secret-key'
```

---

## 📋 What's Protected vs Open

| Route | Status | Purpose |
|-------|--------|---------|
| `/login` | 🔓 Open | Login form |
| `/logout` | 🔓 Open | Logout (accessible) |
| `/` | 🔒 Protected | Home page |
| `/map` | 🔒 Protected | Map view |
| `/cam` | 🔒 Protected | Camera list |
| `/battery/*` | 🔒 Protected | Battery stats |
| `/events` | 🔒 Protected | Live updates |
| `POST /api/metadata` | 🔓 Open | Receive device data |
| `POST /api/image` | 🔓 Open | Receive images |

---

## 🎯 Common Tasks

### Add a New User
```bash
python manage_users.py
# Select: 2. Add new user
# Follow prompts
```

### Change Password
```bash
python manage_users.py
# Select: 4. Change password
# Enter old and new password
```

### Remove a User
```bash
python manage_users.py
# Select: 3. Remove user
# Confirm deletion
```

### List All Users
```bash
python manage_users.py
# Select: 1. List users
```

### Edit Users Directly
```bash
# Edit JSON/users.json in your editor
nano JSON/users.json
```

---

## 🔧 Configuration

### Secret Key (auth.py)
```python
# Change this to a random value
app.secret_key = 'your-secret-key-here'
```

**Generate secure key:**
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Add Logout Button to Pages
```html
<a href="{{ url_for('logout') }}">Logout</a>
```

### Display Logged-In User
```html
<span>{{ session.get('user') }}</span>
```

---

## 📂 Files Reference

| File | Purpose | Status |
|------|---------|--------|
| `auth.py` | Authentication logic | ✅ NEW |
| `manage_users.py` | User management CLI | ✅ NEW |
| `JSON/users.json` | User credentials | ✅ NEW |
| `templates/login.html` | Login page | ✅ NEW |
| `utils/webserver.py` | Flask routes | ✅ MODIFIED |
| `LOGIN_SETUP.md` | Setup guide | ✅ NEW |
| `AUTH_CUSTOMIZATION.md` | Advanced options | ✅ NEW |
| `IMPLEMENTATION_SUMMARY.md` | Overview | ✅ NEW |
| `VISUAL_GUIDE.md` | Diagrams | ✅ NEW |

---

## ✅ Verification Checklist

- [ ] Default login works (admin/admin123)
- [ ] Protected pages redirect to /login when not logged in
- [ ] Logout clears session
- [ ] API endpoints still receive data (no auth required)
- [ ] Users can be added via manage_users.py
- [ ] Secret key changed from default

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "ModuleNotFoundError: No module named 'auth'" | Check auth.py is in root directory |
| Login page shows blank | Check templates/login.html exists |
| Users not persisting | Check JSON/users.json has write permissions |
| API not receiving data | Make sure API routes DON'T have @login_required |
| Can't login | Default is admin/admin123; verify in users.json |

---

## 🔐 Security Checklist

- [ ] Secret key changed (not default)
- [ ] Users have strong passwords
- [ ] Removed default admin user (production only)
- [ ] API endpoints confirmed open for devices
- [ ] HTTPS enabled (production only)
- [ ] Session timeout configured (production only)
- [ ] Password hashing enabled (production only)

---

## 📊 System Status

✅ **Implemented**: Session-based login
✅ **Implemented**: Protected web routes  
✅ **Implemented**: Open API endpoints
✅ **Implemented**: User management

🔷 **Recommended (Production)**:
- Password hashing
- HTTPS/SSL
- Session timeout
- Rate limiting

---

## 🔗 Documentation

```
├── LOGIN_SETUP.md          ← Start here
├── IMPLEMENTATION_SUMMARY.md ← What was done
├── AUTH_CUSTOMIZATION.md   ← Advanced features
├── VISUAL_GUIDE.md         ← Architecture diagrams
└── test_login_system.sh    ← Run tests
```

---

## 💡 Pro Tips

1. **Test API still works**:
   ```bash
   curl -X POST http://localhost:5000/api/metadata -d "test=data"
   # Should work without login
   ```

2. **Check logs for auth events**:
   ```
   User 'admin' logged in successfully
   User 'admin' logged out
   Failed login attempt for user 'john'
   ```

3. **Back up users.json**:
   ```bash
   cp JSON/users.json JSON/users.json.backup
   ```

4. **Use strong passwords**:
   ```
   ✓ Good: P@ssw0rd!2024#Secure
   ✗ Bad: admin123
   ```

---

## 🚀 Next Steps

1. **Test the system**
   - Login with admin/admin123
   - Try accessing protected pages
   - Verify API endpoints work

2. **Customize for production**
   - Change secret key
   - Add your users
   - Remove default admin user
   - Enable password hashing
   - Set up HTTPS

3. **Integrate with UI**
   - Add logout button to pages
   - Display username in navbar
   - Use navbar_example.html as reference

4. **Monitor and maintain**
   - Check login logs
   - Rotate passwords periodically
   - Back up users.json
   - Update security settings as needed

---

## 📞 Support Resources

- **Flask Docs**: https://flask.palletsprojects.com/
- **Session Docs**: https://flask.palletsprojects.com/sessions/
- **Security**: https://owasp.org/www-community/attacks/Session_hijacking_attack

---

**Ready to go! 🎉**

Start with: `python manage_users.py`

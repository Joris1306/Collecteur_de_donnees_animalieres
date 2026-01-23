# Login System - Visual Guide

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      FLASK APPLICATION                          │
└─────────────────────────────────────────────────────────────────┘
         │                              │
         │                              │
    ┌────▼────────────────────┐   ┌────▼──────────────────────────┐
    │   WEB PAGES (Protected) │   │   API ENDPOINTS (Open)         │
    ├────────────────────────┤   ├────────────────────────────────┤
    │ ✓ Require Login        │   │ ✗ No Authentication           │
    │ ✓ Session Cookie       │   │ ✗ Open to all devices         │
    │ ✓ User verification    │   │ ✗ Receive data from emitters   │
    │                        │   │                                │
    │ /login (public)        │   │ POST /api/metadata             │
    │ /logout (public)       │   │ POST /api/image                │
    │ / (protected)          │   │ POST /api/test                 │
    │ /map (protected)       │   │                                │
    │ /cam (protected)       │   │                                │
    │ /battery/*/graph       │   │                                │
    │ /battery/*/data        │   │                                │
    │ /events (SSE)          │   │                                │
    └────────────────────────┘   └────────────────────────────────┘
         │                              │
         │                              │
    ┌────▼──────────────────┐   ┌──────▼──────────────────────┐
    │   auth.py             │   │   webserver.py             │
    │   ───────────────     │   │   ──────────────            │
    │ • verify_password()   │   │ • @login_required          │
    │ • is_logged_in()      │   │ • login_page()             │
    │ • @login_required     │   │ • logout()                 │
    │ • Session handling    │   │ • [Protected routes]       │
    └────────────────────────┘   └────────────────────────────┘
         │                              │
         │                              │
    ┌────▼──────────────────┐   ┌──────▼──────────────────────┐
    │  JSON/users.json      │   │   SQL Database             │
    │  ─────────────────    │   │   ──────────────           │
    │ {                     │   │ • Images                   │
    │  "admin": {           │   │ • Camera data              │
    │    "password": "..."  │   │ • Battery info             │
    │  }                    │   │ • Timestamps               │
    │ }                     │   │                            │
    └──────────────────────┘   └────────────────────────────┘
```

---

## Login Flow Diagram

```
BROWSER                           SERVER
  │                                 │
  ├──── Request: GET / ────────────>│
  │                                 │
  │<──────── 302 Redirect ──────────┤ (Not logged in)
  │         to /login               │
  │                                 │
  ├──── Request: GET /login ──────->│
  │                                 │
  │<────── Response: Login.html ────┤
  │   (Form with username/password) │
  │                                 │
  │ [User enters: admin/admin123]   │
  │                                 │
  ├──── POST /login ───────────────>│
  │   (username, password)          │
  │                                 │
  │                        ┌────────┐
  │                        │ Verify │
  │                        │ auth   │
  │                        └────────┘
  │                                 │
  │<──── 302 Redirect to / ────────┤ (Success)
  │    Set-Cookie: session=...      │
  │                                 │
  ├──── Request: GET / ────────────>│
  │     (with session cookie)       │
  │                                 │
  │<────── Response: index.html ────┤
  │    (Protected page, rendered)   │
  │                                 │
  ├──── Request: GET /logout ──────>│
  │                                 │
  │<──── 302 Redirect to /login ───┤ (Session cleared)
  │    Set-Cookie: session=clear    │
  │                                 │
```

---

## API Data Flow (No Authentication)

```
EXTERNAL DEVICE                    SERVER
  │                                 │
  ├──── POST /api/metadata ───────->│
  │   "IMG.TYPE=jpeg..."            │
  │                                 │
  │                        ┌────────┐
  │                        │ Receive│
  │                        │ data   │
  │                        └────────┘
  │                                 │
  │<──── Response: "OK" ────────────┤
  │                                 │
  ├──── POST /api/image ───────────>│
  │   [binary image data]           │
  │                                 │
  │                        ┌────────┐
  │                        │ Store  │
  │                        │ image  │
  │                        └────────┘
  │                                 │
  │<──── Response: "OK" ────────────┤
  │                                 │
  [No authentication needed ✓]      │
```

---

## File Relationships

```
┌─────────────────────────────────────────────────────────────┐
│                  utlitaires.py                              │
│              (Flask app initialization)                     │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
    ┌────▼────┐  ┌───▼───┐  ┌───▼──────┐
    │ auth.py │  │ app.py│  │webserver.│
    │ (NEW)   │  │       │  │  py      │
    └────┬────┘  └───┬───┘  │(MODIFIED)│
         │           │      └──────────┘
         │      ┌────▼──────────────┐
         │      │  utils/           │
         │      │  sql_db.py        │
         │      │  data_receiver.py │
         │      │  web_map.py       │
         │      └───────────────────┘
         │
    ┌────▼──────────────┐
    │ JSON/             │
    │ users.json (NEW)  │
    │ settings.json     │
    │ config.json       │
    └───────────────────┘
         │
    ┌────▼──────────────────┐
    │ templates/            │
    │ login.html (NEW)      │
    │ index.html            │
    │ map.html              │
    │ cam.html              │
    │ battery_graph.html    │
    └───────────────────────┘
         │
    ┌────▼──────────────┐
    │ Database (SQLite) │
    │ app.db            │
    └───────────────────┘
```

---

## Request Routing

```
┌─────────────────────────────────────────┐
│ HTTP Request arrives                    │
└──────────────────┬──────────────────────┘
                   │
                   ▼
        ┌──────────────────────┐
        │ Is it a protected    │
        │ route?               │
        └──────┬────────────────┘
               │
        ┌──────┴──────┐
       YES             NO
        │              │
        ▼              ▼
    ┌────────────┐  ┌──────────────┐
    │ Has valid  │  │ Serve        │
    │ session?   │  │ response     │
    └─┬──────┬──┘  │ (login page, │
      │      │     │  API data)   │
     YES    NO     └──────────────┘
      │      │
      │      ▼
      │  ┌──────────────┐
      │  │ Redirect to  │
      │  │ /login       │
      │  └──────────────┘
      │
      ▼
    ┌──────────────┐
    │ Serve        │
    │ page/data    │
    └──────────────┘
```

---

## User Management

```
┌─────────────────────────────────────────┐
│ python manage_users.py                  │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┼──────────┐
        │          │          │
        ▼          ▼          ▼
    ┌────────┐ ┌─────────┐ ┌──────┐
    │ List   │ │ Add     │ │Remove│
    │ Users  │ │ User    │ │User  │
    └────────┘ └────┬────┘ └──────┘
                    │
                    ▼
            ┌──────────────┐
            │ Update       │
            │ users.json   │
            └──────────────┘
                    │
                    ▼
            ┌──────────────┐
            │ Password     │
            │ Change       │
            └──────────────┘
```

---

## Session Management

```
LOGIN SUCCESS:
┌──────────────────────┐
│ session['user']      │
│ = 'admin'            │
│                      │
│ (stored in cookie)   │
└──────────────────────┘

EACH REQUEST:
Browser sends:
Cookie: session=<encrypted_token>
           │
           ▼
    ┌────────────────┐
    │ Flask decodes  │
    │ session cookie │
    └────┬───────────┘
         │
         ▼
    ┌────────────────────┐
    │ Check if           │
    │ session['user']    │
    │ exists             │
    └────┬──────┬────────┘
         │      │
        YES    NO
         │      │
         ▼      ▼
      Allow   Redirect
      Access  to /login

LOGOUT:
┌──────────────────┐
│ session.clear()  │
└────┬─────────────┘
     │
     ▼
Set-Cookie: 
  session=; 
  Max-Age=0
  (Delete cookie)
```

---

## Security Layers

```
Layer 1: Route Protection
    ┌───────────────────────────────────┐
    │ @login_required decorator         │
    │ Checks session['user'] exists      │
    └───────────────────────────────────┘

Layer 2: Session Validation
    ┌───────────────────────────────────┐
    │ Flask validates session cookie    │
    │ Prevents tampering with secret_key│
    └───────────────────────────────────┘

Layer 3: Credential Verification
    ┌───────────────────────────────────┐
    │ verify_password() checks          │
    │ username + password against JSON  │
    └───────────────────────────────────┘

Layer 4: API Endpoint Separation
    ┌───────────────────────────────────┐
    │ API routes have NO @login_required │
    │ Designed for external devices     │
    └───────────────────────────────────┘

Additional (Production):
    ┌───────────────────────────────────┐
    │ • Password hashing (bcrypt)       │
    │ • HTTPS/SSL                       │
    │ • Secure session cookies          │
    │ • Session timeout                 │
    │ • Rate limiting on login          │
    └───────────────────────────────────┘
```

---

## Configuration Files

```
JSON/users.json
───────────────
{
  "admin": {
    "password": "admin123"
  },
  "john": {
    "password": "john_pass"
  }
}

auth.py
───────
app.secret_key = 'your-secret-key'
  ↓
  Flask uses this to encrypt
  session cookies

utils/webserver.py
──────────────────
@app.route("/")
@login_required
def index():
  ↓
  Decorator checks session
  Redirects to /login if needed
```

---

## Summary

✅ **Protected**: All web pages require login
✅ **Open**: API endpoints accept data from anyone
✅ **Secure**: Session-based authentication with cookies
✅ **Manageable**: User management via manage_users.py
✅ **Flexible**: Easy to customize and extend

This design separates **web interface access** (protected) from **data ingestion** (open), perfect for IoT/device data collection scenarios.

# Logout Process - Visual Reference

## Standard Logout Flow

```
┌─────────────────────────┐
│  User Clicks Logout     │
│  Button on Page         │
└────────────┬────────────┘
             │
             ▼
    ┌────────────────┐
    │  GET /logout   │
    └────────┬───────┘
             │
             ▼
    ┌──────────────────────┐
    │  Server executes:    │
    │  - Log event         │
    │  - session.clear()   │
    │  - Redirect /login   │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Browser:            │
    │  - Delete cookie     │
    │  - Follow redirect   │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  User at /login      │
    │  ✓ Logged out        │
    └──────────────────────┘
```

---

## Force Logout (Block User) Flow

```
┌─────────────────────────┐
│  Admin Action:          │
│  Block user "john"      │
│  (CLI or API)           │
└────────────┬────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Update JSON/users.  │
    │  json:               │
    │  "blocked": true     │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  John is still       │
    │  logged in (has old  │
    │  session cookie)     │
    └────────┬─────────────┘
             │
             │ John makes next request
             │ (any protected page)
             ▼
    ┌──────────────────────┐
    │  @login_required     │
    │  decorator runs:     │
    │  1. Check: Has       │
    │     session['user']? │
    │     → Yes: 'john'    │
    │  2. Check:           │
    │     is_user_blocked? │
    │     → Yes!           │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Server executes:    │
    │  - session.clear()   │
    │  - Log "is blocked"  │
    │  - Redirect /login   │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  John is NOW logged  │
    │  out ✓               │
    └────────┬─────────────┘
             │
             │ John tries to login
             ▼
    ┌──────────────────────┐
    │  verify_password():  │
    │  1. Load users.json  │
    │  2. Check blocked?   │
    │     → Yes!           │
    │  3. Return False     │
    └────────┬─────────────┘
             │
             ▼
    ┌──────────────────────┐
    │  Login fails:        │
    │  "Invalid username   │
    │   or password"       │
    └──────────────────────┘
```

---

## Force Logout Decision Tree

```
                    Need to logout user?
                           │
           ┌───────────────┼───────────────┐
           │               │               │
        User          Account            Need
      already        Security           password
      logged in      Issue?             reset?
           │               │               │
          YES              │               │
           │         ┌─────┴─────┐        │
           │        YES          NO       │
           │         │            │      YES
           │         │            │       │
           ▼         ▼            ▼       ▼
    ┌─────────┐ ┌──────────┐ ┌──────┐ ┌─────────┐
    │  BLOCK  │ │ REMOVE   │ │ UNBLOCK│ │CHANGE   │
    │  USER   │ │ USER     │ │       │ │PASSWORD │
    │(Force   │ │(Permanent│ │(If    │ │         │
    │ logout) │ │ delete)  │ │ needed)│ │(Re-auth)│
    └─────────┘ └──────────┘ └──────┘ └─────────┘
         │            │          │        │
         ▼            ▼          ▼        ▼
    IMMEDIATE    IMMEDIATE   Can login  NEXT
    LOGOUT        LOGOUT      again      LOGIN
    
    Best for:   Best for:    Best for:  Best for:
    - Security  - Employee   - Mistake  - Password
      breach      left       blocking   reset
    - Quick      - Clean     - Testing  - Credential
      action      up                      change
```

---

## Blocking Mechanism

```
JSON File State:
┌──────────────────────────────┐
│ {                            │
│   "admin": {                 │
│     "password": "...",       │
│     "blocked": false  ← ✓   │
│   },                         │
│   "john": {                  │
│     "password": "...",       │
│     "blocked": true   ← ✗   │
│   }                          │
│ }                            │
└──────────────────────────────┘

What happens:
┌────────────────────┬────────────────────┐
│  Admin (blocked:f) │  John (blocked:t)  │
├────────────────────┼────────────────────┤
│ Can login          │ Cannot login       │
│ Can access pages   │ Logged out on      │
│ ✓ Has access       │ page access        │
│                    │ ✗ No access        │
└────────────────────┴────────────────────┘
```

---

## Session Lifecycle

```
WITHOUT BLOCKING:
┌──────────────────────┐
│ User logs in         │
│ session['user']='j'  │
└──────────┬───────────┘
           │
      ┌────▼────────────────┐
      │ Can access pages ✓  │
      │ (30 min later)      │
      └────┬────────────────┘
           │
      ┌────▼────────────────────────┐
      │ User clicks logout           │
      │ session.clear()              │
      └────┬───────────────────────┘
           │
      ┌────▼──────────────────┐
      │ Logged out ✓          │
      │ Redirect to /login    │
      └───────────────────────┘


WITH BLOCKING:
┌──────────────────────┐
│ User logs in         │
│ session['user']='j'  │
└──────────┬───────────┘
           │
      ┌────▼────────────────────────┐
      │ Can access pages ✓          │
      │ (5 min later)               │
      └────┬───────────────────────┘
           │
      ┌────▼──────────────────────────┐
      │ Admin BLOCKS user              │
      │ JSON: "blocked": true          │
      └────┬───────────────────────────┘
           │
      ┌────▼──────────────────────────┐
      │ User makes next request        │
      │ @login_required checks JSON    │
      │ Finds: blocked=true            │
      └────┬───────────────────────────┘
           │
      ┌────▼──────────────────────────┐
      │ session.clear() forced         │
      │ Logged out immediately ✓       │
      └───────────────────────────────┘
```

---

## Admin Commands

```
┌─────────────────────────────────────┐
│ python manage_users.py              │
├─────────────────────────────────────┤
│ 1. List users                       │
│ 2. Add new user                     │
│ 3. Remove user                      │
│ 4. Change password                  │
│ 5. Block user ← FORCE LOGOUT        │
│ 6. Unblock user                     │
│ 7. Show user status                 │
│ 8. Exit                             │
└─────────────────────────────────────┘
     │
     ▼ Select: 5
┌─────────────────────────────────────┐
│ Block User                          │
│ Username: john                      │
│                                     │
│ User 'john' has been blocked! ✓     │
│ They will be logged out on next     │
│ page access.                        │
└─────────────────────────────────────┘
```

---

## Security Validation Points

```
REQUEST FLOW:

1. POST /login
   └─→ verify_password('john', 'pwd')
       └─→ Check: is_user_blocked('john')?
           ├─ True → Deny login
           └─ False → Check password

2. GET /protected
   └─→ @login_required decorator
       ├─ Check: is_logged_in()?
       │  └─ False → Redirect /login
       └─ Check: is_user_blocked(user)?
          ├─ True → Force logout
          └─ False → Allow access

3. GET /logout
   └─→ session.clear()
   └─→ Redirect /login

4. Password verified by:
   └─→ HMAC signature (secret_key)
       └─→ Prevents tampering
```

---

## Timeline of Force Logout

```
14:30:00 - Admin blocks user
          JSON updated
          Logs: "User 'john' blocked"
                │
14:30:05 - John clicks a page
          Request arrives
          @login_required runs
                │
14:30:05.1 - Check: is_user_blocked('john')?
             Returns: True
                │
14:30:05.2 - session.clear() executed
             Logs: "Access denied: blocked"
                │
14:30:05.3 - Redirect to /login
                │
14:30:06 - John now at login page
          ✓ FORCE LOGOUT COMPLETE
          
Speed: < 1 second from blocking
```

---

## API Endpoints

```
LOGIN & LOGOUT:
  GET  /login             → Show login form
  POST /login             → Authenticate user
  GET  /logout            → Logout user (clear session)

ADMIN (Force Logout):
  POST /admin/block-user/<username>     → Block user
  POST /admin/unblock-user/<username>   → Unblock user
  GET  /admin/user-status/<username>    → Check status

PROTECTED PAGES:
  GET  /                  → @login_required (check blocked)
  GET  /map              → @login_required (check blocked)
  GET  /cam              → @login_required (check blocked)
  etc...

API (ALWAYS OPEN):
  POST /api/metadata     → No auth required
  POST /api/image        → No auth required
```

---

## Force Logout Comparison

```
┌──────────────┬─────────┬──────────┬──────────┬─────────────┐
│ Method       │ Speed   │ Reversib │ Permanent│ Best For    │
├──────────────┼─────────┼──────────┼──────────┼─────────────┤
│ Block        │ ⚡ Immed │ ✓ Yes   │ ✗ No    │ Emergency   │
│ Remove       │ ⚡ Immed │ ✗ No    │ ✓ Yes   │ Off-board   │
│ Change PW    │ ⏱️ Re-lg │ ✓ Yes   │ ✗ No    │ Reset       │
│ Timeout      │ ⏱️ 8h    │ N/A     │ ✗ No    │ Auto logout │
└──────────────┴─────────┴──────────┴──────────┴─────────────┘
```

---

## State Machine: User Blocking

```
        ┌─────────────────┐
        │ User Created    │
        │ blocked: false  │
        └────────┬────────┘
                 │
       ┌─────────▼──────────┐
       │ User logs in       │
       │ Session created    │
       └─────────┬──────────┘
                 │
    ┌────────────┼────────────┐
    │            │            │
    ▼            ▼            ▼
 Can log   Can access    Normal user
 out       protected     behavior
 (normal)  pages (✓)
    │            │            │
    │            └──────┬─────┘
    │                   │
    │           ┌───────▼──────┐
    │           │ Admin blocks │
    │           │ user         │
    │           └───────┬──────┘
    │                   │
    │            ┌──────▼──────────┐
    │            │ blocked: true   │
    │            │ in JSON         │
    │            └───────┬─────────┘
    │                    │
    │           ┌────────▼─────────┐
    │           │ User's next      │
    │           │ request:         │
    │           │ Force logout     │
    │           └────────┬─────────┘
    │                    │
    │           ┌────────▼──────────┐
    │           │ Cannot access     │
    │           │ Cannot login (✗)  │
    │           └────────┬──────────┘
    │                    │
    │           ┌────────▼──────────┐
    │           │ Admin unblocks    │
    │           │ blocked: false    │
    │           └────────┬──────────┘
    │                    │
    └────────────┬───────┘
                 │
         ┌───────▼──────┐
         │ User can log │
         │ in again ✓   │
         └──────────────┘
```

---

## Summary

**Standard Logout**: User clicks logout button
**Force Logout**: Admin blocks user via CLI/API
**Speed**: Force logout is immediate (~100ms)
**Reversible**: Users can be unblocked
**Secure**: Multiple validation layers
**Logged**: All actions recorded

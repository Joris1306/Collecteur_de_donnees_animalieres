# Logout Button - Location Guide

## Where is the Logout Button?

The **Logout button** is now at the **top-right corner** of every page in your application.

### Visual Location

```
┌────────────────────────────────────────────────────┐
│ Data Monitoring System    Logged in as: admin  [Logout] │
└────────────────────────────────────────────────────┘
                                                      ↑
                                                 Logout button here
```

## On Each Page

### 1. Home Page (/)
- **Location**: Top-right navbar
- **Shows**: Your username and logout button
- **Click**: Logout button to logout

### 2. Camera List (/cam)
- **Location**: Top-right navbar
- **Shows**: Your username and logout button
- **Click**: Logout button to logout

### 3. Map (/map)
- **Location**: Top-right navbar
- **Shows**: Your username and logout button
- **Click**: Logout button to logout

### 4. Battery Graph (/battery/*/graph)
- **Location**: Top-right navbar
- **Shows**: Your username and logout button
- **Click**: Logout button to logout

### 5. Map View (/map/submap)
- **Location**: Top-right navbar
- **Shows**: Your username and logout button
- **Click**: Logout button to logout

## Logout Navbar Components

```html
<nav>
  <!-- Left side: Title -->
  <h2>Data Monitoring System</h2>
  
  <!-- Right side: User info + Logout -->
  <div>
    <span>Logged in as: <strong>admin</strong></span>
    <a href="{{ url_for('logout') }}">
      Logout  ← Click here to logout
    </a>
  </div>
</nav>
```

## How to Use

### Click to Logout
1. Look at the top-right corner of any page
2. Click the red **"Logout"** button
3. You will be logged out
4. You will be redirected to the login page

### After Logout
- Session is cleared
- Browser cookie is deleted
- You must login again to access protected pages
- All your session data is removed

## What Happens When You Click Logout

```
Click "Logout" button
    ↓
Send: GET /logout request
    ↓
Server:
  - Logs the event
  - Clears your session
  - Deletes the cookie
    ↓
Redirect: to /login page
    ↓
You are logged out ✓
```

## Styling

The logout button has these properties:
- **Background**: Your theme colors (gradient)
- **Text**: Light color
- **Position**: Top-right of every page
- **Always visible**: On all protected pages
- **Theme**: Matches your system design

## Examples

### Example 1: Logout from Home
1. You're on the home page (/)
2. See navbar at the top
3. Click "Logout" button on the right
4. Redirected to /login

### Example 2: Logout from Map
1. You're viewing the map page
2. See navbar at the top
3. Click "Logout" button on the right
4. Redirected to /login

### Example 3: Logout from Camera List
1. You're viewing cameras
2. See navbar at the top
3. Click "Logout" button on the right
4. Redirected to /login

## Navbar Details

**Left side:**
- Shows: "Data Monitoring System"
- Icon/Title: Your app name
- Always visible

**Right side:**
- Shows: "Logged in as: [your username]"
- Has: "Logout" button
- Matches: Your theme colors
- Clickable: Logout button triggers logout

## Mobile View

On mobile/tablet, the navbar:
- Still appears at the top
- Logout button is accessible
- Responsive design
- Button stays visible

## If Logout Button is Not Showing

✅ **You should see:**
- At the top of every page
- Right side of the navbar
- Shows your username
- Logout link/button

❌ **If missing:**
1. Check you're logged in (should be on protected page)
2. Refresh the page
3. Check browser isn't blocking content
4. Clear browser cache

## Code Location

The logout button HTML is in:
- `templates/index.html`
- `templates/cam.html`
- `templates/map.html`
- `templates/battery_graph.html`
- `templates/index_map.html`

**Pattern:**
```html
<nav>
  <span>Logged in as: {{ session.get('user') }}</span>
  <a href="{{ url_for('logout') }}">Logout</a>
</nav>
```

## Quick Reference

| Feature | Details |
|---------|---------|
| **Location** | Top-right corner of every page |
| **Visible on** | All protected pages |
| **Requires** | Active login session |
| **Action** | GET /logout |
| **Result** | Session cleared, redirected to /login |
| **Speed** | Immediate |
| **Reversible** | No - must login again |

## Keyboard Shortcut

Currently: Click button manually

Future enhancement: Could add keyboard shortcut (e.g., Ctrl+L)

---

**Summary**: The logout button is at the **top-right** of every page, showing your username and a clickable "Logout" link. Click it to logout immediately.

# Theme Integration Guide

## Login Page Theme

✅ The login page now uses your existing `style.css` theme with:
- Dark background gradient matching your system design
- Same color variables (--bg, --text, --muted, --border, etc.)
- Consistent card styling with glass morphism effect
- Responsive design

**No additional changes needed** - the login page automatically uses your theme!

---

## Adding Navbar to Existing Pages

To add the logout button and user info to your existing pages, follow these steps:

### Option 1: Quick Add (Individual Pages)

Add this at the top of your page template `<body>`:

```html
<nav style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02)); backdrop-filter: blur(6px);">
    <h2 style="margin: 0; color: var(--text); font-size: 20px;">Data Monitoring System</h2>
    <div style="display: flex; align-items: center; gap: 20px;">
        <span style="color: var(--muted); font-size: 14px;">
            Logged in as: <strong style="color: var(--text);">{{ session.get('user') }}</strong>
        </span>
        <a href="{{ url_for('logout') }}" style="padding: 10px 16px; background: linear-gradient(180deg, var(--panel2), var(--panel)); color: var(--text); text-decoration: none; border: 1px solid var(--border); border-radius: 12px; cursor: pointer; font-size: 14px;">
            Logout
        </a>
    </div>
</nav>
```

### Option 2: Using Jinja2 Include (Recommended)

See `templates/navbar_example.html` for a reusable navbar snippet.

Add to each template:
```html
{% include 'navbar_example.html' %}
```

### Option 3: Base Template (Best Practice)

Create a `base.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
    <title>{% block title %}Data System{% endblock %}</title>
</head>
<body>
    <!-- Navbar -->
    <nav style="display: flex; justify-content: space-between; align-items: center; padding: 16px 20px; border-bottom: 1px solid var(--border);">
        <h2 style="margin: 0; color: var(--text);">Data Monitoring System</h2>
        <div style="display: flex; align-items: center; gap: 20px;">
            <span style="color: var(--muted);">Logged in as: <strong style="color: var(--text);">{{ session.get('user') }}</strong></span>
            <a href="{{ url_for('logout') }}" style="padding: 10px 16px; background: linear-gradient(180deg, var(--panel2), var(--panel)); color: var(--text); text-decoration: none; border: 1px solid var(--border); border-radius: 12px;">Logout</a>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container">
        {% block content %}{% endblock %}
    </div>
</body>
</html>
```

Then update each page to extend this base:

```html
{% extends "base.html" %}

{% block title %}My Page{% endblock %}

{% block content %}
    <h1>Welcome to My Page</h1>
    <!-- Your content here -->
{% endblock %}
```

---

## Color Variables Available

Your `style.css` defines these CSS variables you can use:

```css
--bg: #0b1220              /* Dark background */
--panel: rgba(255,255,255,.06)    /* Panel background */
--panel2: rgba(255,255,255,.09)   /* Panel background variant */
--text: rgba(255,255,255,.92)     /* Main text color */
--muted: rgba(255,255,255,.62)    /* Muted/secondary text */
--border: rgba(255,255,255,.10)   /* Border color */
--shadow: 0 16px 40px rgba(0,0,0,.35)  /* Shadow */
--radius: 18px                    /* Border radius */
```

Use them in your HTML:

```html
<div style="color: var(--text); border: 1px solid var(--border); background: var(--panel); border-radius: var(--radius);">
    Your content
</div>
```

---

## Current Theme Breakdown

| Element | Color | Variable |
|---------|-------|----------|
| Background | Dark blue/green gradient | body background |
| Text | Light white | `--text` |
| Secondary text | Muted light | `--muted` |
| Cards | Glass effect | `--panel`, `--panel2` |
| Borders | Subtle white | `--border` |

---

## Pages Already Themed

✅ **login.html** - Uses your theme (just updated)
✅ **style.css** - Your design system
✅ **navbar_example.html** - Uses your theme

---

## Pages to Update (Optional)

You may want to add the navbar to these pages for consistency:

- ✓ `index.html` - Home page
- ✓ `map.html` - Map view  
- ✓ `cam.html` - Camera list
- ✓ `battery_graph.html` - Battery graph
- ✓ `index_map.html` - Map variant
- ✓ `error.html` - Error page

Each can include the navbar at the top of the `<body>`.

---

## Quick Copy-Paste Navbar

For faster updates, here's a minimal navbar that fits your theme:

```html
<nav style="padding:16px 20px; border-bottom:1px solid var(--border); background: linear-gradient(180deg, rgba(255,255,255,.05), rgba(255,255,255,.02)); display:flex; justify-content:space-between; align-items:center; gap:20px;">
  <h2 style="margin:0; color:var(--text);">Data Monitoring System</h2>
  <div style="display:flex; gap:20px; align-items:center;">
    <span style="color:var(--muted); font-size:14px;">{{ session.get('user') }}</span>
    <a href="{{ url_for('logout') }}" style="padding:10px 16px; background:linear-gradient(180deg, var(--panel2), var(--panel)); color:var(--text); text-decoration:none; border:1px solid var(--border); border-radius:12px; font-size:14px;">Logout</a>
  </div>
</nav>
```

---

## Testing

After updating pages:

1. **Login** with admin/admin123
2. **Check navbar** appears at top
3. **Verify colors** match your theme
4. **Test logout** button works
5. **Check mobile** responsiveness

---

## Notes

- ✅ Login page theme is complete
- ✅ CSS variables are available for reuse
- ✅ Navbar example provided
- ✓ Optional: Update existing templates to add navbar
- ✓ Optional: Create base.html for full consistency

The login page will now seamlessly blend with your existing design system!

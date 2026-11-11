# 🎒 CampusFind — Campus Lost & Found Portal

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-4.x-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-CDN-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Auth_Only-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

**A full-stack Django web application for reporting, searching, and recovering lost items on campus.**

*Built as a college-level educational project demonstrating MVT architecture, dual-database design, and secure authentication.*

</div>

---

## 📖 About the Project

**CampusFind** is a Campus Lost & Found Portal where students can:
- **Report** lost or found items with photos, category, and location
- **Search & Browse** all active reports with filters
- **Contact** item reporters securely through masked email links
- **Manage** their own reports (edit, delete, mark as resolved)
- **Admins** can moderate all reports (approve, reject, resolve, delete)

> **Why two databases?**  
> Django's built-in authentication system (login, sessions, passwords) *requires* a relational database. We use **SQLite** for that — zero configuration needed for a college project.  
> All item reports are stored in **MongoDB Atlas** because items are documents with flexible fields (a lost laptop has different details than a lost water bottle). MongoDB's document model fits this naturally.  
> This design pattern is called **Polyglot Persistence** — using the right database for each job.

---

## 🏗️ Architecture

### MVT (Model-View-Template) Pattern

```
Browser Request
      │
      ▼
  urls.py  ──► View Function (views.py)
                    │           │
                    ▼           ▼
              models.py     forms.py
           (ReportService)  (Validation)
                    │
          ┌─────────┴──────────┐
          ▼                    ▼
     SQLite DB           MongoDB Atlas
   (auth_user,          (item_reports
    sessions)            collection)
          │
          └─────────► Template (.html)
                            │
                            ▼
                      HTML Response
```

### Dual-Database Design

| Database | Engine | Stores |
|----------|--------|--------|
| **SQLite** (`db.sqlite3`) | Django ORM | Users, Sessions, Auth tokens |
| **MongoDB Atlas** | PyMongo (direct) | Item reports (documents) |

**How they link:** When a user reports an item, `reporter_id` (Django user PK) and `reporter_username` are saved inside the MongoDB document. This creates a soft reference between the two stores.

### MongoDB Document Structure

```json
{
  "_id": "ObjectId('64a3f...')",
  "title": "Lost Blue Backpack",
  "description": "Nike backpack with laptop inside, left in Library Block B",
  "item_type": "lost",
  "category": "bags",
  "location": "Library",
  "status": "approved",
  "reporter_id": 3,
  "reporter_username": "alice2024",
  "reporter_email": "alice@college.edu",
  "image_path": "items/uuid-filename.jpg",
  "created_at": "2026-11-01T10:30:00",
  "updated_at": "2026-11-01T10:30:00"
}
```

---

## ✨ Features

### 👤 Guest (Not Logged In)
- Browse all **approved** lost & found items
- Search by keyword, type (lost/found), category, location
- View item details (reporter contact is hidden)

### 🎓 Student (Logged In)
- Everything a Guest can do, **plus:**
- Report a lost or found item (with optional photo upload)
- Contact the reporter via secure masked email link
- View personal dashboard (`My Reports`)
- Edit, delete, or mark their own reports as resolved

### 🛡️ Admin (Staff User)
- Full student access, **plus:**
- Access the Admin Portal (`/portal-admin/`)
- Approve or reject pending reports
- Resolve or delete any report on the platform
- View all reports across all users

---

## 🛠️ Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.12 | Core language |
| **Django** | 5.1 | Web framework (MVT) |
| **PyMongo** | 4.x | MongoDB driver (direct, no ORM) |
| **MongoDB Atlas** | Cloud | Item reports document store |
| **SQLite** | Built-in | Django auth & sessions |
| **Pillow** | 13.x | Image upload validation & processing |
| **python-dotenv** | Latest | Environment variable management |
| **certifi** | Latest | TLS certificate bundle for Atlas (Windows) |
| **dnspython** | Latest | Resolves `mongodb+srv://` DNS SRV records |
| **Tailwind CSS** | CDN | Utility-first responsive styling |
| **Lucide Icons** | CDN | Clean SVG icon set |

---

## 📂 Project Structure

```
Lost and Found/
│
├── manage.py                        # Django project runner
├── requirements.txt                 # All Python dependencies
├── .env                             # 🔒 Secret config (git-ignored!)
├── .env.example                     # Template for .env
├── .gitignore
├── db.sqlite3                       # SQLite: auth/sessions only
│
├── campus_lost_found/               # Django project package
│   ├── settings.py                  # Config: dotenv, INSTALLED_APPS, MEDIA_*, DB
│   ├── urls.py                      # Root URL router → finder.urls
│   └── wsgi.py / asgi.py
│
└── finder/                          # Main Django application
    ├── db.py                        # MongoDB connection (certifi TLS fix)
    ├── models.py                    # ReportService class (all CRUD operations)
    ├── forms.py                     # StudentRegistrationForm, LoginForm, ItemReportForm
    ├── views.py                     # All view functions (home, auth, reports, admin)
    ├── urls.py                      # All URL patterns
    ├── tests.py                     # 14 automated test cases
    │
    ├── management/
    │   └── commands/
    │       ├── check_mongo.py       # Test Atlas connection
    │       ├── test_mongo_crud.py   # Test full CRUD on Atlas
    │       └── create_admin.py      # Create staff/superuser account
    │
    ├── templates/
    │   ├── 404.html                 # Custom Not Found page
    │   ├── 500.html                 # Custom Server Error page
    │   └── finder/
    │       ├── base.html            # Navbar, footer, messages (all pages inherit)
    │       ├── home.html            # Hero, stats, categories, recent items
    │       ├── item_list.html       # Browse & search with filters
    │       ├── item_detail.html     # Full item info + contact button
    │       ├── report_form.html     # Create & Edit report (shared template)
    │       ├── register.html        # Student registration
    │       ├── login.html           # Student login
    │       ├── my_reports.html      # Personal dashboard
    │       └── admin_dashboard.html # Staff moderation portal
    │
    ├── static/finder/
    │   ├── css/style.css            # Custom styles (supplement Tailwind)
    │   └── js/script.js             # Mobile menu, flash message dismiss
    │
    └── media/items/                 # Uploaded item photos (UUID filenames)
```

---

## 🚀 Setup Instructions

### Prerequisites

- Python 3.10 or higher installed
- A free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) account
- Git installed

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/<your-username>/campus-lost-found.git
cd "campus-lost-found"
```

---

### Step 2 — Create a Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

**What gets installed:**
```
Django==5.1.*
pymongo[srv]==4.*
dnspython
certifi
python-dotenv
Pillow
```

---

### Step 4 — Configure Environment Variables

```bash
# Copy the example file
copy .env.example .env       # Windows
cp .env.example .env         # macOS/Linux
```

Now open `.env` in any text editor and fill in your values:

```env
SECRET_KEY=your-long-random-secret-key-here
DEBUG=True
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=campus_lost_found
```

**How to get `MONGO_URI`:**
1. Log in to [MongoDB Atlas](https://cloud.mongodb.com)
2. Go to your Cluster → **Connect** → **Connect your application**
3. Choose **Python** driver → Copy the connection string
4. Replace `<password>` with your Atlas database user password

> ⚠️ **Never commit `.env` to Git!** It's already in `.gitignore`.

**How to generate `SECRET_KEY`:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

### Step 5 — Run Database Migrations

This creates the SQLite tables for Django's auth system (users, sessions):

```bash
python manage.py migrate
```

---

### Step 6 — Create an Admin User

```bash
python manage.py create_admin
```

This creates a staff/superuser with:
- **Username:** `admin`
- **Password:** `AdminPass@2026`

> You can change the credentials inside `finder/management/commands/create_admin.py`

---

### Step 7 — Verify MongoDB Connection

```bash
python manage.py check_mongo
```

Expected output:
```
[SUCCESS] Connected to MongoDB Atlas
[SUCCESS] Database: campus_lost_found
[SUCCESS] Collection: item_reports
```

---

### Step 8 — Run the Development Server

```bash
python manage.py runserver
```

Open your browser and visit: **http://127.0.0.1:8000/**

---

## 👥 User Roles & Access

| Role | How to Get Access | Key Pages |
|------|------------------|-----------|
| **Guest** | No login needed | `/`, `/items/`, `/items/<id>/` |
| **Student** | Register at `/register/` | `/report/`, `/my-reports/` |
| **Admin** | Created via `create_admin` command | `/portal-admin/` |

**Demo Credentials (Admin):**
```
Username: admin
Password: AdminPass@2026
```

---

## 🔧 Management Commands

These are custom Django management commands located in `finder/management/commands/`:

### `check_mongo`
Tests the MongoDB Atlas connection and prints status.
```bash
python manage.py check_mongo
```

### `test_mongo_crud`
Runs a full Create-Read-Update-Delete cycle on Atlas to verify everything works.
```bash
python manage.py test_mongo_crud
```

### `create_admin`
Creates (or resets) the admin staff user with preset credentials.
```bash
python manage.py create_admin
```

---

## 🧪 Running Tests

The project includes **14 automated test cases** covering all major workflows:

```bash
python manage.py test
```

Expected output:
```
Ran 14 tests in ~30s

OK
```

### What the tests cover:

| Test | What It Checks |
|------|---------------|
| `test_home_page_loads` | Home page returns HTTP 200 |
| `test_item_list_loads` | Browse page returns HTTP 200 |
| `test_register_page_loads` | Register form renders |
| `test_login_page_loads` | Login form renders |
| `test_register_valid_user` | New user creation works end-to-end |
| `test_login_valid_user` | Login + session works |
| `test_login_invalid_password` | Wrong password rejected |
| `test_report_requires_login` | `/report/` redirects if not logged in |
| `test_my_reports_requires_login` | `/my-reports/` redirects if not logged in |
| `test_admin_requires_staff` | `/portal-admin/` blocked for regular users |
| `test_registration_form_valid` | Form accepts valid data |
| `test_registration_form_duplicate_username` | Duplicate username rejected |
| `test_image_upload_validates_pillow` | Non-image file rejected by Pillow |
| `test_invalid_objectid_handled` | Malformed MongoDB ID returns 404 |

---

## 📸 Pages & UI Walkthrough

| Page | URL | Description |
|------|-----|-------------|
| **Home** | `/` | Hero section, live stats from MongoDB, categories grid, 6 most recent approved items |
| **Browse Items** | `/items/` | All approved reports, search bar, filter dropdowns (type/category/location) |
| **Item Detail** | `/items/<id>/` | Full report info, photo, reporter contact (login required to see email) |
| **Report Item** | `/report/` | Form to report a lost/found item with optional image upload |
| **My Reports** | `/my-reports/` | Personal dashboard showing all your reports with status badges |
| **Edit Report** | `/edit/<id>/` | Edit any of your own reports |
| **Register** | `/register/` | Student self-registration |
| **Login** | `/login/` | Email + password login |
| **Admin Portal** | `/portal-admin/` | Staff-only: approve/reject/resolve/delete all reports |

---

## 📜 Git Commit History

| Commit | Phase | Description |
|--------|-------|-------------|
| `f8f0173` | Phase 1 | Project setup: venv, requirements.txt, .gitignore, .env.example |
| `0087001` | Phase 2 | Django project scaffold, finder app, settings with dotenv, placeholder views |
| `12e1292` | Phase 3 | `finder/db.py` MongoDB connection module, `check_mongo` management command |
| `9d57178` | Phase 4 | `finder/models.py` — `ReportService` class with full CRUD |
| `2b6b8f0` | Phase 5 | `base.html` layout, `home.html` with live stats & recent items |
| `2f29f8b` | Phase 6 | Student registration, login, logout with Django's `authenticate()` |
| `4b42663` | Phase 7 | Item report form, Pillow image validation, UUID filename saving |
| `261fce8` | Bugfix | Fix `TemplateSyntaxError` in report_form.html (unclosed `{% if %}`) |
| `d3eb2e6` | Phase 8 | Browse/search page with GET filters: `?q=`, `?type=`, `?category=`, `?location=` |
| `48fe6af` | Phase 9 | Item detail page, certifi TLS fix for Windows + Atlas |
| `aa68bb9` | Phase 10 | My Reports dashboard, edit/delete/resolve own reports |
| `56e8a4e` | Phase 11 | Admin dashboard, `@staff_required` decorator, `create_admin` command |
| `aa2eafb` | Phase 12 | 14 automated tests, custom 404/500 error templates |
| *(this commit)* | Phase 13 | Comprehensive README with architecture docs and interview Q&A |

---

## 🎓 Viva / Interview Q&A

Likely questions from your instructor or examiner, with model answers:

---

### Q1. What is the MVT pattern in Django? How is it different from MVC?

**A:** MVT stands for **Model-View-Template**.
- **Model** — Handles data and business logic. In this project, `ReportService` in `models.py` performs all CRUD operations on MongoDB.
- **View** — The controller/logic layer. `views.py` functions receive HTTP requests, call the Model, and pass data to the Template.
- **Template** — The presentation layer. `.html` files in `finder/templates/` render the final HTML using Django's template language.

In classic MVC, the Controller sits between Model and View. In Django's MVT, the **View plays the Controller role**, and Django's URL dispatcher (router) is what maps URLs to Views. The Template replaces the MVC "View".

---

### Q2. Why did you use two databases (SQLite + MongoDB)? Isn't that complicated?

**A:** This is called **Polyglot Persistence** — using the best database for each specific job.

- **SQLite (via Django ORM):** Django's authentication system (`User`, `Session`, `Permission` models) is built on relational tables. Django ORM *requires* a SQL database to manage these. SQLite requires zero configuration, making it perfect for a development/college project.

- **MongoDB Atlas (via PyMongo):** Item reports are documents — each one can have different fields. A lost laptop might have a serial number field; a lost ID card might have a student roll number. MongoDB's flexible schema handles this naturally. Also, as the platform grows, MongoDB scales horizontally better than SQLite.

The two stores are linked by storing `reporter_id` (Django user primary key) and `reporter_username` inside each MongoDB document.

---

### Q3. What is PyMongo? Why not use Django's ORM with MongoDB?

**A:** **PyMongo** is the official low-level Python driver for MongoDB. It lets us write Python code that sends raw MongoDB commands (like `insert_one`, `find`, `update_one`) directly to the database.

Django's ORM is designed for **relational databases** (tables with fixed schemas). While third-party libraries like `Djongo` or `MongoEngine` try to bridge the gap, they add complexity and often lag behind MongoDB's latest features.

Using PyMongo **directly** in `finder/db.py` and `finder/models.py` gives us:
- Full access to all MongoDB query operators (`$regex`, `$in`, `$set`, etc.)
- No schema mismatch issues
- Clear, explicit database operations

The tradeoff is we write more boilerplate — but it's also more educational.

---

### Q4. What is `@login_required` and how does it work?

**A:** `@login_required` is a Django **decorator** imported from `django.contrib.auth.decorators`. When placed above a view function, it checks if the current user is authenticated before allowing access.

```python
@login_required
def report_item(request):
    ...
```

**How it works internally:**
1. Django checks `request.user.is_authenticated`
2. If `True` → runs the view normally
3. If `False` → redirects to `settings.LOGIN_URL` (we set this to `/login/`)

The original destination URL is preserved as `?next=/report/` so after login the user is sent back to where they wanted to go.

---

### Q5. What is `@staff_required`? Why didn't you use `@login_required` for admin views?

**A:** We wrote a **custom decorator** called `@staff_required` in `views.py`:

```python
def staff_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.is_staff:
            return redirect('home')
        return view_func(request, *args, **kwargs)
    return wrapper
```

`@login_required` only checks *authentication* (is the user logged in?). The admin portal needs *authorization* — checking that the user has **staff privileges** (`is_staff=True`).

A regular student who is logged in must still be blocked from `/portal-admin/`. `@staff_required` handles both: redirect to login if not authenticated, redirect to home if authenticated but not staff.

---

### Q6. What is CSRF and how does Django protect against it?

**A:** **CSRF (Cross-Site Request Forgery)** is an attack where a malicious website tricks a logged-in user's browser into making an unwanted request to your site (e.g., submitting a form on their behalf).

Django's protection:
1. When rendering a form, `{% csrf_token %}` injects a **hidden input** with a random token unique to that user's session.
2. When the form is submitted, Django's middleware (`CsrfViewMiddleware`) checks that the submitted token matches the session token.
3. If they don't match (or if the token is missing), Django returns a **403 Forbidden** error.

We include `{% csrf_token %}` inside every `<form method="POST">` tag in our templates.

---

### Q7. What is an ObjectId in MongoDB? Why do we convert it in Django?

**A:** Every MongoDB document automatically gets a unique `_id` field of type **ObjectId** — a 12-byte BSON value that looks like `64a3f1b2c4e5d6a7b8c9d0e1`.

**The Django URL problem:** Our URL pattern is `/items/<str:item_id>/`. Django receives `item_id` as a Python `str`. But PyMongo's `find_one({"_id": item_id})` won't work — it expects a **BSON ObjectId** object, not a string.

**Solution in `views.py`:**
```python
from bson import ObjectId
from bson.errors import InvalidId

try:
    obj_id = ObjectId(item_id)
except InvalidId:
    raise Http404("Invalid item ID")

report = collection.find_one({"_id": obj_id})
```

We also handle `InvalidId` to return a clean 404 instead of a server crash when someone types a malformed URL.

---

### Q8. How does image upload work? What is Pillow's role?

**A:** Image upload involves three parts:

1. **Form (`forms.py`):** `ItemReportForm` has an `ImageField` with `required=False`. Django validates that the file is an image using its **magic bytes** (not just the extension).

2. **Pillow validation (extra security):** We add a `clean_image()` method that opens the file with `PIL.Image.open()`. If the file is not a real image, Pillow throws an exception and we return a form error. This prevents someone from renaming a `.exe` to `.jpg` and uploading it.

3. **Saving (`views.py`):** We generate a **UUID4 filename** to avoid collisions and path traversal attacks:
   ```python
   ext = image.name.split('.')[-1]
   filename = f"{uuid.uuid4()}.{ext}"
   path = os.path.join(settings.MEDIA_ROOT, 'items', filename)
   ```
   The file is saved to `media/items/` and the relative path is stored in MongoDB.

---

### Q9. What is the difference between `request.GET` and `request.POST`?

**A:**

| | `request.GET` | `request.POST` |
|--|---------------|----------------|
| HTTP Method | GET | POST |
| Data location | URL query string (`?q=laptop`) | Request body (hidden from URL) |
| Use case | Filtering, searching, pagination | Form submissions, login, file upload |
| Bookmarkable? | ✅ Yes | ❌ No |
| Secure for passwords? | ❌ No | ✅ Yes (use HTTPS too) |

In our project:
- **Search filters** use `request.GET` → `/items/?q=laptop&type=lost` (bookmarkable!)
- **Report form, login, register** use `request.POST` → data not shown in URL

---

### Q10. What is `python-dotenv` and why do we use it?

**A:** `python-dotenv` is a library that reads key-value pairs from a `.env` file and loads them as **environment variables** at runtime.

**Why?** We never want to hardcode sensitive values (database passwords, Django secret keys) directly in source code — they would be visible in Git history. Instead:

1. `.env` file (git-ignored) stores real secrets
2. `.env.example` (committed to Git) shows what keys exist without values
3. `settings.py` calls `load_dotenv()` and reads values via `os.environ.get('SECRET_KEY')`

This follows the **12-Factor App** methodology for configuration management.

---

### Q11. What does `certifi` do in this project?

**A:** When connecting to **MongoDB Atlas** (a cloud database) using `mongodb+srv://`, the connection uses **TLS/SSL encryption** to protect data in transit. For TLS to work, your machine needs a bundle of trusted **Certificate Authority (CA) certificates** to verify that it's talking to the real Atlas server and not an imposter.

On **Windows**, Python sometimes uses a different certificate store that doesn't include the CA that Atlas uses. This caused a `TLSV1_ALERT_INTERNAL_ERROR` during connection.

`certifi` ships its own up-to-date CA bundle. We pass it to PyMongo:
```python
import certifi
client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
```

This tells PyMongo to trust `certifi`'s CA list instead of the Windows system store, fixing the TLS error.

---

### Q12. What is `uuid.uuid4()` and why use it for image filenames?

**A:** `uuid.uuid4()` generates a **Universally Unique Identifier** — a random 128-bit number represented as a hex string like `550e8400-e29b-41d4-a716-446655440000`.

**Why use it for image filenames?**

1. **Collision prevention:** If two students upload a file both named `photo.jpg`, the second would overwrite the first. UUIDs are statistically guaranteed to be unique.
2. **Security:** Attackers sometimes try to guess or enumerate uploaded file paths. Random UUIDs are unpredictable.
3. **Path traversal prevention:** A malicious filename like `../../settings.py` can't escape the `media/items/` directory when you ignore the original name entirely.

---

### Q13. How does the search/filter feature work?

**A:** The browse page (`/items/`) uses **GET parameters** in the URL. The HTML form has `method="GET"` so each filter value appears in the URL: `/items/?q=backpack&type=lost&category=bags&location=Library`.

In `views.py`, the `item_list` view builds a **MongoDB query dictionary** progressively:

```python
query = {"status": "approved"}

if q:
    query["$or"] = [
        {"title": {"$regex": q, "$options": "i"}},
        {"description": {"$regex": q, "$options": "i"}},
    ]
if item_type:
    query["item_type"] = item_type
if category:
    query["category"] = category
if location:
    query["location"] = {"$regex": location, "$options": "i"}
```

MongoDB's `$regex` operator does case-insensitive partial matching (similar to SQL `LIKE '%backpack%'`). The `$or` operator lets us search both title and description at once. This query dictionary is passed to `collection.find(query)`.

---

### Q14. What happens when a user logs out? What is a session?

**A:** A **session** is how the web server remembers who you are between requests (HTTP is stateless — each request is independent by default).

**When you log in:**
1. Django calls `login(request, user)` which creates a **session record** in SQLite (`django_session` table)
2. Django sends a **session cookie** (`sessionid`) to the browser
3. On every subsequent request, the browser sends this cookie back
4. Django looks up the cookie in `django_session`, finds your user ID, and sets `request.user`

**When you log out:**
1. Django calls `logout(request)` which **deletes the session record** from SQLite
2. The browser's cookie becomes invalid
3. The next request has no valid session → `request.user` is `AnonymousUser`

This is why `@login_required` works — it checks `request.user.is_authenticated`, which is `False` for anonymous users.

---

### Q15. How would you scale this project for a real production deployment?

**A:** Several improvements for production:

1. **Replace SQLite with PostgreSQL** — SQLite is single-file, not suitable for concurrent writes in production
2. **Use MongoDB Atlas dedicated cluster** — Upgrade from free tier M0 for better performance and backups
3. **Serve media files via cloud storage** — Use AWS S3 or Google Cloud Storage instead of local `media/` folder (doesn't work on multi-server setups)
4. **Add `django-storages`** — Integrates S3/GCS with Django's file handling
5. **Use Gunicorn + Nginx** — Replace Django's `runserver` (development only) with production WSGI server
6. **Set `DEBUG=False`** and configure `ALLOWED_HOSTS` and `STATIC_ROOT` properly
7. **Add rate limiting** on the report submission endpoint to prevent spam
8. **Email verification** on registration so only real college email addresses can register
9. **Add pagination** to the browse and admin pages for large datasets
10. **Environment-specific settings** — Separate `settings/dev.py` and `settings/prod.py`

---

## 🤝 Contributing

This is a college educational project. If you'd like to extend it:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/email-notifications`
3. Commit your changes: `git commit -m 'Add email notification on item match'`
4. Push to the branch: `git push origin feature/email-notifications`
5. Open a Pull Request

---

## 📄 License

This project is built for educational purposes as part of a college web development course.

---

<div align="center">

**Built with ❤️ using Django + MongoDB Atlas**

*CampusFind — Connecting lost items with their owners*

</div>

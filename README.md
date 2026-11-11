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

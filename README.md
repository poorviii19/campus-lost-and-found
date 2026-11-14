# 🎒 CampusFind — Campus Lost & Found Portal

<div align="center">

![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1-092E20?style=for-the-badge&logo=django&logoColor=white)
![MongoDB](https://img.shields.io/badge/MongoDB_Atlas-4.x-47A248?style=for-the-badge&logo=mongodb&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-CDN-06B6D4?style=for-the-badge&logo=tailwindcss&logoColor=white)
![SQLite](https://img.shields.io/badge/SQLite-Auth_Only-003B57?style=for-the-badge&logo=sqlite&logoColor=white)

**A secure, full-stack campus web portal for reporting, tracking, and reuniting lost belongings.**

*Designed with Django's MVT architecture, dual-database persistence (SQLite + MongoDB Atlas), and staff-moderated verification.*

</div>

---

## 📖 Overview

**CampusFind** is an official lost-and-found hub tailored for college campuses. Students frequently misplace ID cards, electronics, keys, and books across lecture halls, libraries, and cafeterias. This portal provides a structured, verified platform where:

- Students report lost or found belongings with photos, locations, and descriptions.
- Campus staff review and approve reports before they become publicly searchable.
- Authenticated students can search, filter, and contact finders securely.
- Platform metrics only update once items are verified by administrators.

---

## 🏗️ System Architecture

The application adopts a **Polyglot Persistence** architecture, utilizing two database engines according to their operational strengths:

```
                  ┌────────────────────────┐
                  │      User Browser      │
                  └───────────┬────────────┘
                              │ HTTP Request
                              ▼
                  ┌────────────────────────┐
                  │    Django URL Router   │
                  │       (urls.py)        │
                  └───────────┬────────────┘
                              │
                              ▼
                  ┌────────────────────────┐
                  │     View Functions     │
                  │       (views.py)       │
                  └──────┬──────────┬──────┘
                         │          │
         Django ORM     │          │  PyMongo (Direct)
                         ▼          ▼
             ┌──────────────┐    ┌────────────────────┐
             │  SQLite DB   │    │   MongoDB Atlas    │
             │ (db.sqlite3) │    │  (item_reports)    │
             ├──────────────┤    ├────────────────────┤
             │ • Users      │    │ • Item documents   │
             │ • Sessions   │    │ • Flexible schema  │
             │ • Auth/Roles │    │ • Soft-ref user ID │
             └──────────────┘    └────────────────────┘
                         │          │
                         └────┬─────┘
                              ▼
                  ┌────────────────────────┐
                  │  Django HTML Templates │
                  │     (Tailwind CSS)     │
                  └────────────────────────┘
```

### Why Dual Databases?

1. **SQLite (via Django ORM):**
   - Django's built-in session, user authentication, and permission system require a relational SQL backend. SQLite provides zero-configuration local persistence for student accounts, passwords, and staff privileges.

2. **MongoDB Atlas (via PyMongo):**
   - Lost and found items inherently possess variable, semi-structured attributes (e.g., a laptop has brand/specs; an ID card has roll numbers/departments). MongoDB's BSON document store naturally models these items.
   - Built with native TLS configuration (`certifi` + `tls=True`) to ensure secure SSL handshakes on Windows and cloud environments.

---

## 📄 MongoDB Document Schema

Each item report in the `item_reports` collection follows this document structure:

```json
{
  "_id": "ObjectId('6735e1...')",
  "reporter_id": 2,
  "reporter_username": "demostudent",
  "report_type": "lost",
  "title": "TI-84 Plus Graphing Calculator",
  "category": "Electronics",
  "description": "Black calculator in a slide case with silver scratches on the back.",
  "location": "Science Block Lab 3",
  "date_lost_found": "2026-11-14",
  "image_path": "items/4b2e8a109f3b49c7bc299e55198d01ef.jpg",
  "status": "Approved",
  "created_at": "2026-11-14T12:30:00Z",
  "updated_at": "2026-11-14T12:35:00Z"
}
```

### Report Status Lifecycle:
- `Pending` — Newly submitted by student; awaiting staff approval (invisible on Browse page and excluded from public counts).
- `Approved` — Verified by admin; publicly searchable on Browse Items and counted in verified statistics.
- `Resolved` — Item successfully reunited; closed out by author or admin.
- `Rejected` — Marked as invalid or duplicate by campus staff.

---

## ✨ Features by Role

### 👤 Guest (Unauthenticated Visitor)
- **Interactive Landing Page:** Minimalist hero with ambient lighting, colorful floating glass bubble effects, and step-by-step workflow guide.
- **Privacy Protection:** Item listings, item detail pages, and live statistics are protected from unauthenticated access.
- **Dedicated Dual Login:** Switch seamlessly between Student Login and Admin Login tabs.

### 🎓 Registered Student (Logged In)
- **Browse & Search:** Filter verified items by keyword, item type (*Lost / Found*), category (*Electronics, Books, Accessories, ID Cards, Clothing, Other*), and campus location.
- **Submit Reports:** Report lost or found belongings with image upload (verified via Pillow for format and size security).
- **Personal Dashboard (*My Reports*):** View status breakdown (*Pending, Approved, Resolved, Rejected*), edit existing submissions, delete reports, or mark approved items as resolved.
- **Secure Campus Contact:** Direct mailto communication channel to the reporter without exposing raw contact details publicly.

### 🛡️ Campus Staff & Administrator
- **Admin Verification Portal (`/portal-admin/`):** Dedicated staff dashboard with live metrics.
- **One-Click Moderation:**
  - **Approve:** Publishes pending items to the live directory.
  - **Reject:** Dismisses spam or invalid submissions.
  - **Resolve:** Manually closes completed cases.
  - **Delete:** Permanently deletes inappropriate reports and removes media files from disk.
- **Staff Direct Route:** Automatic redirect to moderation dashboard upon login with administrator credentials.

---

## 🛠️ Tech Stack

| Component | Technology | Description |
|-----------|------------|-------------|
| **Backend** | Python 3.12, Django 5.1 | Model-View-Template web framework |
| **NoSQL Database** | MongoDB Atlas, PyMongo 4.x | Cloud document database for item reports |
| **SQL Database** | SQLite 3 | Relational database for auth users & sessions |
| **Styling & Icons** | Tailwind CSS (CDN), Lucide Icons | Responsive UI and modern vector icons |
| **Image Handling** | Pillow (PIL) | Secure file validation and upload sanitization |
| **Security & Config** | python-dotenv, certifi | Secret management and TLS root CA validation |

---

## 📂 Project Directory Structure

```
Lost and Found/
│
├── manage.py                        # Django CLI utility
├── requirements.txt                 # Project dependencies
├── .env                             # Secret environment variables (ignored by git)
├── .env.example                     # Environment variables template
├── .gitignore                       # Git ignore rules
├── db.sqlite3                       # SQLite database (auth & sessions)
│
├── campus_lost_found/               # Core project configuration
│   ├── settings.py                  # Django settings & MongoDB environment loading
│   ├── urls.py                      # Root URL routing & media serving
│   ├── wsgi.py                      # WSGI configuration
│   └── asgi.py                      # ASGI configuration
│
└── finder/                          # Main lost and found application
    ├── db.py                        # MongoDB client singleton & TLS configuration
    ├── models.py                    # ReportService CRUD layer & metrics calculation
    ├── forms.py                     # StudentRegistrationForm, LoginForm, ItemReportForm
    ├── views.py                     # Controllers for auth, reporting, search, & admin
    ├── urls.py                      # Application endpoint routes
    ├── tests.py                     # 14 automated unit and integration tests
    │
    ├── management/commands/
    │   ├── check_mongo.py           # Connectivity test command for MongoDB Atlas
    │   ├── test_mongo_crud.py       # Automated CRUD verification command
    │   └── create_admin.py          # Admin/staff user generator command
    │
    ├── static/finder/
    │   ├── css/style.css            # Custom CSS & bubble float animations
    │   └── js/script.js             # Mobile menu and alert dismissal scripts
    │
    ├── templates/
    │   ├── 404.html                 # Custom 404 Not Found template
    │   ├── 500.html                 # Custom 500 Server Error template
    │   └── finder/
    │       ├── base.html            # Core layout, responsive navbar & footer
    │       ├── home.html            # Public landing & member home page
    │       ├── item_list.html       # Search, filter, and report catalog
    │       ├── item_detail.html     # Single report view & reporter contact
    │       ├── report_form.html     # Submission & edit report form
    │       ├── register.html        # Student account creation page
    │       ├── login.html           # Dual Student/Admin login page with tab switcher
    │       ├── my_reports.html      # Student management dashboard
    │       └── admin_dashboard.html # Staff moderation & approval portal
    │
    └── media/items/                 # Uploaded item images (UUID4-renamed)
```

---

## 🚀 Setup & Installation

### Prerequisites
- Python 3.10+ installed
- Free [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) cluster (or local MongoDB)
- Git installed

---

### Step 1 — Clone the Repository

```bash
git clone https://github.com/poorviii19/campus-lost-and-found.git
cd "campus-lost-and-found"
```

---

### Step 2 — Create & Activate Virtual Environment

```bash
# Windows (PowerShell / Command Prompt)
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

---

### Step 4 — Configure Environment Variables

Create your local `.env` configuration file from the template:

```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```

Open `.env` and configure your credentials:

```env
SECRET_KEY=your-django-secret-key-here
DEBUG=True
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/?retryWrites=true&w=majority
MONGO_DB_NAME=campus_lost_found
```

> **Tip:** In MongoDB Atlas, make sure your IP address is added to the **Network Access** IP Access List (`0.0.0.0/0` for development).

---

### Step 5 — Apply Database Migrations

Initializes SQLite tables for Django's user accounts and session records:

```bash
python manage.py migrate
```

---

### Step 6 — Initialize Administrator Account

Run the custom management command to create or update the default campus staff account:

```bash
python manage.py create_admin
```

- **Default Username:** `admin`
- **Default Password:** `AdminPass@2026`

---

### Step 7 — Verify MongoDB Connectivity

Verify that your cluster connection, credentials, and TLS certificates are valid:

```bash
python manage.py check_mongo
```

Expected output:
```
[SUCCESS] Successfully connected to MongoDB! Database: 'campus_lost_found'
```

---

### Step 8 — Start the Development Server

```bash
python manage.py runserver 8000
```

Open your browser and navigate to: **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)**

---

## 👥 User Roles & Credentials

| Role | Portal URL | Default Credentials | Capabilities |
|------|------------|---------------------|--------------|
| **Guest** | `/` | *None* | Views landing page, workflow guide, and login portal |
| **Student** | `/login/` | Register at `/register/` or use existing student | Submits reports, searches items, contacts finders, manages own submissions |
| **Admin** | `/login/?role=admin` | `admin` / `AdminPass@2026` | Reviews pending items, approves, rejects, resolves, and moderates all submissions |

---

## 🔧 Management Commands

Custom management commands located in `finder/management/commands/`:

| Command | Usage | Description |
|---------|-------|-------------|
| `check_mongo` | `python manage.py check_mongo` | Pings MongoDB Atlas and validates TLS & database connection |
| `test_mongo_crud` | `python manage.py test_mongo_crud` | Executes automated Create-Read-Update-Delete cycle on MongoDB |
| `create_admin` | `python manage.py create_admin` | Creates or resets the administrator superuser account |

---

## 🧪 Automated Testing

The project includes an automated test suite covering all critical workflows, authentication boundaries, form validations, and error handlers:

```bash
python manage.py test
```

### Coverage Highlights:
- **Landing & Navigation:** Verifies guest landing page layout and authenticated dashboard views.
- **Authentication:** Tests registration, valid and invalid logins, session handling, and access restrictions.
- **Access Control:** Verifies that `/report/`, `/items/`, `/items/<id>/`, and `/my-reports/` redirect unauthenticated visitors to `/login/`.
- **Form & Image Validation:** Tests Pillow image integrity verification and duplicate username detection.
- **Error Boundaries:** Verifies graceful error handling and redirects on malformed MongoDB ObjectIds.

```
Ran 14 tests in ~23s

OK
```

---

## 📸 Key Application Routes

| Route | View Name | Access | Purpose |
|-------|-----------|--------|---------|
| `/` | `home` | Public | Guest landing page / Student dashboard |
| `/login/` | `login` | Public | Dual Student & Administrator authentication |
| `/register/` | `register` | Public | Student self-registration |
| `/logout/` | `logout` | Authenticated | Flushes session and logs user out |
| `/items/` | `item_list` | Login Required | Searchable and filterable approved item directory |
| `/items/<id>/` | `item_detail` | Login Required | Item details with photo and reporter contact |
| `/report/` | `report_item` | Login Required | Form to submit lost or found reports |
| `/my-reports/` | `my_reports` | Login Required | Personal dashboard with report management |
| `/edit/<id>/` | `edit_report` | Login Required (Owner) | Edit user's own existing report |
| `/delete/<id>/` | `delete_report` | Login Required (Owner) | Delete user's own report and associated image |
| `/resolve/<id>/` | `mark_resolved` | Login Required (Owner) | Mark an approved report as resolved/reunited |
| `/portal-admin/` | `admin_dashboard` | Staff Only | Administration & moderation dashboard |
| `/portal-admin/status/<id>/<action>/` | `admin_update_status` | Staff Only | Approve, reject, or resolve any report |
| `/portal-admin/delete/<id>/` | `admin_delete_report` | Staff Only | Permanently delete inappropriate submissions |

---

## 📄 License

This project was developed for educational and portfolio demonstration purposes as a modern college campus web application.

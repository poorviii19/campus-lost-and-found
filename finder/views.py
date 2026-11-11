import os
import uuid
import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage

from .models import ReportService, CATEGORIES, STATUS_PENDING
from .forms import StudentRegistrationForm, StudentLoginForm, ItemReportForm


def home(request):
    """
    Home page view:
    - Fetches live statistics from MongoDB Atlas (lost, found, resolved counts).
    - Fetches the 6 most recently approved reports from MongoDB.
    - Renders the landing page with Tailwind CSS.
    """
    try:
        stats = ReportService.get_statistics()
        recent_items = ReportService.get_recent_approved_reports(limit=6)
    except Exception as e:
        stats = {'total_lost': 0, 'total_found': 0, 'total_resolved': 0}
        recent_items = []
        messages.warning(request, "Could not connect to database to fetch stats.")

    context = {
        'stats': stats,
        'recent_items': recent_items,
        'categories': CATEGORIES,
    }
    return render(request, 'finder/home.html', context)


# ==========================================
# Authentication Views (Phase 6)
# ==========================================

def user_register(request):
    """
    Student registration view:
    - Validates username uniqueness and password strength.
    - Saves student record to SQLite auth_user table.
    - Automatically logs the student in upon successful registration.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to CampusFind, {user.username}! Your account has been created.")
            return redirect('home')
        else:
            messages.error(request, "Please correct the registration errors below.")
    else:
        form = StudentRegistrationForm()

    return render(request, 'finder/register.html', {'form': form})


def user_login(request):
    """
    Student login view:
    - Validates credentials using Django's built-in authentication system.
    - Establishes a session in SQLite django_session table.
    - Redirects to intended protected page (next parameter) or home.
    """
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next') or 'home'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = StudentLoginForm(request)

    return render(request, 'finder/login.html', {'form': form})


def user_logout(request):
    """
    User logout view:
    - Flushes the session from SQLite django_session table.
    - Clears auth cookies and flashes confirmation message.
    """
    if request.user.is_authenticated:
        username = request.user.username
        logout(request)
        messages.info(request, f"Goodbye {username}! You have been logged out successfully.")
    return redirect('home')


# ==========================================
# Report Submission (Phase 7)
# ==========================================

@login_required
def report_item(request):
    """
    Allows authenticated students to submit a lost or found item report:
    - Validates text inputs and optional image file (size, format, integrity via Pillow).
    - Saves uploaded image to Django media storage.
    - Saves report document to MongoDB Atlas 'item_reports' collection with 'Pending' status.
    """
    if request.method == 'POST':
        form = ItemReportForm(request.POST, request.FILES)
        if form.is_valid():
            image_path = ''
            if request.FILES.get('image'):
                uploaded_file = request.FILES['image']
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                unique_filename = f"items/{uuid.uuid4().hex}{ext}"
                saved_path = default_storage.save(unique_filename, uploaded_file)
                image_path = saved_path

            report = ReportService.create_report(
                reporter_id=request.user.id,
                reporter_username=request.user.username,
                report_type=form.cleaned_data['report_type'],
                title=form.cleaned_data['title'],
                category=form.cleaned_data['category'],
                description=form.cleaned_data['description'],
                location=form.cleaned_data['location'],
                date_lost_found=str(form.cleaned_data['date_lost_found']),
                image_path=image_path,
                status=STATUS_PENDING,
            )

            messages.success(
                request,
                f"Your report for '{report['title']}' has been submitted! It is currently Pending admin verification."
            )
            return redirect('my_reports')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        initial_type = request.GET.get('type', 'lost')
        form = ItemReportForm(initial={
            'report_type': initial_type,
            'date_lost_found': datetime.date.today(),
        })

    return render(request, 'finder/report_form.html', {
        'form': form,
        'is_edit': False,
    })


# ==========================================
# Browse, Search & Filter (Phase 8)
# ==========================================

def item_list(request):
    """
    Public directory of approved lost and found reports:
    - Supports text search across title and description (?q=...).
    - Supports filtering by type ('lost' or 'found') (?type=...).
    - Supports filtering by category (?category=...).
    - Supports filtering by location (?location=...).
    - Sorted by newest reports first.
    - Only reports with status='Approved' are shown.
    """
    q = request.GET.get('q', '').strip()
    type_filter = request.GET.get('type', '').strip().lower()
    category_filter = request.GET.get('category', '').strip()
    location_filter = request.GET.get('location', '').strip()

    try:
        items = ReportService.get_approved_reports(
            search_query=q,
            report_type=type_filter,
            category=category_filter,
            location=location_filter
        )
    except Exception as e:
        items = []
        messages.error(request, "Error retrieving items from database.")

    context = {
        'items': items,
        'categories': CATEGORIES,
        'q': q,
        'selected_type': type_filter,
        'selected_category': category_filter,
        'selected_location': location_filter,
        'total_results': len(items),
    }
    return render(request, 'finder/item_list.html', context)


# ==========================================
# Item Details & Contact (Phase 9)
# ==========================================

def item_detail(request, item_id):
    """
    Item detail view:
    - Retrieves document from MongoDB by ObjectId string.
    - Ensures unapproved reports are accessible only to their author or staff.
    - Retrieves reporter information from SQLite User model.
    - Pre-composes a structured mailto subject & body for authenticated students.
    """
    try:
        item = ReportService.get_report_by_id(item_id)
    except Exception as e:
        messages.error(request, "Unable to load item details due to a database connection issue.")
        return redirect('item_list')

    if not item:
        messages.error(request, "Item report not found or has been removed.")
        return redirect('item_list')

    # Security check: If report is not Approved, only author or admin can view it
    if item.get('status') != 'Approved':
        is_authorized = (
            request.user.is_authenticated and 
            (request.user.id == item.get('reporter_id') or request.user.is_staff or request.user.is_superuser)
        )
        if not is_authorized:
            messages.warning(request, "This report is currently pending verification or has not been approved.")
            return redirect('item_list')

    reporter = User.objects.filter(id=item.get('reporter_id')).first()
    is_owner = request.user.is_authenticated and (request.user.id == item.get('reporter_id'))

    # Pre-compose contact email details for authenticated students
    contact_subject = f"Regarding your {item.get('report_type', 'item')} report: {item.get('title')}"
    if request.user.is_authenticated:
        contact_body = (
            f"Hi {item.get('reporter_username')},\n\n"
            f"I saw your report on the Campus Lost & Found Portal regarding: '{item.get('title')}'.\n\n"
            f"Please let me know when and where on campus we can meet to verify and return the item.\n\n"
            f"Sender Username: {request.user.username}\n"
            f"Sender Email: {request.user.email}"
        )
    else:
        contact_body = ""

    context = {
        'item': item,
        'reporter': reporter,
        'is_owner': is_owner,
        'contact_subject': contact_subject,
        'contact_body': contact_body,
    }
    return render(request, 'finder/item_detail.html', context)


# ==========================================
# Protected View Placeholders
# ==========================================

@login_required
def my_reports(request):
    """User reports dashboard (Full implementation in Phase 10)."""
    messages.info(request, "My Reports dashboard will be implemented in Phase 10.")
    return redirect('home')

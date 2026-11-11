import os
import uuid
import datetime
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.storage import default_storage

from .models import (
    ReportService,
    CATEGORIES,
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_REJECTED,
    STATUS_RESOLVED,
)
from .forms import StudentRegistrationForm, StudentLoginForm, ItemReportForm


def staff_required(view_func):
    """
    Decorator that ensures the user is logged in and possesses staff or superuser privileges.
    """
    return user_passes_test(
        lambda u: u.is_authenticated and (u.is_staff or u.is_superuser),
        login_url='login'
    )(view_func)


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
    except Exception:
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
    except Exception:
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
    except Exception:
        messages.error(request, "Unable to load item details due to a database connection issue.")
        return redirect('item_list')

    if not item:
        messages.error(request, "Item report not found or has been removed.")
        return redirect('item_list')

    # Security check: If report is not Approved, only author or admin can view it
    if item.get('status') != STATUS_APPROVED:
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
# My Reports, Edit & Delete (Phase 10)
# ==========================================

@login_required
def my_reports(request):
    """
    Personal dashboard for the logged-in student:
    - Lists all reports submitted by this user (Pending, Approved, Rejected, Resolved).
    - Summarizes report counts by status.
    """
    try:
        reports = ReportService.get_user_reports(request.user.id)
    except Exception:
        reports = []
        messages.error(request, "Could not fetch your reports from the database.")

    counts = {
        'pending': sum(1 for r in reports if r.get('status') == STATUS_PENDING),
        'approved': sum(1 for r in reports if r.get('status') == STATUS_APPROVED),
        'resolved': sum(1 for r in reports if r.get('status') == STATUS_RESOLVED),
        'rejected': sum(1 for r in reports if r.get('status') == STATUS_REJECTED),
    }

    return render(request, 'finder/my_reports.html', {
        'reports': reports,
        'counts': counts,
    })


@login_required
def edit_report(request, item_id):
    """
    Allows a student to edit details of a report they submitted:
    - Verifies document ownership (user_id == reporter_id).
    - Supports updating title, description, location, date, and photo.
    - Automatically marks modified reports as 'Pending' for admin re-verification (unless already Resolved).
    """
    try:
        item = ReportService.get_report_by_id(item_id)
    except Exception:
        messages.error(request, "Database error retrieving item.")
        return redirect('my_reports')

    if not item or item.get('reporter_id') != request.user.id:
        messages.error(request, "Report not found or you do not have permission to edit it.")
        return redirect('my_reports')

    if request.method == 'POST':
        form = ItemReportForm(request.POST, request.FILES)
        if form.is_valid():
            image_path = item.get('image_path', '')
            if request.FILES.get('image'):
                uploaded_file = request.FILES['image']
                ext = os.path.splitext(uploaded_file.name)[1].lower()
                unique_filename = f"items/{uuid.uuid4().hex}{ext}"
                image_path = default_storage.save(unique_filename, uploaded_file)

            new_status = STATUS_RESOLVED if item.get('status') == STATUS_RESOLVED else STATUS_PENDING

            update_data = {
                'report_type': form.cleaned_data['report_type'],
                'title': form.cleaned_data['title'],
                'category': form.cleaned_data['category'],
                'description': form.cleaned_data['description'],
                'location': form.cleaned_data['location'],
                'date_lost_found': str(form.cleaned_data['date_lost_found']),
                'image_path': image_path,
                'status': new_status,
            }

            ReportService.update_report(item_id, update_data, user_id=request.user.id)
            messages.success(request, f"Report for '{form.cleaned_data['title']}' has been updated successfully!")
            return redirect('my_reports')
        else:
            messages.error(request, "Please correct the errors in the form below.")
    else:
        initial = {
            'report_type': item.get('report_type'),
            'title': item.get('title'),
            'category': item.get('category'),
            'description': item.get('description'),
            'location': item.get('location'),
            'date_lost_found': item.get('date_lost_found'),
        }
        form = ItemReportForm(initial=initial)

    return render(request, 'finder/report_form.html', {
        'form': form,
        'is_edit': True,
        'current_image': item.get('image_path', ''),
    })


@login_required
def delete_report(request, item_id):
    """
    Allows a student to delete their own report:
    - Verifies document ownership (user_id == reporter_id).
    - Deletes document from MongoDB collection.
    - Removes associated image from media storage.
    """
    if request.method == 'POST':
        try:
            item = ReportService.get_report_by_id(item_id)
            if item and item.get('reporter_id') == request.user.id:
                if item.get('image_path') and default_storage.exists(item['image_path']):
                    default_storage.delete(item['image_path'])
                ReportService.delete_report(item_id, user_id=request.user.id)
                messages.success(request, f"Report for '{item['title']}' was deleted.")
            else:
                messages.error(request, "Permission denied or report does not exist.")
        except Exception:
            messages.error(request, "Error deleting report from database.")
    return redirect('my_reports')


@login_required
def mark_resolved(request, item_id):
    """
    Allows a student to mark their own report as Resolved once an item is reunited/claimed:
    - Verifies document ownership.
    - Updates status to 'Resolved'.
    """
    if request.method == 'POST':
        try:
            item = ReportService.get_report_by_id(item_id)
            if item and item.get('reporter_id') == request.user.id:
                ReportService.update_report(item_id, {'status': STATUS_RESOLVED}, user_id=request.user.id)
                messages.success(request, f"Item '{item['title']}' marked as Resolved! 🎉")
            else:
                messages.error(request, "Permission denied.")
        except Exception:
            messages.error(request, "Error updating status.")
    return redirect('my_reports')


# ==========================================
# Admin Management & Moderation (Phase 11)
# ==========================================

@staff_required
def admin_dashboard(request):
    """
    Staff / Administrator Portal:
    - Displays all campus reports with live status metrics.
    - Allows filtering by status (Pending, Approved, Resolved, Rejected).
    - Supports search across title, student username, and location.
    """
    status_filter = request.GET.get('status', '').strip()
    search_query = request.GET.get('q', '').strip()

    try:
        # Get filtered list for display
        reports = ReportService.get_all_reports(
            status_filter=status_filter,
            search_query=search_query
        )
        # Fetch all reports to compute metric cards
        all_reports = ReportService.get_all_reports()
    except Exception:
        reports = []
        all_reports = []
        messages.error(request, "Database connection error while retrieving reports.")

    counts = {
        'all': len(all_reports),
        'pending': sum(1 for r in all_reports if r.get('status') == STATUS_PENDING),
        'approved': sum(1 for r in all_reports if r.get('status') == STATUS_APPROVED),
        'resolved': sum(1 for r in all_reports if r.get('status') == STATUS_RESOLVED),
        'rejected': sum(1 for r in all_reports if r.get('status') == STATUS_REJECTED),
    }

    return render(request, 'finder/admin_dashboard.html', {
        'reports': reports,
        'counts': counts,
        'status_filter': status_filter,
        'search_query': search_query,
    })


@staff_required
def admin_update_status(request, item_id, action):
    """
    Allows staff to update the verification status of a report:
    - 'approve' -> Approved
    - 'reject'  -> Rejected
    - 'resolve' -> Resolved
    """
    if request.method == 'POST':
        action_map = {
            'approve': STATUS_APPROVED,
            'reject': STATUS_REJECTED,
            'resolve': STATUS_RESOLVED,
        }
        new_status = action_map.get(action.lower())
        if new_status:
            try:
                success = ReportService.update_status(item_id, new_status)
                if success:
                    messages.success(request, f"Report status successfully updated to '{new_status}'.")
                else:
                    messages.error(request, "Failed to update report status.")
            except Exception:
                messages.error(request, "Database error updating report.")
        else:
            messages.error(request, "Invalid status action.")

    return redirect('admin_dashboard')


@staff_required
def admin_delete_report(request, item_id):
    """
    Allows staff to permanently delete an inappropriate or spam report and its media file.
    """
    if request.method == 'POST':
        try:
            item = ReportService.get_report_by_id(item_id)
            if item:
                if item.get('image_path') and default_storage.exists(item['image_path']):
                    default_storage.delete(item['image_path'])
                ReportService.delete_report(item_id)
                messages.success(request, f"Report '{item.get('title')}' permanently deleted by Admin.")
            else:
                messages.error(request, "Report not found.")
        except Exception:
            messages.error(request, "Error deleting report.")

    return redirect('admin_dashboard')

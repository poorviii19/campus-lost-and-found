import os
import uuid
import datetime
from django.shortcuts import render, redirect
from django.http import JsonResponse, Http404
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
    CoinWallet,
    CoinTransaction,
    CampusVendor,
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
    - For logged-in users: Fetches live stats and 6 recent approved reports from MongoDB.
    - For guests: Renders a beautiful marketing landing page with no data fetching.
    """
    # Always build the guest category preview (no DB call needed)
    categories_preview = [
        {'label': 'Electronics', 'icon': 'laptop',      'bg': 'bg-blue-50',   'text': 'text-blue-600'},
        {'label': 'Books',       'icon': 'book-open',   'bg': 'bg-amber-50',  'text': 'text-amber-600'},
        {'label': 'Accessories', 'icon': 'watch',       'bg': 'bg-purple-50', 'text': 'text-purple-600'},
        {'label': 'ID Cards',    'icon': 'badge-check', 'bg': 'bg-rose-50',   'text': 'text-rose-600'},
        {'label': 'Clothing',    'icon': 'shirt',       'bg': 'bg-teal-50',   'text': 'text-teal-600'},
        {'label': 'Other',       'icon': 'package',     'bg': 'bg-gray-100',  'text': 'text-gray-600'},
    ]

    if not request.user.is_authenticated:
        return render(request, 'finder/home.html', {
            'categories_preview': categories_preview,
        })

    # Logged-in: fetch live data from MongoDB
    try:
        stats = ReportService.get_statistics()
        recent_items = ReportService.get_recent_approved_reports(limit=6)
    except Exception as e:
        stats = {'total_lost': 0, 'total_found': 0, 'total_resolved': 0}
        recent_items = []
        messages.warning(request, f"Could not connect to database: {type(e).__name__}. Check your .env MONGO_URI.")

    context = {
        'stats': stats,
        'recent_items': recent_items,
        'categories': CATEGORIES,
        'categories_preview': categories_preview,
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
    User login view (supports both Student and Admin/Staff logins):
    - Validates credentials using Django's built-in authentication system.
    - Establishes a session in SQLite django_session table.
    - If user is staff/admin and no specific destination was requested,
      routes directly to the Admin Dashboard.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')
        return redirect('home')

    if request.method == 'POST':
        form = StudentLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            next_url = request.GET.get('next') or request.POST.get('next')
            if not next_url:
                if user.is_staff or user.is_superuser:
                    next_url = 'admin_dashboard'
                else:
                    next_url = 'home'
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please try again.")
    else:
        form = StudentLoginForm(request)

    role = request.GET.get('role', 'student').lower()
    return render(request, 'finder/login.html', {
        'form': form,
        'initial_role': role,
    })


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

@login_required
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
        messages.error(
            request,
            f"Could not connect to the database. Please try again shortly. ({type(e).__name__})"
        )

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

@login_required
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
    Allows a student to mark their own report as Resolved once an item is reunited/claimed.
    Awards 5 CampusCoins to the reporter on successful resolution.
    """
    if request.method == 'POST':
        try:
            item = ReportService.get_report_by_id(item_id)
            if item and item.get('reporter_id') == request.user.id:
                if item.get('status') != STATUS_APPROVED:
                    messages.warning(request, "Only reports that have been approved by an administrator can be marked as resolved.")
                    return redirect('my_reports')
                ReportService.update_report(item_id, {'status': STATUS_RESOLVED}, user_id=request.user.id)

                # 🪙 Award 5 CampusCoins to the reporter
                _award_resolution_coins(request.user, item, item_id)

                messages.success(request, f"Item '{item['title']}' marked as Resolved! 🎉 You earned 5 CampusCoins! 🪙")
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
    Allows staff to update the verification status of a report.
    Awards 5 CampusCoins to the reporter when admin resolves a 'found' item.
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
                item = ReportService.get_report_by_id(item_id)
                success = ReportService.update_status(item_id, new_status)
                if success:
                    messages.success(request, f"Report status successfully updated to '{new_status}'.")
                    # 🪙 Award coins when admin marks as Resolved
                    if new_status == STATUS_RESOLVED and item:
                        try:
                            reporter = User.objects.get(id=item.get('reporter_id'))
                            _award_resolution_coins(reporter, item, item_id)
                        except (User.DoesNotExist, Exception):
                            pass
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


# ==========================================
# Report Chat & Discussion (Admin & Reporter)
# ==========================================

@login_required
def report_chat(request, item_id):
    """
    Direct Chat & Discussion portal for an item report:
    - Allows the Student Reporter and Campus Staff/Admin to communicate directly.
    - Strictly restricts access: only the report's owner and staff members can enter.
    - Supports standard form submissions and renders conversation history.
    """
    try:
        item = ReportService.get_report_by_id(item_id)
    except Exception:
        messages.error(request, "Database connection error.")
        return redirect('item_list')

    if not item:
        messages.error(request, "Report not found.")
        return redirect('item_list')

    is_admin = bool(request.user.is_staff or request.user.is_superuser)
    is_owner = bool(request.user.id == item.get('reporter_id'))

    # Security check: Only author or admin can view/chat
    if not (is_admin or is_owner):
        messages.warning(
            request,
            "Access denied: This report discussion is private between the reporter and campus administration."
        )
        return redirect('item_detail', item_id=item_id)

    sender_role = 'admin' if is_admin else 'reporter'

    if request.method == 'POST':
        message_text = request.POST.get('message', '').strip()
        if message_text:
            msg = ReportService.add_message(
                report_id=item_id,
                sender_id=request.user.id,
                sender_username=request.user.username,
                sender_role=sender_role,
                message_text=message_text
            )
            # Support AJAX / fetch response
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
                return JsonResponse({'success': True, 'message': msg})
        return redirect('report_chat', item_id=item_id)

    reporter = User.objects.filter(id=item.get('reporter_id')).first()
    messages_list = item.get('messages', [])

    context = {
        'item': item,
        'reporter': reporter,
        'messages_list': messages_list,
        'is_admin': is_admin,
        'is_owner': is_owner,
        'sender_role': sender_role,
    }
    return render(request, 'finder/report_chat.html', context)


@login_required
def report_chat_api(request, item_id):
    """
    JSON API endpoint for real-time chat polling and AJAX messaging.
    """
    try:
        item = ReportService.get_report_by_id(item_id)
    except Exception:
        return JsonResponse({'error': 'Database error'}, status=500)

    if not item:
        return JsonResponse({'error': 'Report not found'}, status=404)

    is_admin = bool(request.user.is_staff or request.user.is_superuser)
    is_owner = bool(request.user.id == item.get('reporter_id'))

    if not (is_admin or is_owner):
        return JsonResponse({'error': 'Permission denied'}, status=403)

    sender_role = 'admin' if is_admin else 'reporter'

    if request.method == 'POST':
        import json
        message_text = ''
        if request.content_type == 'application/json':
            try:
                body = json.loads(request.body.decode('utf-8'))
                message_text = body.get('message', '').strip()
            except Exception:
                message_text = ''
        else:
            message_text = request.POST.get('message', '').strip()

        if not message_text:
            return JsonResponse({'error': 'Message cannot be empty'}, status=400)

        msg = ReportService.add_message(
            report_id=item_id,
            sender_id=request.user.id,
            sender_username=request.user.username,
            sender_role=sender_role,
            message_text=message_text
        )
        if msg:
            return JsonResponse({'success': True, 'message': msg})
        return JsonResponse({'error': 'Failed to save message'}, status=500)

    # GET: return list of messages
    messages_list = item.get('messages', [])
    return JsonResponse({
        'messages': messages_list,
        'status': item.get('status'),
        'total': len(messages_list),
    })


# ===========================================================================
# CampusCoin Rewards System Views
# ===========================================================================

COINS_PER_RESOLUTION = 5
MIN_REDEEM_BALANCE = 50


def _award_resolution_coins(user, item, item_id):
    """
    Internal helper: awards 5 CampusCoins to `user` for a resolved report.
    Called by both student mark_resolved and admin_update_status.
    Safe to call in a try/except – never raises.
    """
    try:
        wallet = CoinWallet.get_or_create_wallet(user)
        report_type = item.get('report_type', '')
        title = item.get('title', 'item')
        if report_type == 'found':
            desc = f"🎁 Rewarded for returning found item: {title}"
        else:
            desc = f"🎁 Item successfully recovered: {title}"
        wallet.add_coins(COINS_PER_RESOLUTION, description=desc, report_id=str(item_id))
    except Exception:
        pass


@login_required
def coin_wallet(request):
    """
    Student wallet dashboard:
    - Shows current balance, lifetime stats
    - Shows full transaction history
    - Shows active campus vendors accepting CampusCoin
    """
    wallet = CoinWallet.get_or_create_wallet(request.user)
    transactions = wallet.transactions.all()[:50]
    vendors = CampusVendor.objects.filter(is_active=True)

    return render(request, 'finder/coin_wallet.html', {
        'wallet': wallet,
        'transactions': transactions,
        'vendors': vendors,
        'min_redeem': MIN_REDEEM_BALANCE,
        'coins_per_action': COINS_PER_RESOLUTION,
    })


@login_required
def redeem_coins(request):
    """
    POST endpoint: student redeems coins at a specific campus vendor.
    - Validates vendor exists and is active.
    - Validates amount ≤ vendor's max_discount_coins and ≤ user balance.
    - Validates balance ≥ 50.
    - Deducts coins and logs transaction.
    """
    if request.method != 'POST':
        return redirect('coin_wallet')

    vendor_id = request.POST.get('vendor_id', '').strip()
    try:
        amount = int(request.POST.get('amount', '0'))
    except (ValueError, TypeError):
        messages.error(request, "Please enter a valid coin amount.")
        return redirect('coin_wallet')

    if amount <= 0:
        messages.error(request, "Redemption amount must be greater than 0.")
        return redirect('coin_wallet')

    try:
        vendor = CampusVendor.objects.get(id=vendor_id, is_active=True)
    except CampusVendor.DoesNotExist:
        messages.error(request, "Selected vendor not found or no longer active.")
        return redirect('coin_wallet')

    if amount > vendor.max_discount_coins:
        messages.error(request, f"You can redeem a maximum of {vendor.max_discount_coins} coins per visit at {vendor.name}.")
        return redirect('coin_wallet')

    wallet = CoinWallet.get_or_create_wallet(request.user)
    try:
        wallet.deduct_coins(
            amount,
            description=f"🛍️ Discount at {vendor.name}",
            vendor=vendor.name,
        )
        messages.success(
            request,
            f"✅ Redeemed {amount} coins (₹{amount} discount) at {vendor.logo_emoji} {vendor.name}! "
            f"Remaining balance: {wallet.balance} coins."
        )
    except ValueError as e:
        messages.error(request, str(e))

    return redirect('coin_wallet')


@staff_required
def admin_grant_coins(request):
    """
    Admin tool: manually grant or deduct coins for a user (for testing or special events).
    """
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        try:
            amount = int(request.POST.get('amount', 0))
        except (ValueError, TypeError):
            amount = 0
        reason = request.POST.get('reason', 'Admin grant').strip()

        if not username or amount == 0:
            messages.error(request, "Please provide a username and a non-zero amount.")
            return redirect('admin_coin_manager')

        try:
            user = User.objects.get(username=username)
            wallet = CoinWallet.get_or_create_wallet(user)
            if amount > 0:
                wallet.add_coins(amount, description=f"🎖️ Admin grant: {reason}")
                messages.success(request, f"Granted {amount} coins to @{username}. New balance: {wallet.balance}.")
            else:
                # negative = deduct
                deduct_amt = abs(amount)
                if wallet.balance < deduct_amt:
                    messages.error(request, f"@{username} only has {wallet.balance} coins – cannot deduct {deduct_amt}.")
                else:
                    wallet.balance -= deduct_amt
                    wallet.save(update_fields=['balance', 'updated_at'])
                    CoinTransaction.objects.create(
                        wallet=wallet,
                        transaction_type=CoinTransaction.REDEEM,
                        amount=deduct_amt,
                        description=f"🔧 Admin deduction: {reason}",
                    )
                    messages.success(request, f"Deducted {deduct_amt} coins from @{username}. New balance: {wallet.balance}.")
        except User.DoesNotExist:
            messages.error(request, f"User '@{username}' not found.")

    all_wallets = CoinWallet.objects.select_related('user').order_by('-balance')
    vendors = CampusVendor.objects.all()
    return render(request, 'finder/admin_coin_manager.html', {
        'all_wallets': all_wallets,
        'vendors': vendors,
    })


@staff_required
def admin_manage_vendor(request):
    """
    Admin: add or toggle active/inactive status of a campus vendor.
    """
    if request.method == 'POST':
        action = request.POST.get('action', '')

        if action == 'add':
            name = request.POST.get('name', '').strip()
            location = request.POST.get('location', '').strip()
            description = request.POST.get('description', '').strip()
            logo_emoji = request.POST.get('logo_emoji', '🏪').strip() or '🏪'
            try:
                max_coins = int(request.POST.get('max_discount_coins', 50))
            except (ValueError, TypeError):
                max_coins = 50
            if name and location:
                CampusVendor.objects.create(
                    name=name,
                    location=location,
                    description=description,
                    logo_emoji=logo_emoji,
                    max_discount_coins=max_coins,
                )
                messages.success(request, f"Vendor '{name}' added successfully.")
            else:
                messages.error(request, "Vendor name and location are required.")

        elif action == 'toggle':
            vid = request.POST.get('vendor_id', '')
            try:
                vendor = CampusVendor.objects.get(id=vid)
                vendor.is_active = not vendor.is_active
                vendor.save(update_fields=['is_active'])
                status_str = 'activated' if vendor.is_active else 'deactivated'
                messages.success(request, f"Vendor '{vendor.name}' {status_str}.")
            except CampusVendor.DoesNotExist:
                messages.error(request, "Vendor not found.")

        elif action == 'delete':
            vid = request.POST.get('vendor_id', '')
            try:
                vendor = CampusVendor.objects.get(id=vid)
                name = vendor.name
                vendor.delete()
                messages.success(request, f"Vendor '{name}' permanently removed.")
            except CampusVendor.DoesNotExist:
                messages.error(request, "Vendor not found.")

    return redirect('admin_coin_manager')

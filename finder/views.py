from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import ReportService, CATEGORIES
from .forms import StudentRegistrationForm, StudentLoginForm


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
# Authentication Views
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
# Placeholder views for upcoming phases
# ==========================================

def item_list(request):
    """Browse items page (Full implementation in Phase 8)."""
    return render(request, 'finder/home.html', {
        'stats': ReportService.get_statistics(),
        'recent_items': ReportService.get_recent_approved_reports(limit=6),
        'categories': CATEGORIES,
    })

def item_detail(request, item_id):
    """Item detail view (Full implementation in Phase 9)."""
    messages.info(request, "Item details view will be implemented in Phase 9.")
    return redirect('home')

@login_required
def report_item(request):
    """Report lost/found item (Full implementation in Phase 7)."""
    messages.info(request, "Item reporting form will be implemented in Phase 7.")
    return redirect('home')

@login_required
def my_reports(request):
    """User reports dashboard (Full implementation in Phase 10)."""
    messages.info(request, "My Reports dashboard will be implemented in Phase 10.")
    return redirect('home')

from django.shortcuts import render, redirect
from django.contrib import messages
from .models import ReportService, CATEGORIES

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
        messages.warning(request, "Could not fetch live database stats. Please ensure MongoDB is connected.")

    context = {
        'stats': stats,
        'recent_items': recent_items,
        'categories': CATEGORIES,
    }
    return render(request, 'finder/home.html', context)


# ==========================================
# Placeholder views for navigation routes
# (Will be fully implemented in upcoming phases)
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

def report_item(request):
    """Report lost/found item (Full implementation in Phase 7)."""
    messages.info(request, "Item reporting form will be implemented in Phase 7.")
    return redirect('home')

def my_reports(request):
    """User reports management (Full implementation in Phase 10)."""
    messages.info(request, "My Reports dashboard will be implemented in Phase 10.")
    return redirect('home')

def user_login(request):
    """Student login view (Full implementation in Phase 6)."""
    messages.info(request, "Login system will be implemented in Phase 6.")
    return redirect('home')

def user_register(request):
    """Student registration view (Full implementation in Phase 6)."""
    messages.info(request, "Student registration will be implemented in Phase 6.")
    return redirect('home')

def user_logout(request):
    """User logout view (Full implementation in Phase 6)."""
    messages.info(request, "Logout will be implemented in Phase 6.")
    return redirect('home')

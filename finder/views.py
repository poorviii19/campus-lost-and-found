import django
from django.shortcuts import render

def home(request):
    """
    Temporary homepage view to test MVT routing, view logic, and template rendering.
    Full homepage with MongoDB statistics will be built in Phase 5.
    """
    context = {
        'django_version': django.get_version(),
    }
    return render(request, 'finder/home.html', context)

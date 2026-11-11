from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Browse & Details
    path('items/', views.item_list, name='item_list'),
    path('items/<str:item_id>/', views.item_detail, name='item_detail'),

    # Item Reporting
    path('report/', views.report_item, name='report_item'),

    # My Reports & Management (Phase 10)
    path('my-reports/', views.my_reports, name='my_reports'),
    path('my-reports/edit/<str:item_id>/', views.edit_report, name='edit_report'),
    path('my-reports/delete/<str:item_id>/', views.delete_report, name='delete_report'),
    path('my-reports/resolve/<str:item_id>/', views.mark_resolved, name='mark_resolved'),

    # Authentication (Phase 6)
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
]

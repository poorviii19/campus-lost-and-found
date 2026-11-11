from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Browse & Details
    path('items/', views.item_list, name='item_list'),
    path('items/<str:item_id>/', views.item_detail, name='item_detail'),

    # Item Reporting & Management
    path('report/', views.report_item, name='report_item'),
    path('my-reports/', views.my_reports, name='my_reports'),

    # Authentication
    path('login/', views.user_login, name='login'),
    path('register/', views.user_register, name='register'),
    path('logout/', views.user_logout, name='logout'),
]

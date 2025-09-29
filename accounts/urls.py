from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Authentication URLs
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register'),
    
    # User Dashboard URLs
    path('dashboard/', views.user_dashboard, name='user-dashboard'),
    path('bookings/', views.user_bookings, name='user-bookings'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit-profile'),
    
    # Admin Dashboard URLs
    path('admin/dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('admin/bookings/', views.admin_bookings, name='admin-bookings'),
    path('admin/users/', views.admin_users, name='admin-users'),
    path('admin/facilities/', views.admin_facilities, name='admin-facilities'),
    
    # No password change/reset URLs anymore
]
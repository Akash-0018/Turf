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
    
    # Password reset URLs
    path('password_reset/', 
         auth_views.PasswordResetView.as_view(template_name='accounts/password_reset.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='accounts/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
]
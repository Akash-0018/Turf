"""
URL configuration for turfzone project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from facilities import views as facility_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('admin/', admin.site.urls),
    path('admin/offer/<int:offer_id>/toggle/', facility_views.toggle_offer_active, name='toggle-offer-active'),
    path('admin/review/<int:review_id>/toggle-featured/', facility_views.toggle_review_featured, name='toggle-review-featured'),
    path('admin/review/<int:review_id>/toggle-approved/', facility_views.toggle_review_approved, name='toggle-review-approved'),
    path('accounts/', include('accounts.urls')),
    path('facilities/', include('facilities.urls')),
    path('bookings/', include('bookings.urls')),  # Use main bookings URLs
    path('payments/', include('payments.urls')),
    path('reviews/', include('reviews.urls')),
    
    # Static pages
    path('about/', views.about_us, name='about'),
    path('contact/', views.contact_us, name='contact'),
    path('privacy/', views.privacy_policy, name='privacy'),
    path('terms/', views.terms_conditions, name='terms'),
    path('faq/', views.faq, name='faq'),
    path('careers/', views.careers, name='careers'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'api', views.FacilityViewSet, basename='facility-api')

urlpatterns = [
    path('', views.FacilityListView.as_view(), name='facility-list'),
    path('<int:pk>/', views.FacilityDetailView.as_view(), name='facility-detail'),
    path('', include(router.urls)),
    
    # Admin Settings URLs
    path('admin/settings/', views.AdminSettingsView.as_view(), name='admin-settings'),
    path('admin/settings/save/', views.save_settings, name='save-settings'),
    
    # Facility Management
    path('admin/facility/add/', views.add_facility, name='add-facility'),
    path('admin/facility/<int:facility_id>/edit/', views.edit_facility, name='edit-facility'),
    path('admin/facility/<int:facility_id>/delete/', views.delete_facility, name='delete-facility'),
    path('admin/facility/<int:facility_id>/images/add/', views.add_facility_images, name='add-facility-images'),
    path('admin/facility/<int:facility_id>/images/<int:image_id>/delete/', views.delete_facility_image, name='delete-facility-image'),
    path('admin/facility/<int:facility_id>/images/<int:image_id>/set-primary/', views.set_primary_image, name='set-primary-image'),
    
    # Sports Management
    path('admin/sport/add/', views.add_sport, name='add-sport'),
    path('admin/sport/<int:sport_id>/edit/', views.edit_sport, name='edit-sport'),
    path('admin/sport/<int:sport_id>/delete/', views.delete_sport, name='delete-sport'),
    
    # Offers Management
    path('admin/offer/add/', views.add_offer, name='add-offer'),
    path('admin/offer/<int:offer_id>/edit/', views.edit_offer, name='edit-offer'),
    path('admin/offer/<int:offer_id>/delete/', views.delete_offer, name='delete-offer'),
    path('admin/offer/<int:offer_id>/toggle/', views.toggle_offer_active, name='toggle-offer'),
]
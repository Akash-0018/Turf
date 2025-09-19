from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from . import views, api

router = DefaultRouter()
router.register(r'api', views.BookingViewSet, basename='booking-api')

urlpatterns = [
    # Test URLs
    path('test/', TemplateView.as_view(template_name='includes/slots_test.html'), name='slots-test'),

    # View URLs
    path('', views.BookingPageView.as_view(), name='booking-page'),
    path('get-slots/', api.get_slots, name='get-slots'),
    path('home-slots/', views.home_get_slots, name='home-slots'),
    path('my-bookings/', views.UserBookingListView.as_view(), name='bookings'),
    path('create/', views.BookingCreateView.as_view(), name='booking-create'),
    path('<int:pk>/', views.BookingDetailView.as_view(), name='booking-detail'),
    path('review/<int:booking_id>/', views.review_booking, name='submit-review'),
    path('cancel/<int:pk>/', views.cancel_booking, name='booking-cancel'),
    
    # API URLs
    path('api/', include(router.urls)),
    path('api/activities/', api.get_activities, name='get-activities'),
    path('api/weather/', api.get_weather, name='get-weather'),
    path('api/slots/', api.get_slots, name='api-slots'),
    path('api/book/', api.book_slot, name='api-book-slot'),
]

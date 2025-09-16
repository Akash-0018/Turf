from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'', views.PaymentViewSet, basename='payment')

urlpatterns = [
    path('process/<int:booking_id>/', views.process_payment, name='payment-process'),
    path('success/<int:booking_id>/', views.payment_success, name='payment-success'),
    path('failure/<int:booking_id>/', views.payment_failure, name='payment-failure'),
    path('', include(router.urls)),
]
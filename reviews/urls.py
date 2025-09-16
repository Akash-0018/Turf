from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('reviews', views.ReviewViewSet, basename='review')
router.register('replies', views.ReplyViewSet, basename='reply')

urlpatterns = [
    path('create/', views.create_review, name='review-create'),
    path('<int:review_id>/toggle-featured/', views.toggle_review_featured, name='toggle-review-featured'),
    path('', include(router.urls)),
]
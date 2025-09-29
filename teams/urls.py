from django.urls import path
from . import views

urlpatterns = [
    path('', views.team_list, name='team_list'),
    path('create/', views.create_team, name='create_team'),
    path('join/<int:team_id>/', views.join_team, name='join_team'),
    path('match/call/', views.call_match, name='call_match'),
    path('match/accept/<int:request_id>/', views.accept_match, name='accept_match'),
    path('match/reject/<int:request_id>/', views.reject_match, name='reject_match'),
]
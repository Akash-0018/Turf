from django.urls import path
from . import views

app_name = 'sport_teams'

urlpatterns = [
    # Match request actions
    path('match/reschedule/<int:request_id>/', views.reschedule_match, name='reschedule_match'),
    # Match request URLs
    path('match/call/', views.call_match, name='call_match'),
    path('match/accept/<int:request_id>/', views.accept_match, name='accept_match'),
    path('match/reject/<int:request_id>/', views.reject_match, name='reject_match'),
    path('match/requests/', views.get_match_requests, name='match_requests'),
    # Search endpoint should be before slug patterns to avoid confusion
    path('search_player/', views.search_player, name='search_player'),
    
    # Team management URLs
    path('', views.TeamListView.as_view(), name='team_list'),
    path('create/', views.TeamCreateView.as_view(), name='create_team'),
    path('<slug:slug>/', views.TeamDetailView.as_view(), name='team_detail'),
    path('<slug:slug>/manage/', views.TeamManageView.as_view(), name='manage_team'),
    path('<slug:slug>/delete/', views.TeamDeleteView.as_view(), name='delete_team'),
    path('<slug:slug>/members/<int:member_id>/remove/', views.remove_team_member, name='remove_member'),
    path('<slug:slug>/members/add/', views.add_team_member, name='add_member'),
]
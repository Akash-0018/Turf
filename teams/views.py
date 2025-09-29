from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from .models import Team, TeamMember
from .match_request import MatchRequest
from facilities.models import Facility, TimeSlot


@login_required
def team_list(request):
    teams = Team.objects.all()
    user_team = TeamMember.objects.filter(user=request.user, is_active=True).first()
    available_opponents = Team.objects.exclude(
        Q(members__user=request.user) | Q(match_challenges__opponent__members__user=request.user)
    ).distinct()

    context = {
        'teams': teams,
        'user_team': user_team.team if user_team else None,
        'available_opponents': available_opponents,
        'today': timezone.now().date()
    }
    return render(request, 'teams/teams.html', context)


@login_required
def create_team(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        try:
            team = Team.objects.create(name=name)
            TeamMember.objects.create(
                team=team,
                user=request.user,
                role='captain'
            )
            return JsonResponse({
                'success': True,
                'message': 'Team created successfully!'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': str(e)
            })
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@login_required
def join_team(request, team_id):
    if request.method == 'POST':
        team = get_object_or_404(Team, id=team_id)
        if not TeamMember.objects.filter(user=request.user, is_active=True).exists():
            TeamMember.objects.create(
                team=team,
                user=request.user,
                role='player'
            )
            return JsonResponse({
                'success': True,
                'message': f'Successfully joined {team.name}!'
            })
        return JsonResponse({
            'success': False,
            'message': 'You are already a member of a team'
        })
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@login_required
def call_match(request):
    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        opponent_id = request.POST.get('opponent_id')
        preferred_date = request.POST.get('preferred_date')
        message = request.POST.get('message', '')

        team = get_object_or_404(Team, id=team_id)
        opponent = get_object_or_404(Team, id=opponent_id)

        # Check if user is captain of the team
        if not TeamMember.objects.filter(
            team=team,
            user=request.user,
            role='captain'
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'Only team captains can call for matches'
            })

        # Check if there's already a pending request
        if MatchRequest.objects.filter(
            Q(challenger=team, opponent=opponent) |
            Q(challenger=opponent, opponent=team),
            status='pending'
        ).exists():
            return JsonResponse({
                'success': False,
                'message': 'There is already a pending match request with this team'
            })

        # Create match request
        MatchRequest.objects.create(
            challenger=team,
            opponent=opponent,
            preferred_date=preferred_date,
            message=message
        )

        return JsonResponse({
            'success': True,
            'message': f'Match request sent to {opponent.name}!'
        })

    return JsonResponse({
        'success': False,
        'message': 'Invalid request method'
    })


@login_required
def accept_match(request, request_id):
    match_request = get_object_or_404(MatchRequest, id=request_id)
    
    # Check if user is captain of the opponent team
    if not TeamMember.objects.filter(
        team=match_request.opponent,
        user=request.user,
        role='captain'
    ).exists():
        return JsonResponse({
            'success': False,
            'message': 'Only team captains can accept match requests'
        })

    match_request.accept()
    return JsonResponse({
        'success': True,
        'message': 'Match request accepted!'
    })


@login_required
def reject_match(request, request_id):
    match_request = get_object_or_404(MatchRequest, id=request_id)
    
    # Check if user is captain of the opponent team
    if not TeamMember.objects.filter(
        team=match_request.opponent,
        user=request.user,
        role='captain'
    ).exists():
        return JsonResponse({
            'success': False,
            'message': 'Only team captains can reject match requests'
        })

    response_message = request.POST.get('message', '')
    match_request.reject(response_message)
    return JsonResponse({
        'success': True,
        'message': 'Match request rejected'
    })
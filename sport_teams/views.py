import json
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from django.utils import timezone
from .models import Team, TeamMember, MatchRequest
from .forms import TeamForm, TeamManagementForm, AddPlayerForm
from facilities.models import Facility, TimeSlot
from .utils import notify_match_request

User = get_user_model()

@login_required
def search_player(request):
    phone_number = request.GET.get('phone_number', '').strip()
    if not phone_number:
        return HttpResponse('')
    
    # Use filter instead of get to handle multiple users
    users = User.objects.select_related('player_profile').filter(phone_number=phone_number)
    
    if not users.exists():
        return HttpResponse('<div class="alert alert-warning mt-3"><i class="fas fa-exclamation-circle me-2"></i>No players found with this phone number.</div>')
    
    context = {
        'found_users': users,  # Pass all found users to template
        'multiple_users': users.count() > 1  # Flag to indicate multiple users
    }
    html = render_to_string('sport_teams/player_search_result.html', context)
    return HttpResponse(html)

class TeamListView(ListView):
    model = Team
    template_name = 'sport_teams/team_list.html'
    context_object_name = 'teams'
    ordering = ['name']

class TeamDetailView(DetailView):
    model = Team
    template_name = 'sport_teams/team_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        team = self.get_object()
        
        # Get available opponents
        context['available_opponents'] = Team.objects.exclude(
            Q(id=team.id) |  # Exclude current team
            Q(match_challenges__opponent=team, match_challenges__status='pending') |  # Exclude teams with pending requests
            Q(match_invitations__challenger=team, match_invitations__status='pending')  # Exclude teams we've challenged
        ).distinct()

        # Get available facilities
        context['facilities'] = Facility.objects.filter(is_active=True)

        # Get available time slots
        context['time_slots'] = TimeSlot.objects.all().order_by('start_time')

        # Get pending match requests count
        if self.request.user == team.captain or self.request.user == team.vice_captain:
            context['pending_match_requests'] = MatchRequest.objects.filter(
                opponent=team,
                status='pending'
            ).count()

        # Add today's date for date input
        context['today'] = timezone.now().date()
        
        return context

class TeamCreateView(LoginRequiredMixin, CreateView):
    model = Team
    form_class = TeamForm
    template_name = 'sport_teams/create_team.html'
    success_url = reverse_lazy('sport_teams:team_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        messages.success(self.request, 'Team created successfully!')
        return super().form_valid(form)

class TeamManageView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Team
    form_class = TeamManagementForm
    template_name = 'sport_teams/manage_team.html'

    def test_func(self):
        team = self.get_object()
        return self.request.user == team.captain

    def get_success_url(self):
        return reverse_lazy('sport_teams:team_detail', kwargs={'slug': self.object.slug})

    def form_valid(self, form):
        # Get the old vice captain
        old_vice_captain = self.get_object().vice_captain
        
        # Save the form
        response = super().form_valid(form)
        
        # Get the new vice captain
        new_vice_captain = form.cleaned_data['vice_captain']
        
        # Update team member roles
        if old_vice_captain:
            # Reset old vice captain's role to player
            TeamMember.objects.filter(
                team=self.object,
                user=old_vice_captain
            ).update(role='player')
        
        if new_vice_captain:
            # Update new vice captain's role
            TeamMember.objects.filter(
                team=self.object,
                user=new_vice_captain
            ).update(role='vice_captain')
            messages.success(
                self.request,
                f'Team settings updated. {new_vice_captain.get_full_name() or new_vice_captain.username} is now the vice captain.'
            )
        else:
            messages.success(self.request, 'Team settings updated successfully!')
        
        return response

class TeamDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Team
    success_url = reverse_lazy('sport_teams:team_list')

    def test_func(self):
        team = self.get_object()
        return self.request.user == team.captain

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Team deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
def remove_team_member(request, slug, member_id):
    team = get_object_or_404(Team, slug=slug)
    if request.user != team.captain:
        messages.error(request, 'Only the team captain can remove members.')
        return redirect('sport_teams:team_detail', slug=slug)
    
    member = get_object_or_404(TeamMember, id=member_id, team=team)
    if member.user == team.captain:
        messages.error(request, 'Cannot remove the team captain.')
        return redirect('sport_teams:team_detail', slug=slug)
    
    member.delete()
    messages.success(request, f'{member.user.username} has been removed from the team.')
    return redirect('sport_teams:team_detail', slug=slug)

@login_required
def add_team_member(request, slug):
    team = get_object_or_404(Team, slug=slug)
    
    # Only captain can add members
    if request.user != team.captain:
        messages.error(request, 'Only the team captain can add members.')
        return redirect('sport_teams:team_detail', slug=slug)
    
    if request.method == 'POST':
        # Check if we have a user_id (from search results)
        user_id = request.POST.get('user_id')
        if user_id:
            try:
                user = User.objects.get(id=user_id)
                
                # Check if user is already a member
                if TeamMember.objects.filter(team=team, user=user).exists():
                    messages.error(request, f'{user.get_full_name() or user.username} is already a member of this team.')
                    return redirect('sport_teams:add_member', slug=slug)
                
                # Show confirmation page with user details
                return render(request, 'sport_teams/confirm_add_member.html', {
                    'team': team,
                    'user_to_add': user,
                    'phone_number': user.phone_number,
                    'player_profile': user.player_profile if hasattr(user, 'player_profile') else None
                })
            except User.DoesNotExist:
                messages.error(request, 'Selected player not found. Please try again.')
                return redirect('sport_teams:add_member', slug=slug)
                
        # Handle confirmation submission
        elif 'confirm' in request.POST:
            phone_number = request.POST.get('phone_number')
            try:
                user = User.objects.get(phone_number=phone_number)
                
                # Check if user is already a member
                if TeamMember.objects.filter(team=team, user=user).exists():
                    messages.error(request, f'{user.get_full_name() or user.username} is already a member of this team.')
                    return redirect('sport_teams:team_detail', slug=slug)
                
                # Create new team member
                TeamMember.objects.create(
                    team=team,
                    user=user,
                    role='player'
                )
                messages.success(request, f'{user.get_full_name() or user.username} has been added to the team.')
                return redirect('sport_teams:team_detail', slug=slug)
            except User.DoesNotExist:
                messages.error(request, 'Player not found. Please try again.')
                return redirect('sport_teams:add_member', slug=slug)
        
        # Handle search form submission
        else:
            form = AddPlayerForm(request.POST)
            if form.is_valid():
                return redirect('sport_teams:add_member', slug=slug)
    else:
        form = AddPlayerForm()
    
    context = {
        'form': form,
        'team': team
    }
    return render(request, 'sport_teams/add_member.html', context)


@login_required
def call_match(request):
    if request.method == 'POST':
        team_id = request.POST.get('team_id')
        opponent_id = request.POST.get('opponent_id')
        preferred_date = request.POST.get('preferred_date')
        preferred_facility_id = request.POST.get('facility_id')
        preferred_time_id = request.POST.get('time_slot_id')
        message = request.POST.get('message', '')

        # Validate team captain
        team = get_object_or_404(Team, id=team_id)
        if not team.captain == request.user:
            messages.error(request, 'Only team captains can call for matches.')
            return JsonResponse({'success': False, 'message': 'Only team captains can call for matches'})

        # Get opponent team
        opponent = get_object_or_404(Team, id=opponent_id)

        # Check for existing pending requests
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
        try:
            match_request = MatchRequest.objects.create(
                challenger=team,
                opponent=opponent,
                preferred_date=preferred_date,
                message=message
            )

            # Add facility and time slot if provided
            if preferred_facility_id:
                match_request.preferred_facility_id = preferred_facility_id
            if preferred_time_id:
                match_request.preferred_time_id = preferred_time_id
            match_request.save()

            # Send WhatsApp notification
            if notify_match_request(match_request, 'new_request'):
                message = f'Match request sent to {opponent.name}! Team captains will be notified via WhatsApp.'
            else:
                message = f'Match request sent to {opponent.name}, but there was an issue sending WhatsApp notifications. The admin has been notified.'

            return JsonResponse({
                'success': True,
                'message': message
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
def accept_match(request, request_id):
    try:
        match_request = get_object_or_404(MatchRequest, id=request_id)
        
        # Verify user is captain of opponent team
        if request.user != match_request.opponent.captain:
            return JsonResponse({
                'success': False,
                'message': 'Only team captains can accept match requests'
            })
    except (MatchRequest.DoesNotExist, ValueError) as e:
        return JsonResponse({
            'success': False,
            'message': f'Match request not found: {str(e)}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })
    
    if match_request.status != 'pending':
        return JsonResponse({
            'success': False,
            'message': 'This match request cannot be accepted'
        })

    try:
        # Accept the match request (this will also send notifications)
        match_request.accept()
        
        return JsonResponse({
            'success': True,
            'message': f'Match request from {match_request.challenger.name} has been accepted! Both team captains will be notified.'
        })
    except Exception as e:
        print(f"Error accepting match request: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while accepting the match request.'
        })


@login_required
def reject_match(request, request_id):
    try:
        match_request = get_object_or_404(MatchRequest, id=request_id)
        
        # Verify user is captain of opponent team
        if request.user != match_request.opponent.captain:
            return JsonResponse({
                'success': False,
                'message': 'Only team captains can reject match requests'
            })
    except (MatchRequest.DoesNotExist, ValueError) as e:
        return JsonResponse({
            'success': False,
            'message': f'Match request not found: {str(e)}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'An error occurred: {str(e)}'
        })
    
    if match_request.status != 'pending':
        return JsonResponse({
            'success': False,
            'message': 'This match request cannot be rejected'
        })

    try:
        # Get the reason for rejection from POST data
        data = json.loads(request.body)
        reason = data.get('message', '')
        
        # Reject the match request (this will also send notifications)
        match_request.reject(reason)
        
        return JsonResponse({
            'success': True,
            'message': f'Match request from {match_request.challenger.name} has been rejected. Both team captains will be notified.'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid request data format'
        })
    except Exception as e:
        print(f"Error rejecting match request: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while rejecting the match request.'
        })


@login_required
def get_match_requests(request):
    user_teams = Team.objects.filter(
        Q(captain=request.user) |
        Q(vice_captain=request.user)
    )

    received_requests = MatchRequest.objects.filter(
        opponent__in=user_teams,
        status='pending'
    )

    sent_requests = MatchRequest.objects.filter(
        challenger__in=user_teams
    )

    context = {
        'received_requests': received_requests,
        'sent_requests': sent_requests
    }
    return render(request, 'sport_teams/match_requests.html', context)

@login_required
def reschedule_match(request, request_id):
    match_request = get_object_or_404(MatchRequest, id=request_id)
    team = match_request.challenger if request.user == match_request.challenger.captain else match_request.opponent
    
    # Check if the user is authorized to reschedule
    if request.user not in [match_request.challenger.captain, match_request.opponent.captain]:
        messages.error(request, "You don't have permission to reschedule this match.")
        return redirect('sport_teams:team_detail', slug=team.slug)
    
    if request.method == 'POST':
        new_date = request.POST.get('new_date')
        new_time = request.POST.get('new_time')
        reason = request.POST.get('reason')
        
        if not all([new_date, new_time, reason]):
            messages.error(request, "Please fill in all fields.")
            return render(request, 'sport_teams/reschedule_form.html', {'team': team})
        
        # Update match request
        match_request.preferred_date = new_date
        match_request.preferred_time = new_time
        match_request.message = f"Rescheduled - {reason}"
        match_request.last_updated = timezone.now()
        match_request.status = 'pending'  # Reset to pending for re-approval
        match_request.save()
        
        # Send WhatsApp notification
        if notify_match_request(match_request, 'rescheduled'):
            messages.success(request, "Match has been rescheduled and is pending approval. Team captains have been notified via WhatsApp.")
        else:
            messages.warning(request, "Match has been rescheduled but there was an issue sending WhatsApp notifications. The admin has been notified.")
        
        return redirect('sport_teams:team_detail', slug=team.slug)
    
    context = {
        'team': team,
        'match_request': match_request,
    }
    return render(request, 'sport_teams/reschedule_form.html', context)
from django.db import models
from django.conf import settings
from django.utils.text import slugify
from django.utils import timezone
from facilities.models import Facility, TimeSlot

class Team(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to='team_logos/', null=True, blank=True)
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='captained_teams',
        null=True
    )
    vice_captain = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='vice_captained_teams',
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class TeamMember(models.Model):
    ROLE_CHOICES = [
        ('player', 'Player'),
        ('captain', 'Captain'),
        ('vice_captain', 'Vice Captain'),
    ]

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='player')
    joined_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['team', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.username} - {self.team.name} ({self.role})"


class MatchRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
    ]

    challenger = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='match_challenges'
    )
    opponent = models.ForeignKey(
        Team,
        on_delete=models.CASCADE,
        related_name='match_invitations'
    )
    preferred_date = models.DateField()
    preferred_facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='match_requests'
    )
    preferred_time = models.ForeignKey(
        TimeSlot,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='match_requests'
    )
    message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    response_message = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.challenger.name} vs {self.opponent.name} - {self.get_status_display()}"

    def accept(self):
        self.status = 'accepted'
        self.save()
        from .utils import notify_match_request
        notify_match_request(self, 'accepted')
        return True

    def reject(self, message=None):
        self.status = 'rejected'
        if message:
            self.response_message = message
        self.save()
        from .utils import notify_match_request
        notify_match_request(self, 'rejected')
        return True

    def cancel(self):
        self.status = 'cancelled'
        self.save()

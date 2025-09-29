from django.contrib import admin
from django.utils.html import format_html
from .models import Team, TeamMember, MatchRequest
from .utils import notify_match_request

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'captain', 'vice_captain', 'created_at')
    search_fields = ('name', 'captain__username', 'vice_captain__username')
    list_filter = ('created_at',)
    prepopulated_fields = {'slug': ('name',)}



@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'joined_at', 'is_active')
    list_filter = ('role', 'is_active', 'joined_at')
    search_fields = ('user__username', 'team__name')
    raw_id_fields = ('user', 'team')
    date_hierarchy = 'joined_at'

@admin.register(MatchRequest)
class MatchRequestAdmin(admin.ModelAdmin):
    list_display = ('get_match_teams', 'preferred_date', 'get_status_badge', 'get_facility_info', 'get_actions')
    list_filter = ('status', 'preferred_date', 'created_at')
    search_fields = ('challenger__name', 'opponent__name', 'message')
    readonly_fields = ('created_at', 'updated_at', 'get_status_badge', 'get_challenger_info', 'get_opponent_info')
    raw_id_fields = ('challenger', 'opponent', 'preferred_facility', 'preferred_time')
    date_hierarchy = 'preferred_date'
    actions = ['accept_matches', 'reject_matches', 'cancel_matches']
    
    fieldsets = (
        ('Match Teams', {
            'fields': (('challenger', 'get_challenger_info'), ('opponent', 'get_opponent_info'))
        }),
        ('Match Details', {
            'fields': (
                'preferred_date',
                ('preferred_facility', 'preferred_time'),
                ('status', 'get_status_badge')
            )
        }),
        ('Messages', {
            'fields': ('message', 'response_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def get_match_teams(self, obj):
        return format_html(
            '<div class="match-teams">{} <span class="vs">vs</span> {}</div>',
            obj.challenger.name,
            obj.opponent.name
        )
    get_match_teams.short_description = 'Match'
    
    def get_status_badge(self, obj):
        status_colors = {
            'pending': 'warning',
            'accepted': 'success',
            'rejected': 'danger',
            'cancelled': 'secondary',
            'rescheduled': 'info'
        }
        return format_html(
            '<span class="status-badge status-{}">{}</span>',
            obj.status,
            obj.get_status_display()
        )
    get_status_badge.short_description = 'Status'
    
    def get_challenger_info(self, obj):
        if obj.challenger and obj.challenger.captain:
            return format_html(
                '<div class="info-panel">'
                '<label>Captain:</label> {}<br>'
                '<label>Phone:</label> {}'
                '</div>',
                obj.challenger.captain.get_full_name(),
                obj.challenger.captain.phone_number
            )
        return '-'
    get_challenger_info.short_description = 'Challenger Info'
    
    def get_opponent_info(self, obj):
        if obj.opponent and obj.opponent.captain:
            return format_html(
                '<div class="info-panel">'
                '<label>Captain:</label> {}<br>'
                '<label>Phone:</label> {}'
                '</div>',
                obj.opponent.captain.get_full_name(),
                obj.opponent.captain.phone_number
            )
        return '-'
    get_opponent_info.short_description = 'Opponent Info'
    
    def get_facility_info(self, obj):
        if obj.preferred_facility and obj.preferred_time:
            return format_html(
                '{} at {}',
                obj.preferred_facility.name,
                obj.preferred_time.get_slot_time_display()
            )
        return 'Not specified'
    get_facility_info.short_description = 'Facility & Time'
    
    def get_actions(self, obj):
        if obj.status == 'pending':
            return format_html(
                '<div class="action-buttons">'
                '<button onclick="handleMatchAction({}, \'accept\')" '
                'class="btn btn-success">Accept</button> '
                '<button onclick="handleMatchAction({}, \'reject\')" '
                'class="btn btn-danger">Reject</button>'
                '</div>',
                obj.id, obj.id
            )
        return ''
    get_actions.short_description = 'Actions'
    
    def accept_matches(self, request, queryset):
        count = 0
        for match in queryset.filter(status='pending'):
            if match.accept():
                count += 1
        self.message_user(request, f'{count} match request(s) have been accepted.')
    accept_matches.short_description = 'Accept selected match requests'
    
    def reject_matches(self, request, queryset):
        count = 0
        for match in queryset.filter(status='pending'):
            if match.reject():
                count += 1
        self.message_user(request, f'{count} match request(s) have been rejected.')
    reject_matches.short_description = 'Reject selected match requests'
    
    def cancel_matches(self, request, queryset):
        count = 0
        for match in queryset.filter(status__in=['pending', 'accepted']):
            match.status = 'cancelled'
            match.save()
            count += 1
        self.message_user(request, f'{count} match(es) have been cancelled.')
    cancel_matches.short_description = 'Cancel selected matches'
    
    class Media:
        css = {
            'all': ['admin/css/match_admin.css']
        }
        js = ['admin/js/match_actions.js']
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Match Request Management'
        return super().changelist_view(request, extra_context=extra_context)

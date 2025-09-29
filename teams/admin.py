from django.contrib import admin
from .models import Team, TeamMember

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

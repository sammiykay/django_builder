from django.contrib import admin
from .models import TeamMember, Team

class TeamMemberInline(admin.TabularInline):
    model = TeamMember
    extra = 1
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'is_active', 'member_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name',)
    inlines = [TeamMemberInline]
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Team Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def member_count(self, obj):
        return obj.teammember_set.count()
    member_count.short_description = 'Number of Members'

    actions = ['make_active', 'make_inactive']

    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected teams as active"

    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected teams as inactive"

@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'created_at', 'is_active')
    list_filter = ('team', 'role', 'is_active', 'created_at')
    search_fields = ('user__username', 'user__email', 'team__name')
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Member Information', {
            'fields': ('user', 'team', 'role', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['activate_members', 'deactivate_members']

    def activate_members(self, request, queryset):
        queryset.update(is_active=True)
    activate_members.short_description = "Activate selected members"

    def deactivate_members(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_members.short_description = "Deactivate selected members"
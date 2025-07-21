from django.contrib import admin
from .models import Project

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'updated_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Project Information', {
            'fields': ('title', 'description', 'status')
        }),
        ('Timeline', {
            'fields': ('start_date', 'end_date'),
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def make_completed(self, request, queryset):
        queryset.update(status='completed')
    make_completed.short_description = "Mark selected projects as completed"

    def make_in_progress(self, request, queryset):
        queryset.update(status='in_progress')
    make_in_progress.short_description = "Mark selected projects as in progress"

    actions = ['make_completed', 'make_in_progress']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
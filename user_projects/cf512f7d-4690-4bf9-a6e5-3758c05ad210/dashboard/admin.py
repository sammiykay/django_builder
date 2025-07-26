from django.contrib import admin
from .models import Dashboard, Widget

class WidgetInline(admin.TabularInline):
    model = Widget
    extra = 1
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Dashboard)
class DashboardAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [WidgetInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['make_active', 'make_inactive']
    
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected dashboards as active"
    
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected dashboards as inactive"

@admin.register(Widget)
class WidgetAdmin(admin.ModelAdmin):
    list_display = ('name', 'dashboard', 'widget_type', 'position', 'is_active')
    list_filter = ('widget_type', 'is_active', 'created_at')
    search_fields = ('name', 'dashboard__name')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Widget Information', {
            'fields': ('name', 'dashboard', 'widget_type', 'position', 'is_active')
        }),
        ('Configuration', {
            'fields': ('configuration',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['duplicate_widget']
    
    def duplicate_widget(self, request, queryset):
        for widget in queryset:
            widget.pk = None
            widget.name = f"Copy of {widget.name}"
            widget.save()
    duplicate_widget.short_description = "Duplicate selected widgets"
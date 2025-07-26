from django.contrib import admin
from .models import MetricSnapshot

@admin.register(MetricSnapshot)
class MetricSnapshotAdmin(admin.ModelAdmin):
    list_display = ('id', 'metric_name', 'value', 'timestamp', 'category')
    list_filter = ('metric_name', 'category', 'timestamp')
    search_fields = ('metric_name', 'category')
    readonly_fields = ('timestamp',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('metric_name', 'value', 'category')
        }),
        ('Timestamp Information', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )

    actions = ['reset_metrics']

    def reset_metrics(self, request, queryset):
        queryset.update(value=0)
    reset_metrics.short_description = "Reset selected metrics to zero"

    def get_ordering(self, request):
        return ['-timestamp']
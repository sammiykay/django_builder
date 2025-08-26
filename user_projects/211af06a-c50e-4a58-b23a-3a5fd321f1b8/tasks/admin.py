from django.contrib import admin
from .models import TaskList, Task

class TaskInline(admin.TabularInline):
    model = Task
    extra = 1
    readonly_fields = ('created_at', 'updated_at')

@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'task_count')
    list_filter = ('created_at',)
    search_fields = ('name', 'description')
    readonly_fields = ('created_at',)
    inlines = [TaskInline]

    def task_count(self, obj):
        return obj.task_set.count()
    task_count.short_description = 'Number of Tasks'

    fieldsets = (
        ('Main Information', {
            'fields': ('name', 'description')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task_list', 'due_date', 'priority', 'completed', 'created_at')
    list_filter = ('completed', 'priority', 'due_date', 'task_list')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['mark_completed', 'mark_pending']

    fieldsets = (
        ('Task Information', {
            'fields': ('title', 'description', 'task_list')
        }),
        ('Status', {
            'fields': ('completed', 'priority', 'due_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def mark_completed(self, request, queryset):
        queryset.update(completed=True)
    mark_completed.short_description = "Mark selected tasks as completed"

    def mark_pending(self, request, queryset):
        queryset.update(completed=False)
    mark_pending.short_description = "Mark selected tasks as pending"
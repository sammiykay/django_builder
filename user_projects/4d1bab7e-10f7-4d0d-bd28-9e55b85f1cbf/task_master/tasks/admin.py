from django.contrib import admin
from .models import *

@admin.register(TaskList)
class TaskListAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title']

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title']


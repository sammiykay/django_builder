from django.contrib import admin
from .models import *

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'created_at']
    list_filter = ['created_at']
    search_fields = ['title']


from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from .models import Profile

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fk_name = 'user'
    readonly_fields = ('created_at', 'updated_at')

class CustomUserAdmin(UserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)

    def get_date_joined(self, obj):
        return obj.date_joined
    get_date_joined.short_description = 'Joined'
    get_date_joined.admin_order_field = 'date_joined'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return list()
        return super(CustomUserAdmin, self).get_inline_instances(request, obj)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'birth_date', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at', 'birth_date')
    search_fields = ('user__username', 'user__email', 'phone_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'avatar')
        }),
        ('Personal Information', {
            'fields': ('phone_number', 'birth_date', 'bio')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_profiles_verified']

    def mark_profiles_verified(self, request, queryset):
        queryset.update(is_verified=True)
    mark_profiles_verified.short_description = "Mark selected profiles as verified"

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('user')

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)
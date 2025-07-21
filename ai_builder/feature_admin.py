from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .feature_models import FeatureCategory, Feature, UserFeatureUsage, PlanFeatureOverride


@admin.register(FeatureCategory)
class FeatureCategoryAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'icon', 'sort_order', 'feature_count', 'is_active']
    list_editable = ['sort_order', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description')
        }),
        ('Display Settings', {
            'fields': ('icon', 'sort_order', 'is_active')
        }),
    )
    
    def feature_count(self, obj):
        count = obj.features.count()
        if count > 0:
            url = reverse('admin:ai_builder_feature_changelist') + f'?category__id__exact={obj.id}'
            return format_html('<a href="{}">{} features</a>', url, count)
        return "0 features"
    feature_count.short_description = 'Features'


@admin.register(Feature)
class FeatureAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'name', 'category', 'required_plan', 'plan_badge', 'usage_info', 'is_active', 'is_beta']
    list_editable = ['is_active', 'is_beta', 'sort_order']
    list_filter = ['category', 'required_plan', 'is_active', 'is_beta', 'coming_soon', 'track_usage', 'has_limit']
    search_fields = ['name', 'display_name', 'description']
    ordering = ['category__sort_order', 'sort_order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description', 'category')
        }),
        ('Plan Requirements', {
            'fields': ('required_plan',),
            'description': 'Which plan level is required to access this feature'
        }),
        ('Display Settings', {
            'fields': ('icon', 'sort_order', 'is_active', 'is_beta', 'coming_soon')
        }),
        ('Usage Tracking', {
            'fields': ('track_usage', 'usage_description'),
            'description': 'Whether to track how often users use this feature'
        }),
        ('Usage Limits', {
            'fields': ('has_limit', 'free_limit', 'paid_limit', 'enterprise_limit'),
            'description': 'Set usage limits per plan (leave blank for unlimited)',
            'classes': ['collapse']
        }),
    )
    
    def plan_badge(self, obj):
        colors = {
            'free': '#22c55e',      # green
            'paid': '#3b82f6',      # blue  
            'enterprise': '#8b5cf6'  # purple
        }
        color = colors.get(obj.required_plan, '#6b7280')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 4px; font-size: 12px;">{}</span>',
            color, obj.required_plan.title()
        )
    plan_badge.short_description = 'Plan'
    
    def usage_info(self, obj):
        info_parts = []
        
        if obj.track_usage:
            info_parts.append('📊 Tracked')
        
        if obj.has_limit:
            limits = []
            if obj.free_limit is not None:
                limits.append(f"Free: {obj.free_limit}")
            if obj.paid_limit is not None:
                limits.append(f"Paid: {obj.paid_limit}")  
            else:
                limits.append("Paid: ∞")
            if obj.enterprise_limit is not None:
                limits.append(f"Ent: {obj.enterprise_limit}")
            else:
                limits.append("Ent: ∞")
            info_parts.append("📏 " + " | ".join(limits))
        
        return " • ".join(info_parts) if info_parts else "No limits"
    usage_info.short_description = 'Usage'
    
    actions = ['enable_features', 'disable_features', 'make_beta', 'remove_beta']
    
    def enable_features(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f"Enabled {queryset.count()} features")
    enable_features.short_description = "Enable selected features"
    
    def disable_features(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f"Disabled {queryset.count()} features")
    disable_features.short_description = "Disable selected features"
    
    def make_beta(self, request, queryset):
        queryset.update(is_beta=True)
        self.message_user(request, f"Marked {queryset.count()} features as beta")
    make_beta.short_description = "Mark as beta"
    
    def remove_beta(self, request, queryset):
        queryset.update(is_beta=False)
        self.message_user(request, f"Removed beta status from {queryset.count()} features")
    remove_beta.short_description = "Remove beta status"


class FeatureUsageFilter(admin.SimpleListFilter):
    title = 'usage level'
    parameter_name = 'usage'
    
    def lookups(self, request, model_admin):
        return (
            ('high', 'High usage (>100)'),
            ('medium', 'Medium usage (10-100)'),
            ('low', 'Low usage (<10)'),
            ('unused', 'Never used'),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'high':
            return queryset.filter(usage_count__gt=100)
        elif self.value() == 'medium':
            return queryset.filter(usage_count__gte=10, usage_count__lte=100)
        elif self.value() == 'low':
            return queryset.filter(usage_count__gt=0, usage_count__lt=10)
        elif self.value() == 'unused':
            return queryset.filter(usage_count=0)


@admin.register(UserFeatureUsage)
class UserFeatureUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'feature', 'usage_count', 'current_month_usage', 'month_year', 'last_used']
    list_filter = ['feature', 'month_year', FeatureUsageFilter]
    search_fields = ['user__username', 'user__email', 'feature__display_name']
    ordering = ['-last_used']
    readonly_fields = ['last_used']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'feature')


@admin.register(PlanFeatureOverride)
class PlanFeatureOverrideAdmin(admin.ModelAdmin):
    list_display = ['billing_plan', 'feature', 'is_enabled', 'custom_limit', 'override_info']
    list_editable = ['is_enabled', 'custom_limit']
    list_filter = ['billing_plan', 'feature__category', 'is_enabled']
    search_fields = ['billing_plan__name', 'feature__display_name']
    
    fieldsets = (
        ('Override Settings', {
            'fields': ('billing_plan', 'feature', 'is_enabled')
        }),
        ('Custom Configuration', {
            'fields': ('custom_limit', 'custom_description'),
            'description': 'Override default feature limits and descriptions'
        }),
    )
    
    def override_info(self, obj):
        info = []
        if not obj.is_enabled:
            info.append("❌ Disabled")
        if obj.custom_limit is not None:
            info.append(f"📏 Limit: {obj.custom_limit}")
        if obj.custom_description:
            info.append("📝 Custom desc")
        
        return " • ".join(info) if info else "✅ Standard"
    override_info.short_description = 'Override Info'


# Custom admin views for better feature management
class FeatureDashboardAdmin(admin.ModelAdmin):
    """Custom admin view for feature dashboard"""
    change_list_template = 'admin/feature_dashboard.html'
    
    def changelist_view(self, request, extra_context=None):
        # Get feature statistics
        total_features = Feature.objects.count()
        active_features = Feature.objects.filter(is_active=True).count()
        beta_features = Feature.objects.filter(is_beta=True).count()
        
        # Get usage statistics
        from django.db.models import Sum, Count
        usage_stats = UserFeatureUsage.objects.aggregate(
            total_usage=Sum('usage_count'),
            active_users=Count('user', distinct=True)
        )
        
        # Get most popular features
        popular_features = UserFeatureUsage.objects.values(
            'feature__display_name'
        ).annotate(
            total_usage=Sum('usage_count')
        ).order_by('-total_usage')[:5]
        
        extra_context = extra_context or {}
        extra_context.update({
            'total_features': total_features,
            'active_features': active_features,
            'beta_features': beta_features,
            'total_usage': usage_stats['total_usage'] or 0,
            'active_users': usage_stats['active_users'] or 0,
            'popular_features': popular_features
        })
        
        return super().changelist_view(request, extra_context=extra_context)


# Quick setup functions for admin
def setup_features_admin():
    """Call this to set up all the admin interfaces"""
    pass  # Admin registration is handled by decorators above


# Management command helpers
def create_sample_features():
    """Create sample features for testing"""
    from .feature_models import create_default_features
    create_default_features()
    print("✅ Created default features successfully!")


def reset_monthly_usage():
    """Reset all monthly usage counters - run this monthly"""
    UserFeatureUsage.objects.all().update(current_month_usage=0)
    print("✅ Reset monthly usage counters!")


# Quick feature check for templates and views
def user_can_use(user, feature_name):
    """Simple template function to check if user can use a feature"""
    from .feature_service import FeatureService
    service = FeatureService(user)
    can_use, _ = service.can_use_feature(feature_name)
    return can_use
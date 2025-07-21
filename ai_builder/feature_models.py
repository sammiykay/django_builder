from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


class FeatureCategory(models.Model):
    """Categories to organize features (e.g., AI, Collaboration, Analytics)"""
    name = models.CharField(max_length=100, unique=True)
    display_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Lucide icon name")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.display_name


class Feature(models.Model):
    """Individual features that can be enabled/disabled per plan"""
    PLAN_LEVELS = [
        ('free', 'Free'),
        ('paid', 'Paid'),
        ('enterprise', 'Enterprise'),
    ]
    
    # Basic Info
    name = models.CharField(max_length=100, unique=True, help_text="Internal feature name (e.g., 'priority_processing')")
    display_name = models.CharField(max_length=100, help_text="User-facing name (e.g., 'Priority AI Processing')")
    description = models.TextField(help_text="User-friendly description of what this feature does")
    category = models.ForeignKey(FeatureCategory, on_delete=models.CASCADE, related_name='features')
    
    # Plan Requirements
    required_plan = models.CharField(max_length=20, choices=PLAN_LEVELS, default='free')
    
    # Display Settings
    icon = models.CharField(max_length=50, blank=True, help_text="Lucide icon name")
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_beta = models.BooleanField(default=False)
    coming_soon = models.BooleanField(default=False)
    
    # Usage Tracking
    track_usage = models.BooleanField(default=False, help_text="Whether to track usage statistics for this feature")
    usage_description = models.CharField(max_length=200, blank=True, help_text="How usage is described (e.g., 'projects created', 'team members')")
    
    # Limits (optional)
    has_limit = models.BooleanField(default=False)
    free_limit = models.IntegerField(null=True, blank=True, help_text="Limit for free plan (null = not available)")
    paid_limit = models.IntegerField(null=True, blank=True, help_text="Limit for paid plan (null = unlimited)")
    enterprise_limit = models.IntegerField(null=True, blank=True, help_text="Limit for enterprise plan (null = unlimited)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category__sort_order', 'sort_order', 'name']
    
    def __str__(self):
        return self.display_name
    
    def is_available_for_plan(self, plan_type):
        """Check if feature is available for given plan type"""
        plan_hierarchy = {'free': 0, 'paid': 1, 'enterprise': 2}
        required_level = plan_hierarchy.get(self.required_plan, 0)
        user_level = plan_hierarchy.get(plan_type, 0)
        return user_level >= required_level
    
    def get_limit_for_plan(self, plan_type):
        """Get the usage limit for a specific plan"""
        if not self.has_limit:
            return None
        
        limit_map = {
            'free': self.free_limit,
            'paid': self.paid_limit,
            'enterprise': self.enterprise_limit,
        }
        return limit_map.get(plan_type)


class UserFeatureUsage(models.Model):
    """Track usage of features by users"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    usage_count = models.IntegerField(default=0)
    last_used = models.DateTimeField(auto_now=True)
    
    # Monthly tracking
    current_month_usage = models.IntegerField(default=0)
    month_year = models.CharField(max_length=7, help_text="Format: YYYY-MM")
    
    class Meta:
        unique_together = ['user', 'feature', 'month_year']
    
    def __str__(self):
        return f"{self.user.username} - {self.feature.display_name}: {self.usage_count}"
    
    def reset_monthly_usage(self):
        """Reset the monthly usage counter"""
        self.current_month_usage = 0
        self.save()


class PlanFeatureOverride(models.Model):
    """Allow custom feature configurations for specific billing plans"""
    billing_plan = models.ForeignKey('BillingPlan', on_delete=models.CASCADE, related_name='feature_overrides')
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE)
    
    # Override settings
    is_enabled = models.BooleanField(default=True)
    custom_limit = models.IntegerField(null=True, blank=True, help_text="Custom limit for this specific plan")
    custom_description = models.TextField(blank=True, help_text="Custom description for this plan")
    
    class Meta:
        unique_together = ['billing_plan', 'feature']
    
    def __str__(self):
        return f"{self.billing_plan.name} - {self.feature.display_name}"


# Add these fields to your existing BillingPlan model
class BillingPlanExtended(models.Model):
    """Extended billing plan with feature management (add these fields to your existing BillingPlan)"""
    
    # Feature Access
    max_projects = models.IntegerField(default=5, help_text="Maximum number of projects user can create")
    max_team_members = models.IntegerField(default=1, help_text="Maximum team members for collaboration")
    priority_support = models.BooleanField(default=False)
    custom_branding = models.BooleanField(default=False)
    api_access = models.BooleanField(default=False)
    
    # AI Features  
    priority_processing = models.BooleanField(default=False)
    custom_templates = models.BooleanField(default=False)
    advanced_integrations = models.BooleanField(default=False)
    
    # Analytics & Monitoring
    advanced_analytics = models.BooleanField(default=False)
    usage_insights = models.BooleanField(default=False)
    performance_monitoring = models.BooleanField(default=False)
    
    # Deployment Features
    container_scaling = models.BooleanField(default=False)
    custom_domains = models.BooleanField(default=False)
    ssl_certificates = models.BooleanField(default=True)
    
    class Meta:
        abstract = True


def create_default_features():
    """Helper function to create default features - run this in migrations or management command"""
    
    # Create categories
    ai_category, _ = FeatureCategory.objects.get_or_create(
        name='ai_features',
        defaults={
            'display_name': 'AI & Generation',
            'description': 'Artificial intelligence powered features',
            'icon': 'zap',
            'sort_order': 1
        }
    )
    
    collaboration_category, _ = FeatureCategory.objects.get_or_create(
        name='collaboration',
        defaults={
            'display_name': 'Team & Collaboration',
            'description': 'Features for working with your team',
            'icon': 'users',
            'sort_order': 2
        }
    )
    
    analytics_category, _ = FeatureCategory.objects.get_or_create(
        name='analytics',
        defaults={
            'display_name': 'Analytics & Insights',
            'description': 'Advanced analytics and performance monitoring',
            'icon': 'bar-chart-3',
            'sort_order': 3
        }
    )
    
    deployment_category, _ = FeatureCategory.objects.get_or_create(
        name='deployment',
        defaults={
            'display_name': 'Deployment & Infrastructure',
            'description': 'Advanced deployment and infrastructure features',
            'icon': 'rocket',
            'sort_order': 4
        }
    )
    
    # Create AI features
    Feature.objects.get_or_create(
        name='priority_processing',
        defaults={
            'display_name': 'Priority AI Processing',
            'description': 'Get faster project generation with dedicated resources and skip the queue',
            'category': ai_category,
            'required_plan': 'paid',
            'icon': 'zap',
            'sort_order': 1,
            'track_usage': True,
            'usage_description': '3x faster generation'
        }
    )
    
    Feature.objects.get_or_create(
        name='custom_templates',
        defaults={
            'display_name': 'Custom Templates',
            'description': 'Create and save your own project templates for rapid deployment',
            'category': ai_category,
            'required_plan': 'paid',
            'icon': 'star',
            'sort_order': 2,
            'track_usage': True,
            'usage_description': 'templates saved',
            'has_limit': True,
            'free_limit': 0,
            'paid_limit': 10,
            'enterprise_limit': None
        }
    )
    
    Feature.objects.get_or_create(
        name='advanced_integrations',
        defaults={
            'display_name': 'Advanced Integrations',
            'description': 'Connect with external APIs, databases, and third-party services',
            'category': ai_category,
            'required_plan': 'paid',
            'icon': 'globe',
            'sort_order': 3,
            'track_usage': True,
            'usage_description': 'active integrations'
        }
    )
    
    # Create collaboration features
    Feature.objects.get_or_create(
        name='team_collaboration',
        defaults={
            'display_name': 'Team Collaboration',
            'description': 'Invite team members, share projects, and collaborate in real-time',
            'category': collaboration_category,
            'required_plan': 'enterprise',
            'icon': 'users',
            'sort_order': 1,
            'track_usage': True,
            'usage_description': 'team members',
            'has_limit': True,
            'free_limit': 1,
            'paid_limit': 5,
            'enterprise_limit': None
        }
    )
    
    Feature.objects.get_or_create(
        name='project_sharing',
        defaults={
            'display_name': 'Project Sharing',
            'description': 'Share projects with external collaborators and clients',
            'category': collaboration_category,
            'required_plan': 'paid',
            'icon': 'share',
            'sort_order': 2,
            'track_usage': True,
            'usage_description': 'shared projects'
        }
    )
    
    # Create analytics features
    Feature.objects.get_or_create(
        name='advanced_analytics',
        defaults={
            'display_name': 'Advanced Analytics',
            'description': 'Detailed performance metrics, usage insights, and optimization suggestions',
            'category': analytics_category,
            'required_plan': 'enterprise',
            'icon': 'bar-chart-3',
            'sort_order': 1,
            'track_usage': False,
            'usage_description': 'full dashboard access'
        }
    )
    
    # Create deployment features
    Feature.objects.get_or_create(
        name='custom_domains',
        defaults={
            'display_name': 'Custom Domains',
            'description': 'Deploy your applications with custom domain names',
            'category': deployment_category,
            'required_plan': 'paid',
            'icon': 'globe',
            'sort_order': 1,
            'track_usage': True,
            'usage_description': 'custom domains',
            'has_limit': True,
            'free_limit': 0,
            'paid_limit': 3,
            'enterprise_limit': None
        }
    )
    
    Feature.objects.get_or_create(
        name='priority_support',
        defaults={
            'display_name': 'Priority Support',
            'description': '24/7 dedicated support with direct access to our engineering team',
            'category': deployment_category,
            'required_plan': 'enterprise',
            'icon': 'shield',
            'sort_order': 2,
            'track_usage': False,
            'usage_description': '< 1 hour response time'
        }
    )
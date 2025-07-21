from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from .feature_models import Feature, FeatureCategory, UserFeatureUsage, PlanFeatureOverride
from .models import UserSubscription


class FeatureService:
    """User-friendly service for managing features and permissions"""
    
    def __init__(self, user: User):
        self.user = user
        self._subscription = None
        self._user_plan = None
    
    @property
    def subscription(self):
        """Get user's subscription (cached)"""
        if self._subscription is None:
            try:
                self._subscription = UserSubscription.objects.get(user=self.user)
            except UserSubscription.DoesNotExist:
                self._subscription = None
        return self._subscription
    
    @property
    def user_plan(self):
        """Get user's plan type"""
        if self._user_plan is None:
            if self.subscription:
                self._user_plan = self.subscription.plan.plan_type
            else:
                self._user_plan = 'free'
        return self._user_plan
    
    def can_use_feature(self, feature_name: str) -> Tuple[bool, str]:
        """
        Check if user can use a specific feature
        Returns (can_use, reason)
        """
        try:
            feature = Feature.objects.get(name=feature_name, is_active=True)
        except Feature.DoesNotExist:
            return False, f"Feature '{feature_name}' not found"
        
        # Check if feature is available for user's plan
        if not feature.is_available_for_plan(self.user_plan):
            required_plan = feature.required_plan.title()
            return False, f"This feature requires {required_plan} plan or higher"
        
        # Check feature limits if any
        if feature.has_limit:
            current_usage = self.get_feature_usage(feature_name)
            limit = feature.get_limit_for_plan(self.user_plan)
            
            if limit is not None and current_usage >= limit:
                return False, f"Feature limit reached ({current_usage}/{limit})"
        
        # Check for plan-specific overrides
        if self.subscription:
            override = PlanFeatureOverride.objects.filter(
                billing_plan=self.subscription.plan,
                feature=feature
            ).first()
            
            if override and not override.is_enabled:
                return False, "Feature disabled for your specific plan"
            
            if override and override.custom_limit is not None:
                current_usage = self.get_feature_usage(feature_name)
                if current_usage >= override.custom_limit:
                    return False, f"Custom limit reached ({current_usage}/{override.custom_limit})"
        
        return True, "Feature available"
    
    def use_feature(self, feature_name: str, increment: int = 1) -> bool:
        """
        Record usage of a feature
        Returns True if usage was recorded, False if feature is not available
        """
        can_use, reason = self.can_use_feature(feature_name)
        if not can_use:
            return False
        
        try:
            feature = Feature.objects.get(name=feature_name, is_active=True)
            if not feature.track_usage:
                return True  # Feature doesn't track usage, so it's always available
            
            # Get or create usage record for current month
            current_month = datetime.now().strftime('%Y-%m')
            usage, created = UserFeatureUsage.objects.get_or_create(
                user=self.user,
                feature=feature,
                month_year=current_month,
                defaults={'usage_count': 0, 'current_month_usage': 0}
            )
            
            # Increment usage
            usage.usage_count += increment
            usage.current_month_usage += increment
            usage.save()
            
            return True
            
        except Feature.DoesNotExist:
            return False
    
    def get_feature_usage(self, feature_name: str) -> int:
        """Get current month usage for a feature"""
        try:
            feature = Feature.objects.get(name=feature_name, is_active=True)
            current_month = datetime.now().strftime('%Y-%m')
            
            usage = UserFeatureUsage.objects.filter(
                user=self.user,
                feature=feature,
                month_year=current_month
            ).first()
            
            return usage.current_month_usage if usage else 0
            
        except Feature.DoesNotExist:
            return 0
    
    def get_all_features_for_user(self) -> Dict:
        """
        Get all features organized by category with user's access status
        Returns user-friendly structure for frontend
        """
        categories = FeatureCategory.objects.filter(is_active=True).prefetch_related('features')
        result = {
            'user_plan': self.user_plan,
            'categories': []
        }
        
        for category in categories:
            category_data = {
                'name': category.name,
                'display_name': category.display_name,
                'description': category.description,
                'icon': category.icon,
                'features': []
            }
            
            for feature in category.features.filter(is_active=True):
                can_use, reason = self.can_use_feature(feature.name)
                usage = self.get_feature_usage(feature.name)
                limit = feature.get_limit_for_plan(self.user_plan)
                
                feature_data = {
                    'name': feature.name,
                    'display_name': feature.display_name,
                    'description': feature.description,
                    'icon': feature.icon,
                    'required_plan': feature.required_plan,
                    'is_available': can_use,
                    'reason': reason,
                    'is_beta': feature.is_beta,
                    'coming_soon': feature.coming_soon,
                    'track_usage': feature.track_usage,
                    'usage_description': feature.usage_description,
                    'current_usage': usage,
                    'usage_limit': limit,
                    'usage_percentage': (usage / limit * 100) if limit else 0
                }
                
                category_data['features'].append(feature_data)
            
            if category_data['features']:  # Only include categories with features
                result['categories'].append(category_data)
        
        return result
    
    def get_feature_summary(self) -> Dict:
        """Get a summary of user's feature access"""
        all_features = Feature.objects.filter(is_active=True)
        
        enabled_features = []
        locked_features = []
        
        for feature in all_features:
            can_use, reason = self.can_use_feature(feature.name)
            usage = self.get_feature_usage(feature.name)
            
            feature_info = {
                'name': feature.name,
                'display_name': feature.display_name,
                'description': feature.description,
                'icon': feature.icon,
                'category': feature.category.display_name,
                'usage_description': feature.usage_description,
                'current_usage': usage,
                'reason': reason
            }
            
            if can_use:
                enabled_features.append(feature_info)
            else:
                feature_info['required_plan'] = feature.required_plan
                locked_features.append(feature_info)
        
        return {
            'user_plan': self.user_plan,
            'total_features': len(all_features),
            'enabled_count': len(enabled_features),
            'locked_count': len(locked_features),
            'enabled_features': enabled_features,
            'locked_features': locked_features
        }


class FeatureManager:
    """Static methods for managing features system-wide"""
    
    @staticmethod
    def create_feature(
        name: str,
        display_name: str,
        description: str,
        category_name: str,
        required_plan: str = 'free',
        icon: str = '',
        has_limit: bool = False,
        free_limit: Optional[int] = None,
        paid_limit: Optional[int] = None,
        enterprise_limit: Optional[int] = None,
        track_usage: bool = False,
        usage_description: str = ''
    ) -> Feature:
        """Create a new feature with user-friendly parameters"""
        
        category = FeatureCategory.objects.get(name=category_name)
        
        feature = Feature.objects.create(
            name=name,
            display_name=display_name,
            description=description,
            category=category,
            required_plan=required_plan,
            icon=icon,
            has_limit=has_limit,
            free_limit=free_limit,
            paid_limit=paid_limit,
            enterprise_limit=enterprise_limit,
            track_usage=track_usage,
            usage_description=usage_description
        )
        
        return feature
    
    @staticmethod
    def enable_feature_for_plan(plan, feature_name: str, custom_limit: Optional[int] = None):
        """Enable a feature for a specific billing plan with optional custom limit"""
        feature = Feature.objects.get(name=feature_name)
        
        override, created = PlanFeatureOverride.objects.get_or_create(
            billing_plan=plan,
            feature=feature,
            defaults={
                'is_enabled': True,
                'custom_limit': custom_limit
            }
        )
        
        if not created:
            override.is_enabled = True
            override.custom_limit = custom_limit
            override.save()
        
        return override
    
    @staticmethod
    def disable_feature_for_plan(plan, feature_name: str):
        """Disable a feature for a specific billing plan"""
        feature = Feature.objects.get(name=feature_name)
        
        override, created = PlanFeatureOverride.objects.get_or_create(
            billing_plan=plan,
            feature=feature,
            defaults={'is_enabled': False}
        )
        
        if not created:
            override.is_enabled = False
            override.save()
        
        return override
    
    @staticmethod
    def get_plan_comparison() -> Dict:
        """Get feature comparison across all plans for marketing/pricing pages"""
        features = Feature.objects.filter(is_active=True).select_related('category')
        
        comparison = {
            'features': [],
            'plans': ['free', 'paid', 'enterprise']
        }
        
        for feature in features:
            feature_comparison = {
                'name': feature.name,
                'display_name': feature.display_name,
                'description': feature.description,
                'category': feature.category.display_name,
                'icon': feature.icon,
                'availability': {
                    'free': feature.is_available_for_plan('free'),
                    'paid': feature.is_available_for_plan('paid'),
                    'enterprise': feature.is_available_for_plan('enterprise')
                },
                'limits': {
                    'free': feature.get_limit_for_plan('free'),
                    'paid': feature.get_limit_for_plan('paid'),
                    'enterprise': feature.get_limit_for_plan('enterprise')
                }
            }
            comparison['features'].append(feature_comparison)
        
        return comparison


# Decorators for easy feature checking in views
def requires_feature(feature_name: str):
    """Decorator to check if user has access to a feature before executing view"""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                from django.http import JsonResponse
                return JsonResponse({'error': 'Authentication required'}, status=401)
            
            service = FeatureService(request.user)
            can_use, reason = service.can_use_feature(feature_name)
            
            if not can_use:
                from django.http import JsonResponse
                return JsonResponse({
                    'error': f'Feature not available: {reason}',
                    'feature': feature_name,
                    'required_action': 'upgrade_plan'
                }, status=403)
            
            # Record feature usage
            service.use_feature(feature_name)
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
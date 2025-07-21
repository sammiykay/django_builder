from django.utils import timezone
from django.db.models import Sum
from django.contrib.auth.models import User
from datetime import timedelta
from decimal import Decimal

from .models import (
    BillingPlan, UserSubscription, TokenUsage, BillingInvoice
)


class TokenService:
    """
    Service for managing token usage and limits
    """
    
    @staticmethod
    def can_user_use_tokens(user: User, token_count: int) -> tuple[bool, str]:
        """Check if user can use the specified number of tokens"""
        # Superusers have unlimited access
        if user.is_superuser:
            return True, "Superuser has unlimited access"
        
        try:
            subscription = UserSubscription.objects.get(user=user)
            return subscription.can_use_tokens(token_count)
        except UserSubscription.DoesNotExist:
            # Create default subscription if none exists
            billing_service = BillingService()
            subscription = billing_service.get_or_create_default_subscription(user)
            if subscription:
                return subscription.can_use_tokens(token_count)
            return False, "No subscription found"
    
    @staticmethod
    def use_tokens(user: User, token_count: int, usage_type: str, 
                   project=None, operation_description: str = "",
                   request_data: dict = None, response_data: dict = None,
                   response_time_ms: int = None, success: bool = True,
                   error_message: str = "") -> bool:
        """
        Record token usage and update user's subscription
        """
        # Superusers don't consume tokens but we still log usage
        if user.is_superuser:
            TokenUsage.objects.create(
                user=user,
                project=project,
                usage_type=usage_type,
                tokens_used=token_count,
                operation_description=operation_description,
                request_data=request_data or {},
                response_data=response_data or {},
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                cost_cents=0  # No cost for superusers
            )
            return True
        
        try:
            subscription = UserSubscription.objects.get(user=user)
            
            # Check if user can use tokens
            can_use, reason = subscription.can_use_tokens(token_count)
            if not can_use:
                # Log failed attempt
                TokenUsage.objects.create(
                    user=user,
                    project=project,
                    subscription=subscription,
                    usage_type=usage_type,
                    tokens_used=0,
                    operation_description=f"FAILED: {operation_description}",
                    request_data=request_data or {},
                    response_data=response_data or {},
                    response_time_ms=response_time_ms,
                    success=False,
                    error_message=f"Token limit exceeded: {reason}",
                    cost_cents=0
                )
                return False
            
            # Use tokens from subscription
            subscription.use_tokens(token_count)
            
            # Calculate cost (example: $0.001 per token)
            cost_cents = int(token_count * 0.1)  # 0.1 cents per token
            
            # Record usage
            TokenUsage.objects.create(
                user=user,
                project=project,
                subscription=subscription,
                usage_type=usage_type,
                tokens_used=token_count,
                operation_description=operation_description,
                request_data=request_data or {},
                response_data=response_data or {},
                response_time_ms=response_time_ms,
                success=success,
                error_message=error_message,
                cost_cents=cost_cents,
                billing_period=timezone.now().date()
            )
            
            return True
            
        except UserSubscription.DoesNotExist:
            # Try to create default subscription
            billing_service = BillingService()
            subscription = billing_service.get_or_create_default_subscription(user)
            if subscription:
                return TokenService.use_tokens(
                    user, token_count, usage_type, project, operation_description,
                    request_data, response_data, response_time_ms, success, error_message
                )
            return False
    
    @staticmethod
    def get_user_usage_stats(user: User) -> dict:
        """Get comprehensive usage statistics for a user"""
        try:
            subscription = UserSubscription.objects.get(user=user)
            
            # Current period usage
            current_usage = TokenUsage.objects.filter(
                user=user,
                created_at__gte=subscription.current_period_start
            ).aggregate(
                total_tokens=Sum('tokens_used'),
                total_cost_cents=Sum('cost_cents')
            )
            
            # Usage by type
            usage_by_type = TokenUsage.objects.filter(
                user=user,
                created_at__gte=subscription.current_period_start
            ).values('usage_type').annotate(
                tokens=Sum('tokens_used')
            )
            
            # Convert to dict
            usage_by_type_dict = {
                item['usage_type']: item['tokens'] 
                for item in usage_by_type
            }
            
            # Daily usage for last 30 days
            thirty_days_ago = timezone.now() - timedelta(days=30)
            daily_usage = TokenUsage.objects.filter(
                user=user,
                created_at__gte=thirty_days_ago
            ).extra(
                select={'day': 'date(created_at)'}
            ).values('day').annotate(
                tokens=Sum('tokens_used')
            ).order_by('day')
            
            return {
                'total_tokens_used': current_usage['total_tokens'] or 0,
                'tokens_remaining': subscription.tokens_remaining,
                'usage_percentage': subscription.usage_percentage,
                'current_plan': subscription.plan,
                'usage_by_type': usage_by_type_dict,
                'daily_usage': list(daily_usage),
                'monthly_cost': Decimal((current_usage['total_cost_cents'] or 0) / 100)
            }
            
        except UserSubscription.DoesNotExist:
            return {
                'total_tokens_used': 0,
                'tokens_remaining': 0,
                'usage_percentage': 0,
                'current_plan': None,
                'usage_by_type': {},
                'daily_usage': [],
                'monthly_cost': Decimal('0.00')
            }


class BillingService:
    """
    Service for managing billing operations
    """
    
    def get_or_create_default_subscription(self, user: User) -> UserSubscription:
        """Get or create a default subscription for a user"""
        try:
            return UserSubscription.objects.get(user=user)
        except UserSubscription.DoesNotExist:
            # Find default free plan
            default_plan = BillingPlan.objects.filter(
                is_default_free=True, is_active=True
            ).first()
            
            if default_plan:
                return self.create_subscription(user, default_plan)
            
            return None
    
    def create_subscription(self, user: User, plan: BillingPlan) -> UserSubscription:
        """Create a new subscription for a user"""
        current_period_start = timezone.now()
        
        if plan.billing_interval == 'monthly':
            current_period_end = current_period_start + timedelta(days=30)
        elif plan.billing_interval == 'yearly':
            current_period_end = current_period_start + timedelta(days=365)
        else:  # one_time
            current_period_end = current_period_start + timedelta(days=36500)  # 100 years
        
        subscription = UserSubscription.objects.create(
            user=user,
            plan=plan,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            bonus_tokens_remaining=plan.bonus_tokens,
            status='active'
        )
        
        return subscription
    
    def upgrade_subscription(self, subscription: UserSubscription, new_plan: BillingPlan) -> dict:
        """Upgrade a user's subscription to a new plan"""
        try:
            # Calculate prorated amounts if needed
            old_plan = subscription.plan
            
            # Update subscription
            subscription.plan = new_plan
            
            # Reset period for immediate effect
            subscription.reset_period()
            
            # Add bonus tokens from new plan
            subscription.bonus_tokens_remaining = new_plan.bonus_tokens
            subscription.save()
            
            return {
                'success': True,
                'message': f'Successfully upgraded from {old_plan.name} to {new_plan.name}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def cancel_subscription(self, subscription: UserSubscription) -> dict:
        """Cancel a user's subscription"""
        try:
            subscription.status = 'canceled'
            subscription.canceled_at = timezone.now()
            subscription.auto_renew = False
            subscription.save()
            
            return {
                'success': True,
                'message': 'Subscription canceled successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_usage_stats(self, user: User) -> dict:
        """Get usage statistics for dashboard"""
        return TokenService.get_user_usage_stats(user)
    
    def process_period_renewal(self, subscription: UserSubscription) -> dict:
        """Process subscription renewal for new billing period"""
        try:
            if subscription.status != 'active' or not subscription.auto_renew:
                return {
                    'success': False,
                    'error': 'Subscription not eligible for renewal'
                }
            
            # Reset the billing period
            subscription.reset_period()
            
            # Generate invoice if paid plan
            if not subscription.plan.is_free:
                self.generate_invoice(subscription)
            
            return {
                'success': True,
                'message': 'Subscription renewed successfully'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_invoice(self, subscription: UserSubscription) -> BillingInvoice:
        """Generate an invoice for a subscription period"""
        # Calculate billing period
        if subscription.plan.billing_interval == 'monthly':
            period_start = subscription.current_period_start - timedelta(days=30)
            period_end = subscription.current_period_start
        elif subscription.plan.billing_interval == 'yearly':
            period_start = subscription.current_period_start - timedelta(days=365)
            period_end = subscription.current_period_start
        else:
            period_start = subscription.created_at.date() if hasattr(subscription, 'created_at') else timezone.now().date() - timedelta(days=30)
            period_end = timezone.now().date()
        
        # Calculate overage if any
        tokens_overage = max(0, subscription.tokens_used_this_period - subscription.plan.token_limit)
        overage_amount = Decimal(tokens_overage * 0.001)  # $0.001 per overage token
        
        # Calculate due date (30 days from issue)
        due_date = timezone.now().date() + timedelta(days=30)
        
        # Create invoice
        invoice = BillingInvoice.objects.create(
            user=subscription.user,
            subscription=subscription,
            billing_period_start=period_start,
            billing_period_end=period_end,
            subscription_amount=subscription.plan.price,
            token_overage_amount=overage_amount,
            tax_amount=Decimal('0.00'),  # Add tax calculation logic if needed
            total_amount=subscription.plan.price + overage_amount,
            tokens_included=subscription.plan.token_limit,
            tokens_used=subscription.tokens_used_this_period,
            tokens_overage=tokens_overage,
            due_date=due_date,
            status='draft'
        )
        
        return invoice


class TokenMiddleware:
    """
    Middleware decorator for tracking token usage in views
    """
    
    def __init__(self, usage_type: str, operation_description: str = ""):
        self.usage_type = usage_type
        self.operation_description = operation_description
    
    def __call__(self, view_func):
        def wrapper(request, *args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                # Execute the view
                response = view_func(request, *args, **kwargs)
                
                # Extract token count from response if available
                token_count = getattr(response, 'token_count', 0)
                if token_count > 0:
                    # Calculate response time
                    response_time_ms = int((time.time() - start_time) * 1000)
                    
                    # Record token usage
                    TokenService.use_tokens(
                        user=request.user,
                        token_count=token_count,
                        usage_type=self.usage_type,
                        operation_description=self.operation_description,
                        response_time_ms=response_time_ms,
                        success=True
                    )
                
                return response
                
            except Exception as e:
                # Record failed operation
                response_time_ms = int((time.time() - start_time) * 1000)
                TokenService.use_tokens(
                    user=request.user,
                    token_count=0,
                    usage_type=self.usage_type,
                    operation_description=f"FAILED: {self.operation_description}",
                    response_time_ms=response_time_ms,
                    success=False,
                    error_message=str(e)
                )
                raise
        
        return wrapper
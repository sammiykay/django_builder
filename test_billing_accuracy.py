#!/usr/bin/env python
"""
Test script to verify billing calculations are accurate
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
sys.path.append('.')
django.setup()

from django.contrib.auth.models import User
from ai_builder.models import BillingPlan, UserSubscription
from ai_builder.billing_services import TokenService

def test_billing_accuracy():
    print("Testing Billing System Accuracy...\n")
    
    # Test 1: Token limit calculations
    print("Test 1: Token Limit Calculations")
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            username='test_billing_user',
            defaults={'email': 'test@example.com'}
        )
        
        # Get free plan
        free_plan = BillingPlan.objects.filter(is_default_free=True).first()
        if not free_plan:
            print("❌ No default free plan found!")
            return
        
        # Create or get subscription using BillingService
        from ai_builder.billing_services import BillingService
        billing_service = BillingService()
        
        try:
            subscription = UserSubscription.objects.get(user=user)
        except UserSubscription.DoesNotExist:
            subscription = billing_service.create_subscription(user, free_plan)
        
        print(f"   Plan: {subscription.plan.name}")
        print(f"   Token Limit: {subscription.plan.token_limit:,}")
        print(f"   Bonus Tokens: {subscription.bonus_tokens_remaining:,}")
        print(f"   Used This Period: {subscription.tokens_used_this_period:,}")
        print(f"   Tokens Remaining: {subscription.tokens_remaining:,}")
        print(f"   Usage Percentage: {subscription.usage_percentage:.1f}%")
        
        # Test 2: Token usage simulation
        print("\nTest 2: Token Usage Simulation")
        test_usage = 1000
        can_use, reason = subscription.can_use_tokens(test_usage)
        print(f"   Can use {test_usage:,} tokens? {can_use} - {reason}")
        
        if can_use:
            # Use tokens through the service
            success = TokenService.use_tokens(
                user=user,
                token_count=test_usage,
                usage_type='ai_generation',
                operation_description='Test billing calculation'
            )
            
            # Refresh subscription
            subscription.refresh_from_db()
            print(f"   Used {test_usage:,} tokens successfully: {success}")
            print(f"   New Usage: {subscription.tokens_used_this_period:,}")
            print(f"   Remaining: {subscription.tokens_remaining:,}")
            print(f"   New Percentage: {subscription.usage_percentage:.1f}%")
        
        # Test 3: Edge cases
        print("\nTest 3: Edge Cases")
        
        # Try to use more tokens than available
        remaining = int(subscription.tokens_remaining)
        if remaining > 0:
            excess_usage = remaining + 1000
            can_use_excess, reason_excess = subscription.can_use_tokens(excess_usage)
            print(f"   Can use {excess_usage:,} tokens (exceeds limit)? {can_use_excess} - {reason_excess}")
        
        # Test 4: Cost calculation
        print("\nTest 4: Cost Calculations")
        from ai_builder.models import TokenUsage
        
        recent_usage = TokenUsage.objects.filter(user=user).order_by('-created_at').first()
        if recent_usage:
            print(f"   Recent usage: {recent_usage.tokens_used:,} tokens")
            print(f"   Cost: ${recent_usage.cost_dollars:.4f}")
            print(f"   Plan type: {subscription.plan.plan_type}")
        
        # Test 5: Period reset simulation
        print("\nTest 5: Period Reset")
        old_usage = subscription.tokens_used_this_period
        subscription.reset_period()
        subscription.refresh_from_db()
        print(f"   Usage before reset: {old_usage:,}")
        print(f"   Usage after reset: {subscription.tokens_used_this_period:,}")
        print(f"   New period start: {subscription.current_period_start}")
        print(f"   New period end: {subscription.current_period_end}")
        
        print("\nAll billing tests completed successfully!")
        
        # Cleanup
        if created:
            user.delete()
            print("Cleaned up test user")
            
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_billing_accuracy()
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ai_builder.models import BillingPlan, UserSubscription
from decimal import Decimal


class Command(BaseCommand):
    help = 'Set up initial billing plans and migrate existing users'

    def handle(self, *args, **options):
        self.stdout.write('Setting up billing plans...')
        
        # Create billing plans
        plans = [
            {
                'name': 'Free Starter',
                'description': 'Perfect for trying out Django AI Builder with basic features',
                'plan_type': 'free',
                'token_limit': 10000,
                'bonus_tokens': 0,
                'price': Decimal('0.00'),
                'billing_interval': 'monthly',
                'max_projects': 3,
                'max_concurrent_containers': 1,
                'advanced_features': {},
                'is_active': True,
                'is_default_free': True,
                'sort_order': 1
            },
            {
                'name': 'Pro Developer',
                'description': 'Great for professional developers with increased limits and priority support',
                'plan_type': 'paid',
                'token_limit': 100000,
                'bonus_tokens': 5000,
                'price': Decimal('19.99'),
                'billing_interval': 'monthly',
                'max_projects': 25,
                'max_concurrent_containers': 3,
                'advanced_features': {
                    'priority_support': True,
                    'advanced_analytics': True,
                    'api_access': True
                },
                'is_active': True,
                'is_default_free': False,
                'sort_order': 2
            },
            {
                'name': 'Enterprise',
                'description': 'Unlimited usage for teams and enterprises with all premium features',
                'plan_type': 'enterprise',
                'token_limit': 0,  # Unlimited
                'bonus_tokens': 0,
                'price': Decimal('99.99'),
                'billing_interval': 'monthly',
                'max_projects': 0,  # Unlimited
                'max_concurrent_containers': 10,
                'advanced_features': {
                    'priority_support': True,
                    'advanced_analytics': True,
                    'api_access': True,
                    'custom_templates': True,
                    'team_collaboration': True,
                    'dedicated_support': True
                },
                'is_active': True,
                'is_default_free': False,
                'sort_order': 3
            },
            {
                'name': 'Annual Pro',
                'description': 'Pro features with 20% discount for yearly commitment',
                'plan_type': 'paid',
                'token_limit': 100000,
                'bonus_tokens': 10000,
                'price': Decimal('199.99'),
                'billing_interval': 'yearly',
                'max_projects': 25,
                'max_concurrent_containers': 3,
                'advanced_features': {
                    'priority_support': True,
                    'advanced_analytics': True,
                    'api_access': True
                },
                'is_active': True,
                'is_default_free': False,
                'sort_order': 4
            }
        ]
        
        created_plans = []
        for plan_data in plans:
            plan, created = BillingPlan.objects.get_or_create(
                name=plan_data['name'],
                defaults=plan_data
            )
            if created:
                self.stdout.write(f'Created plan: {plan.name}')
                created_plans.append(plan)
            else:
                self.stdout.write(f'Plan already exists: {plan.name}')
        
        # Get the default free plan
        free_plan = BillingPlan.objects.filter(is_default_free=True).first()
        if not free_plan:
            self.stdout.write(self.style.ERROR('No default free plan found!'))
            return
        
        # Create subscriptions for existing users without subscriptions
        users_without_subscriptions = User.objects.exclude(subscription__isnull=False)
        subscriptions_created = 0
        
        for user in users_without_subscriptions:
            # Skip superusers or give them enterprise plan
            if user.is_superuser:
                enterprise_plan = BillingPlan.objects.filter(plan_type='enterprise').first()
                if enterprise_plan:
                    subscription = UserSubscription.objects.create(
                        user=user,
                        plan=enterprise_plan,
                        current_period_start=user.date_joined,
                        current_period_end=user.date_joined.replace(year=user.date_joined.year + 10),  # Far future
                        bonus_tokens_remaining=enterprise_plan.bonus_tokens,
                        status='active'
                    )
                    self.stdout.write(f'Created enterprise subscription for superuser: {user.username}')
                    subscriptions_created += 1
            else:
                # Create free subscription for regular users
                from dateutil.relativedelta import relativedelta
                from django.utils import timezone
                
                current_period_start = timezone.now()
                current_period_end = current_period_start + relativedelta(months=1)
                
                subscription = UserSubscription.objects.create(
                    user=user,
                    plan=free_plan,
                    current_period_start=current_period_start,
                    current_period_end=current_period_end,
                    bonus_tokens_remaining=free_plan.bonus_tokens,
                    status='active'
                )
                self.stdout.write(f'Created free subscription for user: {user.username}')
                subscriptions_created += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully set up billing system!')
        )
        self.stdout.write(f'- Created {len(created_plans)} new plans')
        self.stdout.write(f'- Created {subscriptions_created} new subscriptions')
        
        # Display plan summary
        self.stdout.write('\nBilling Plans Summary:')
        for plan in BillingPlan.objects.filter(is_active=True).order_by('sort_order'):
            token_display = 'Unlimited' if plan.token_limit == 0 else f'{plan.token_limit:,}'
            price_display = 'Free' if plan.is_free else f'${plan.price}/{plan.billing_interval}'
            self.stdout.write(f'  • {plan.name}: {token_display} tokens, {price_display}')
        
        self.stdout.write('\nBilling system is ready!')
        self.stdout.write('Users can now:')
        self.stdout.write('- View their billing dashboard at /billing')
        self.stdout.write('- Track token usage')
        self.stdout.write('- Upgrade/downgrade plans')
        self.stdout.write('- View usage analytics')
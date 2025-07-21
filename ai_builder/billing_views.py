from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.db.models import Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import (
    BillingPlan, UserSubscription, TokenUsage, BillingInvoice
)
from .serializers import (
    BillingPlanSerializer, UserSubscriptionSerializer, TokenUsageSerializer,
    BillingInvoiceSerializer, UsageStatsSerializer, BillingDashboardSerializer
)
from .billing_services import BillingService, TokenService


class BillingPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing billing plans (admin only for create/update/delete)
    """
    queryset = BillingPlan.objects.filter(is_active=True)
    serializer_class = BillingPlanSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Only superusers can create/update/delete plans"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [permissions.IsAdminUser]
        else:
            permission_classes = [permissions.IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter plans based on user permissions"""
        queryset = self.queryset.order_by('sort_order', 'name')
        
        # Non-superusers only see active plans
        if not self.request.user.is_superuser:
            queryset = queryset.filter(is_active=True)
            
        return queryset


class UserSubscriptionViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing user subscriptions
    """
    queryset = UserSubscription.objects.all()
    serializer_class = UserSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own subscription"""
        if self.request.user.is_superuser:
            return self.queryset.select_related('user', 'plan')
        return self.queryset.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Create subscription for the current user"""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def current(self, request):
        """Get current user's subscription"""
        try:
            subscription = UserSubscription.objects.select_related('plan').get(
                user=request.user
            )
            serializer = self.get_serializer(subscription)
            return Response(serializer.data)
        except UserSubscription.DoesNotExist:
            return Response(
                {'error': 'No subscription found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def upgrade(self, request, pk=None):
        """Upgrade/change subscription plan"""
        subscription = self.get_object()
        plan_id = request.data.get('plan_id')
        
        if not plan_id:
            return Response(
                {'error': 'plan_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            new_plan = BillingPlan.objects.get(id=plan_id, is_active=True)
            billing_service = BillingService()
            result = billing_service.upgrade_subscription(subscription, new_plan)
            
            if result['success']:
                serializer = self.get_serializer(subscription)
                return Response({
                    'subscription': serializer.data,
                    'message': 'Subscription upgraded successfully'
                })
            else:
                return Response(
                    {'error': result['error']}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except BillingPlan.DoesNotExist:
            return Response(
                {'error': 'Plan not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel subscription"""
        subscription = self.get_object()
        billing_service = BillingService()
        result = billing_service.cancel_subscription(subscription)
        
        if result['success']:
            serializer = self.get_serializer(subscription)
            return Response({
                'subscription': serializer.data,
                'message': 'Subscription canceled successfully'
            })
        else:
            return Response(
                {'error': result['error']}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class TokenUsageViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing token usage history
    """
    queryset = TokenUsage.objects.all()
    serializer_class = TokenUsageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own usage"""
        queryset = self.queryset.select_related('user', 'project', 'subscription')
        
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        
        # Filter by date range if provided
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(created_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__lte=end_date)
        
        # Filter by usage type if provided
        usage_type = self.request.query_params.get('usage_type')
        if usage_type:
            queryset = queryset.filter(usage_type=usage_type)
        
        return queryset.order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get usage summary for current user"""
        user = request.user
        
        # Get current period usage
        try:
            subscription = UserSubscription.objects.get(user=user)
            period_start = subscription.current_period_start
        except UserSubscription.DoesNotExist:
            period_start = timezone.now().replace(day=1)
        
        current_usage = TokenUsage.objects.filter(
            user=user,
            created_at__gte=period_start
        ).aggregate(
            total_tokens=Sum('tokens_used'),
            total_cost_cents=Sum('cost_cents')
        )
        
        # Usage by type
        usage_by_type = TokenUsage.objects.filter(
            user=user,
            created_at__gte=period_start
        ).values('usage_type').annotate(
            tokens=Sum('tokens_used'),
            cost_cents=Sum('cost_cents')
        )
        
        # Daily usage for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        daily_usage = TokenUsage.objects.filter(
            user=user,
            created_at__gte=thirty_days_ago
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            tokens=Sum('tokens_used')
        ).order_by('day')
        
        return Response({
            'current_period_usage': current_usage,
            'usage_by_type': list(usage_by_type),
            'daily_usage': list(daily_usage)
        })


class BillingInvoiceViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for viewing billing invoices
    """
    queryset = BillingInvoice.objects.all()
    serializer_class = BillingInvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Users can only see their own invoices"""
        queryset = self.queryset.select_related('user', 'subscription')
        
        if not self.request.user.is_superuser:
            queryset = queryset.filter(user=self.request.user)
        
        return queryset.order_by('-issued_date')


class BillingDashboardViewSet(viewsets.ViewSet):
    """
    ViewSet for billing dashboard data
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def list(self, request):
        """Get comprehensive billing dashboard data"""
        user = request.user
        billing_service = BillingService()
        
        try:
            # Get user's subscription
            subscription = UserSubscription.objects.select_related('plan').get(user=user)
            
            # Get usage stats
            usage_stats = billing_service.get_usage_stats(user)
            
            # Get recent usage (last 50 records)
            recent_usage = TokenUsage.objects.filter(user=user).select_related(
                'project'
            ).order_by('-created_at')[:50]
            
            # Get recent invoices (last 12 months)
            recent_invoices = BillingInvoice.objects.filter(
                user=user
            ).order_by('-issued_date')[:12]
            
            # Get available plans
            available_plans = BillingPlan.objects.filter(is_active=True).order_by(
                'sort_order', 'name'
            )
            
            # Serialize data
            dashboard_data = {
                'subscription': UserSubscriptionSerializer(subscription).data,
                'usage_stats': usage_stats,
                'recent_usage': TokenUsageSerializer(recent_usage, many=True).data,
                'invoices': BillingInvoiceSerializer(recent_invoices, many=True).data,
                'available_plans': BillingPlanSerializer(available_plans, many=True).data
            }
            
            return Response(dashboard_data)
            
        except UserSubscription.DoesNotExist:
            # Create default subscription if none exists
            default_plan = BillingPlan.objects.filter(
                is_default_free=True, is_active=True
            ).first()
            
            if default_plan:
                subscription = billing_service.create_subscription(user, default_plan)
                return self.list(request)  # Retry after creating subscription
            
            return Response(
                {'error': 'No subscription found and no default plan available'}, 
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['get'])
    def usage_chart(self, request):
        """Get data for usage charts"""
        user = request.user
        days = int(request.query_params.get('days', 30))
        
        start_date = timezone.now() - timedelta(days=days)
        
        daily_usage = TokenUsage.objects.filter(
            user=user,
            created_at__gte=start_date
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(
            tokens=Sum('tokens_used'),
            cost_cents=Sum('cost_cents')
        ).order_by('day')
        
        usage_by_type = TokenUsage.objects.filter(
            user=user,
            created_at__gte=start_date
        ).values('usage_type').annotate(
            tokens=Sum('tokens_used'),
            cost_cents=Sum('cost_cents')
        ).order_by('-tokens')
        
        return Response({
            'daily_usage': list(daily_usage),
            'usage_by_type': list(usage_by_type)
        })


# Admin-only viewsets for managing billing
class AdminBillingViewSet(viewsets.ViewSet):
    """
    Admin-only billing management endpoints
    """
    permission_classes = [permissions.IsAdminUser]
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """Get billing overview for admins"""
        # Total revenue
        total_revenue = BillingInvoice.objects.filter(
            status='paid'
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Monthly revenue
        current_month = timezone.now().replace(day=1)
        monthly_revenue = BillingInvoice.objects.filter(
            status='paid',
            issued_date__gte=current_month
        ).aggregate(
            total=Sum('total_amount')
        )['total'] or Decimal('0.00')
        
        # Active subscriptions
        active_subscriptions = UserSubscription.objects.filter(
            status='active'
        ).count()
        
        # Token usage stats
        total_tokens_used = TokenUsage.objects.aggregate(
            total=Sum('tokens_used')
        )['total'] or 0
        
        monthly_tokens_used = TokenUsage.objects.filter(
            created_at__gte=current_month
        ).aggregate(
            total=Sum('tokens_used')
        )['total'] or 0
        
        return Response({
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'active_subscriptions': active_subscriptions,
            'total_tokens_used': total_tokens_used,
            'monthly_tokens_used': monthly_tokens_used
        })
    
    @action(detail=False, methods=['post'])
    def reset_user_usage(self, request):
        """Reset a user's usage for current period"""
        user_id = request.data.get('user_id')
        if not user_id:
            return Response(
                {'error': 'user_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            user = User.objects.get(id=user_id)
            subscription = UserSubscription.objects.get(user=user)
            
            # Reset usage
            subscription.tokens_used_this_period = 0
            subscription.save()
            
            return Response({'message': 'Usage reset successfully'})
        except (User.DoesNotExist, UserSubscription.DoesNotExist):
            return Response(
                {'error': 'User or subscription not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from . import views
from . import billing_views

# Main router
router = DefaultRouter()
router.register(r'projects', views.ProjectViewSet, basename='project')

# Enhanced feature routers
router.register(r'user-profile', views.UserProfileViewSet, basename='user-profile')
router.register(r'chat-threads', views.ChatThreadViewSet, basename='chat-threads')
router.register(r'error-logs', views.ErrorLogViewSet, basename='error-logs')
router.register(r'analytics', views.UsageAnalyticsViewSet, basename='analytics')
router.register(r'sessions', views.ProjectSessionViewSet, basename='sessions')

# Billing routers
router.register(r'billing/plans', billing_views.BillingPlanViewSet, basename='billing-plans')
router.register(r'billing/subscriptions', billing_views.UserSubscriptionViewSet, basename='subscriptions')
router.register(r'billing/usage', billing_views.TokenUsageViewSet, basename='token-usage')
router.register(r'billing/invoices', billing_views.BillingInvoiceViewSet, basename='invoices')
router.register(r'billing/dashboard', billing_views.BillingDashboardViewSet, basename='billing-dashboard')
router.register(r'admin/billing', billing_views.AdminBillingViewSet, basename='admin-billing')

# Nested router for project files
projects_router = routers.NestedDefaultRouter(router, r'projects', lookup='project')
projects_router.register(r'files', views.ProjectFileViewSet, basename='project-files')

app_name = 'ai_builder'

urlpatterns = [
    # Web views
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # API endpoints
    path('api/', include(router.urls)),
    path('api/', include(projects_router.urls)),
    
    # Enhanced feature endpoints
    path('api/project-history/', views.ProjectHistoryView.as_view(), name='project-history'),
    path('api/projects/<uuid:pk>/stats/', views.ProjectStatsView.as_view(), name='project-stats'),
    
    # Payment endpoints
    path('api/payments/', include('ai_builder.payment_urls')),
]
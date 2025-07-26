from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('metrics/', views.metric_list, name='metric_list'),
    path('metrics/create/', views.metric_create, name='metric_create'),
    path('metrics/<int:pk>/', views.metric_detail, name='metric_detail'),
    path('metrics/<int:pk>/update/', views.metric_update, name='metric_update'),
    path('metrics/<int:pk>/delete/', views.metric_delete, name='metric_delete'),
    path('api/metrics/', views.metric_api_list, name='metric_api_list'),
    path('api/metrics/<int:pk>/', views.metric_api_detail, name='metric_api_detail'),
]
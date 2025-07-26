from django.shortcuts import render
from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.utils import timezone
from .models import MetricSnapshot
from django.db.models import Avg, Count
from django.core.exceptions import PermissionDenied
import json

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'analytics/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Get latest metrics
            latest_metrics = MetricSnapshot.objects.order_by('-timestamp')[:10]
            
            # Calculate some basic analytics
            context['latest_metrics'] = latest_metrics
            context['total_snapshots'] = MetricSnapshot.objects.count()
            context['avg_metrics'] = MetricSnapshot.objects.aggregate(
                avg_value=Avg('value')
            )
            
            # Add timestamp for real-time updates
            context['last_updated'] = timezone.now()
            
        except Exception as e:
            context['error'] = str(e)
        
        return context

def get_real_time_metrics(request):
    if not request.user.is_authenticated:
        raise PermissionDenied
    
    try:
        # Get metrics since last update
        last_update = request.GET.get('last_update')
        if last_update:
            metrics = MetricSnapshot.objects.filter(
                timestamp__gt=last_update
            ).values()
        else:
            metrics = MetricSnapshot.objects.all()[:5].values()
            
        return JsonResponse({
            'metrics': list(metrics),
            'timestamp': timezone.now().isoformat()
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)

class MetricsListView(LoginRequiredMixin, ListView):
    model = MetricSnapshot
    template_name = 'analytics/metrics_list.html'
    context_object_name = 'metrics'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.order_by('-timestamp')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_count'] = self.model.objects.count()
        return context

def index(request):
    return render(request, 'analytics/index.html', {
        'page_title': 'Analytics Dashboard',
        'metrics_count': MetricSnapshot.objects.count()
    })

def handler500(request):
    return render(request, 'analytics/500.html', status=500)

def handler404(request, exception):
    return render(request, 'analytics/404.html', status=404)
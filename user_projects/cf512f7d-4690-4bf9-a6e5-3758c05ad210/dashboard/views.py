from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied
from .models import Dashboard, Widget
import json

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/main.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            # Get user's dashboards
            context['user_dashboards'] = Dashboard.objects.filter(user=self.request.user)
            
            # Get active widgets
            active_dashboard = context['user_dashboards'].first()
            if active_dashboard:
                context['active_widgets'] = Widget.objects.filter(dashboard=active_dashboard)
            else:
                context['active_widgets'] = []
            
            # Add real-time data placeholder
            context['real_time_data'] = {
                'notifications': [],
                'updates': [],
                'status': 'active'
            }
            
        except Exception as e:
            context['error'] = str(e)
            
        return context

def update_dashboard_data(request):
    if request.method == 'POST' and request.is_ajax():
        try:
            data = json.loads(request.body)
            dashboard_id = data.get('dashboard_id')
            
            if not dashboard_id:
                return HttpResponseBadRequest('Dashboard ID is required')
                
            dashboard = Dashboard.objects.get(id=dashboard_id, user=request.user)
            widgets = Widget.objects.filter(dashboard=dashboard)
            
            return JsonResponse({
                'widgets': list(widgets.values()),
                'last_updated': dashboard.last_updated
            })
            
        except Dashboard.DoesNotExist:
            return HttpResponseBadRequest('Dashboard not found')
        except Exception as e:
            return HttpResponseBadRequest(str(e))
            
    return HttpResponseBadRequest('Invalid request')

def widget_update(request, widget_id):
    if request.method == 'POST' and request.is_ajax():
        try:
            widget = Widget.objects.get(id=widget_id)
            
            if widget.dashboard.user != request.user:
                raise PermissionDenied
                
            data = json.loads(request.body)
            widget.settings = data.get('settings', widget.settings)
            widget.position = data.get('position', widget.position)
            widget.save()
            
            return JsonResponse({'status': 'success'})
            
        except Widget.DoesNotExist:
            return HttpResponseBadRequest('Widget not found')
        except Exception as e:
            return HttpResponseBadRequest(str(e))
            
    return HttpResponseBadRequest('Invalid request')

def index(request):
    if not request.user.is_authenticated:
        return redirect('login')
    return redirect('dashboard')
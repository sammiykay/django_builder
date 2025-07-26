from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from django.http import JsonResponse
from django.urls import reverse
from django.contrib import messages
from .models import Order
from django.views.decorators.http import require_POST
from django.core.exceptions import PermissionDenied

class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')

class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.user != self.request.user:
            raise PermissionDenied
        return obj

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    context = {
        'orders': orders,
        'title': 'Order History'
    }
    return render(request, 'orders/order_history.html', context)

@login_required
@require_POST
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status == 'pending':
        order.status = 'cancelled'
        order.save()
        messages.success(request, 'Order cancelled successfully.')
    else:
        messages.error(request, 'Order cannot be cancelled.')
    return redirect('orders:order_detail', pk=order.id)

@login_required
def order_status(request, order_id):
    if request.is_ajax():
        order = get_object_or_404(Order, id=order_id, user=request.user)
        return JsonResponse({
            'status': order.status,
            'order_id': order.id
        })
    return JsonResponse({'error': 'Invalid request'}, status=400)

def index(request):
    recent_orders = Order.objects.all().order_by('-created_at')[:5]
    context = {
        'title': 'Orders Dashboard',
        'recent_orders': recent_orders
    }
    return render(request, 'orders/index.html', context)

@login_required
def track_order(request, tracking_number):
    order = get_object_or_404(Order, tracking_number=tracking_number, user=request.user)
    context = {
        'order': order,
        'title': f'Track Order #{order.tracking_number}'
    }
    return render(request, 'orders/track_order.html', context)

def handler404(request, exception):
    return render(request, 'orders/404.html', status=404)

def handler500(request):
    return render(request, 'orders/500.html', status=500)
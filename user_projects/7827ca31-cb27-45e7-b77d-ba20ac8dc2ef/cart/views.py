from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Cart, CartItem
from django.views.generic import View, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from decimal import Decimal

def get_cart(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user, completed=False)
    else:
        cart_id = request.session.get('cart_id')
        if cart_id:
            cart = Cart.objects.filter(id=cart_id, completed=False).first()
            if not cart:
                cart = Cart.objects.create()
        else:
            cart = Cart.objects.create()
        request.session['cart_id'] = cart.id
    return cart

@login_required
def cart_detail(request):
    cart = get_cart(request)
    cart_items = CartItem.objects.filter(cart=cart)
    total = sum(item.get_total_price() for item in cart_items)
    context = {
        'cart': cart,
        'cart_items': cart_items,
        'total': total
    }
    return render(request, 'cart/cart_detail.html', context)

@require_POST
def add_to_cart(request, product_id):
    cart = get_cart(request)
    quantity = int(request.POST.get('quantity', 1))
    
    try:
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        cart_item.quantity += quantity
        cart_item.save()
    except CartItem.DoesNotExist:
        CartItem.objects.create(cart=cart, product_id=product_id, quantity=quantity)
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart_count = cart.get_total_items()
        return JsonResponse({'cart_count': cart_count})
    
    return redirect('cart:cart_detail')

@require_POST
def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 0))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    else:
        cart_item.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = get_cart(request)
        return JsonResponse({
            'item_total': cart_item.get_total_price(),
            'cart_total': cart.get_total_price(),
            'cart_count': cart.get_total_items()
        })
    
    return redirect('cart:cart_detail')

@require_POST
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        cart = get_cart(request)
        return JsonResponse({
            'cart_total': cart.get_total_price(),
            'cart_count': cart.get_total_items()
        })
    
    messages.success(request, 'Item removed from cart.')
    return redirect('cart:cart_detail')

class CartSummaryView(LoginRequiredMixin, ListView):
    model = CartItem
    template_name = 'cart/cart_summary.html'
    context_object_name = 'cart_items'
    
    def get_queryset(self):
        cart = get_cart(self.request)
        return CartItem.objects.filter(cart=cart)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = get_cart(self.request)
        context['cart'] = cart
        context['total'] = cart.get_total_price()
        return context

@login_required
def clear_cart(request):
    cart = get_cart(request)
    cart.items.all().delete()
    messages.success(request, 'Cart cleared successfully.')
    return redirect('cart:cart_detail')
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.core.paginator import Paginator
from .models import Product, Category
from django.http import JsonResponse

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.all()
        
        # Filter by category
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__slug=category)
            
        # Filter by price range
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')
        if min_price:
            queryset = queryset.filter(price__gte=float(min_price))
        if max_price:
            queryset = queryset.filter(price__lte=float(max_price))
            
        # Search functionality
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        # Sorting
        sort_by = self.request.GET.get('sort')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['filters'] = {
            'min_price': self.request.GET.get('min_price', ''),
            'max_price': self.request.GET.get('max_price', ''),
            'category': self.request.GET.get('category', ''),
            'search': self.request.GET.get('q', ''),
        }
        context['sorting_options'] = [
            {'value': 'price_asc', 'label': 'Price: Low to High'},
            {'value': 'price_desc', 'label': 'Price: High to Low'},
            {'value': 'name', 'label': 'Name'},
        ]
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['related_products'] = Product.objects.filter(
            category=self.object.category
        ).exclude(id=self.object.id)[:4]
        return context

def product_search_ajax(request):
    query = request.GET.get('q', '')
    if query:
        products = Product.objects.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query)
        )[:5]
        results = [{
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'url': product.get_absolute_url()
        } for product in products]
        return JsonResponse({'results': results})
    return JsonResponse({'results': []})

def index(request):
    featured_products = Product.objects.filter(featured=True)[:4]
    new_arrivals = Product.objects.order_by('-created_at')[:4]
    
    context = {
        'featured_products': featured_products,
        'new_arrivals': new_arrivals,
        'categories': Category.objects.all()
    }
    return render(request, 'products/index.html', context)
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import *

def home(request):
    """Home view displaying items"""
    items = Item.objects.all()[:10]  # Show latest 10 items
    return render(request, f'tasks/home.html', {{'items': items}})

@login_required
def create_item(request):
    """Create new item"""
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        
        if title:
            Item.objects.create(
                title=title,
                description=description,
                user=request.user
            )
            messages.success(request, 'Item created successfully!')
            return redirect('home')
        else:
            messages.error(request, 'Title is required!')
    
    return render(request, f'tasks/create.html')

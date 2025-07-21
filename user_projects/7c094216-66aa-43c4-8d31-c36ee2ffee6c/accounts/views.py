from django.shortcuts import render, get_object_or_404
from django.views.generic import DetailView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import HttpResponse, Http404
from .models import UserProfile
from blog.models import Article, Comment

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = UserProfile
    template_name = 'accounts/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        return get_object_or_404(UserProfile, user__username=username)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object().user
        
        # Get user's articles
        context['articles'] = Article.objects.filter(author=user).order_by('-created_at')
        
        # Calculate total likes on user's articles
        context['total_likes'] = Article.objects.filter(author=user).aggregate(
            total_likes=Count('likes'))['total_likes'] or 0
            
        # Calculate total comments on user's articles
        context['total_comments'] = Comment.objects.filter(article__author=user).count()
        
        return context

def index(request):
    """
    Basic index view for the accounts app
    """
    return render(request, 'accounts/index.html', {
        'title': 'User Accounts',
    })

def profile_redirect(request):
    """
    Redirects to the user's profile if logged in
    """
    if request.user.is_authenticated:
        return redirect('accounts:profile_detail', username=request.user.username)
    return redirect('login')

def handler404(request, exception):
    """
    Custom 404 error handler
    """
    return render(request, 'accounts/404.html', status=404)

def handler500(request):
    """
    Custom 500 error handler
    """
    return render(request, 'accounts/500.html', status=500)
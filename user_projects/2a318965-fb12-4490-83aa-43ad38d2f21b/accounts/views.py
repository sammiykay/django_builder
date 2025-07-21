from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404
from django.http import Http404
from .models import Profile
from posts.models import Post
from django.db.models import Count

class ProfileDetailView(LoginRequiredMixin, DetailView):
    model = Profile
    template_name = 'accounts/profile_detail.html'
    context_object_name = 'profile'
    
    def get_object(self, queryset=None):
        username = self.kwargs.get('username')
        try:
            return get_object_or_404(Profile, user__username=username)
        except Http404:
            raise Http404("User profile does not exist")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.get_object()
        
        # Get user's posts
        context['posts'] = Post.objects.filter(author=profile.user).order_by('-created_at')
        
        # Get followers and following counts
        context['followers_count'] = profile.followers.count()
        context['following_count'] = profile.following.count()
        
        # Add additional context for the logged-in user
        context['is_following'] = False
        if self.request.user.is_authenticated:
            context['is_following'] = profile.followers.filter(id=self.request.user.id).exists()
            context['is_own_profile'] = (self.request.user == profile.user)
            
        return context
from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Post, Comment
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10

    def get_queryset(self):
        queryset = Post.objects.filter(status='published').order_by('-created_at')
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__name=tag)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tags'] = Post.tags.most_common()
        context['featured_posts'] = Post.objects.filter(
            featured=True,
            status='published'
        )[:5]
        context['categories'] = Post.objects.values_list(
            'category', flat=True
        ).distinct()
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        # Get comments
        context['comments'] = Comment.objects.filter(
            post=post,
            approved=True
        ).order_by('-created_at')
        
        # Get related posts
        context['related_posts'] = Post.objects.filter(
            Q(category=post.category) & 
            ~Q(id=post.id)
        ).filter(
            status='published'
        )[:3]
        
        return context

    def get_object(self, queryset=None):
        obj = super().get_object(queryset=queryset)
        # Increment view count
        obj.views += 1
        obj.save()
        return obj

def index(request):
    """Basic index view as fallback"""
    latest_posts = Post.objects.filter(
        status='published'
    ).order_by('-created_at')[:5]
    return render(request, 'blog/index.html', {
        'latest_posts': latest_posts
    })

def handler404(request, exception):
    return render(request, 'blog/404.html', status=404)

def handler500(request):
    return render(request, 'blog/500.html', status=500)
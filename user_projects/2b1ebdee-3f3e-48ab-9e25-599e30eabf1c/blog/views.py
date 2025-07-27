from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count
from .models import Post, Comment
from .forms import PostForm

class PostListView(ListView):
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        return Post.objects.filter(status='published').order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Post.objects.values('category').annotate(count=Count('category'))
        context['popular_posts'] = Post.objects.filter(status='published').order_by('-views')[:5]
        return context

class PostDetailView(DetailView):
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.get_object()
        
        context['comments'] = Comment.objects.filter(post=post, approved=True)
        context['related_posts'] = Post.objects.filter(
            category=post.category
        ).exclude(id=post.id)[:3]
        
        # Increment view count
        post.views += 1
        post.save()
        
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    template_name = 'blog/post_form.html'
    form_class = PostForm
    success_url = reverse_lazy('blog:post_list')
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

def handler404(request, exception):
    return render(request, 'blog/404.html', status=404)

def handler500(request):
    return render(request, 'blog/500.html', status=500)
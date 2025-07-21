from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from .models import Article, Comment
from django.core.paginator import Paginator
from django.http import HttpResponseForbidden

class ArticleListView(ListView):
    model = Article
    template_name = 'articles/article_list.html'
    context_object_name = 'articles'
    paginate_by = 10

    def get_queryset(self):
        queryset = Article.objects.filter(status='published').order_by('-created_at')
        
        # Handle search
        query = self.request.GET.get('q')
        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(content__icontains=query)
            )

        # Handle tag filtering
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__name=tag)

        # Handle category filtering
        category = self.request.GET.get('category')
        if category:
            queryset = queryset.filter(category__name=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_articles'] = Article.objects.filter(
            status='published',
            is_featured=True
        )[:5]
        context['tags'] = Article.tags.most_common()[:10]
        context['categories'] = Article.objects.values_list(
            'category__name',
            flat=True
        ).distinct()
        return context

class ArticleDetailView(DetailView):
    model = Article
    template_name = 'articles/article_detail.html'
    context_object_name = 'article'

    def get_object(self):
        obj = super().get_object()
        if obj.status != 'published' and not self.request.user.is_staff:
            raise HttpResponseForbidden()
        return obj

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        article = self.get_object()
        
        # Get comments
        context['comments'] = Comment.objects.filter(
            article=article,
            is_approved=True
        ).order_by('-created_at')

        # Get related articles
        context['related_articles'] = Article.objects.filter(
            category=article.category,
            status='published'
        ).exclude(id=article.id)[:3]

        # Add comment form if user is authenticated
        if self.request.user.is_authenticated:
            context['can_comment'] = True

        return context

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        
        article = self.get_object()
        comment_text = request.POST.get('comment')
        
        if comment_text:
            Comment.objects.create(
                article=article,
                author=request.user,
                content=comment_text,
                is_approved=True  # Auto-approve for now
            )
        
        return self.get(request, *args, **kwargs)

def index(request):
    latest_articles = Article.objects.filter(
        status='published'
    ).order_by('-created_at')[:5]
    
    context = {
        'latest_articles': latest_articles,
    }
    return render(request, 'articles/index.html', context)
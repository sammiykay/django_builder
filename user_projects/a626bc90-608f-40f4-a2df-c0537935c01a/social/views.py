from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Q
from .models import Post, Profile, Comment
from .forms import PostForm, CommentForm, ProfileForm, UserForm

class FeedView(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'social/feed.html'
    context_object_name = 'posts'
    paginate_by = 10
    
    def get_queryset(self):
        following_users = self.request.user.following.values_list('user', flat=True)
        return Post.objects.filter(
            Q(author__in=following_users) | Q(author=self.request.user)
        ).select_related('author').prefetch_related('likes', 'comments')

class PostDetailView(DetailView):
    model = Post
    template_name = 'social/post_detail.html'
    context_object_name = 'post'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comment_form'] = CommentForm()
        return context

class PostCreateView(LoginRequiredMixin, CreateView):
    model = Post
    form_class = PostForm
    template_name = 'social/post_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

class PostUpdateView(LoginRequiredMixin, UpdateView):
    model = Post
    form_class = PostForm
    template_name = 'social/post_form.html'
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

class PostDeleteView(LoginRequiredMixin, DeleteView):
    model = Post
    template_name = 'social/post_confirm_delete.html'
    success_url = reverse_lazy('social:feed')
    
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)

class ProfileView(DetailView):
    model = Profile
    template_name = 'social/profile.html'
    context_object_name = 'profile'
    
    def get_object(self):
        username = self.kwargs.get('username')
        return get_object_or_404(Profile, user__username=username)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['posts'] = Post.objects.filter(author=self.object.user).select_related('author')
        if self.request.user.is_authenticated:
            context['is_following'] = self.object.followers.filter(id=self.request.user.id).exists()
        return context

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'social/profile_form.html'
    
    def get_object(self):
        return self.request.user.profile
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = UserForm(instance=self.request.user)
        return context
    
    def form_valid(self, form):
        user_form = UserForm(self.request.POST, instance=self.request.user)
        if user_form.is_valid():
            user_form.save()
        return super().form_valid(form)

class UserListView(ListView):
    model = User
    template_name = 'social/user_list.html'
    context_object_name = 'users'
    paginate_by = 20
    
    def get_queryset(self):
        query = self.request.GET.get('q')
        if query:
            return User.objects.filter(
                Q(username__icontains=query) | 
                Q(first_name__icontains=query) | 
                Q(last_name__icontains=query)
            ).select_related('profile')
        return User.objects.all().select_related('profile')

@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.likes.all():
        post.likes.remove(request.user)
        liked = False
    else:
        post.likes.add(request.user)
        liked = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'liked': liked,
            'likes_count': post.likes_count()
        })
    return redirect(post.get_absolute_url())

@login_required
def follow_user(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    profile = user_to_follow.profile
    
    if request.user in profile.followers.all():
        profile.followers.remove(request.user)
        following = False
    else:
        profile.followers.add(request.user)
        following = True
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'following': following,
            'followers_count': profile.followers_count()
        })
    return redirect(profile.get_absolute_url())

@login_required
def add_comment(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    return redirect(post.get_absolute_url())
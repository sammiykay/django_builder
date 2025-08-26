from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from .models import UserProfile
from .forms import UserProfileForm

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    template_name = 'accounts/profile_update.html'
    form_class = UserProfileForm
    success_url = reverse_lazy('accounts:profile')

    def get_object(self):
        return get_object_or_404(UserProfile, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_stats = {
            'total_todos': self.request.user.todos.count() if hasattr(self.request.user, 'todos') else 0,
            'completed_todos': self.request.user.todos.filter(completed=True).count() if hasattr(self.request.user, 'todos') else 0,
        }
        context['user_stats'] = user_stats
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

@login_required
def profile_view(request):
    user_profile = get_object_or_404(UserProfile, user=request.user)
    user_stats = {
        'total_todos': request.user.todos.count() if hasattr(request.user, 'todos') else 0,
        'completed_todos': request.user.todos.filter(completed=True).count() if hasattr(request.user, 'todos') else 0,
    }
    context = {
        'profile': user_profile,
        'user_stats': user_stats,
    }
    return render(request, 'accounts/profile.html', context)

class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = get_object_or_404(UserProfile, user=self.request.user)
        context['user_stats'] = {
            'total_todos': self.request.user.todos.count() if hasattr(self.request.user, 'todos') else 0,
            'completed_todos': self.request.user.todos.filter(completed=True).count() if hasattr(self.request.user, 'todos') else 0,
        }
        return context

@login_required
def ajax_update_profile(request):
    if request.method == 'POST' and request.is_ajax():
        profile = get_object_or_404(UserProfile, user=request.user)
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'errors': form.errors})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)
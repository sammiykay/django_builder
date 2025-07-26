from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView, TemplateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Q
from .models import UserProfile
from .forms import UserProfileForm

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = UserProfile
    form_class = UserProfileForm
    template_name = 'accounts/profile_update.html'
    success_url = reverse_lazy('profile_update')

    def get_object(self, queryset=None):
        return get_object_or_404(UserProfile, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_tasks = self.request.user.tasks.all()
        
        # Calculate completion rate
        total_tasks = user_tasks.count()
        completed_tasks = user_tasks.filter(completed=True).count()
        context['completion_rate'] = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        # Task statistics
        context['task_statistics'] = {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'pending_tasks': total_tasks - completed_tasks,
            'overdue_tasks': user_tasks.filter(due_date__lt=timezone.now(), completed=False).count()
        }

        return context

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating profile. Please check the form.')
        return super().form_invalid(form)

class AccountsHomeView(LoginRequiredMixin, TemplateView):
    template_name = 'accounts/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_profile'] = get_object_or_404(UserProfile, user=self.request.user)
        return context

def handler404(request, exception):
    return render(request, 'accounts/404.html', status=404)

def handler500(request):
    return render(request, 'accounts/500.html', status=500)
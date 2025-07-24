from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from .models import Task
from .forms import TaskForm

class TaskListView(LoginRequiredMixin, ListView):
    model = Task
    template_name = 'tasks/task_list.html'
    context_object_name = 'tasks'
    
    def get_queryset(self):
        return Task.objects.filter(assigned_to=self.request.user)

class TaskDetailView(LoginRequiredMixin, DetailView):
    model = Task
    template_name = 'tasks/task_detail.html'
    context_object_name = 'task'

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, 'Task created successfully!')
        return super().form_valid(form)

class TaskUpdateView(LoginRequiredMixin, UpdateView):
    model = Task
    form_class = TaskForm
    template_name = 'tasks/task_form.html'
    success_url = reverse_lazy('task-list')

    def form_valid(self, form):
        messages.success(self.request, 'Task updated successfully!')
        return super().form_valid(form)

class TaskDeleteView(LoginRequiredMixin, DeleteView):
    model = Task
    template_name = 'tasks/task_confirm_delete.html'
    success_url = reverse_lazy('task-list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Task deleted successfully!')
        return super().delete(request, *args, **kwargs)

@login_required
def toggle_task_status(request, pk):
    if request.method == 'POST' and request.is_ajax():
        task = get_object_or_404(Task, pk=pk)
        task.completed = not task.completed
        task.save()
        return JsonResponse({
            'status': 'success',
            'completed': task.completed
        })
        
    return JsonResponse({'status': 'error'}, status=400)
@login_required
def dashboard(request):
    context = {
        'pending_tasks': Task.objects.filter(assigned_to=request.user, completed=False),
        'completed_tasks': Task.objects.filter(assigned_to=request.user, completed=True),
        'total_tasks': Task.objects.filter(assigned_to=request.user).count(),
    }
    return render(request, 'tasks/dashboard.html', context)

def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'tasks/index.html')
from django.views.generic import ListView, DetailView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404
from .models import TaskList, Task

class TaskListListView(LoginRequiredMixin, ListView):
    model = TaskList
    template_name = 'tasks/tasklist_list.html'
    context_object_name = 'tasklists'

    def get_queryset(self):
        return TaskList.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_tasks = Task.objects.filter(task_list__owner=self.request.user)
        context['total_tasks'] = user_tasks.count()
        context['completed_tasks'] = user_tasks.filter(completed=True).count()
        return context

class TaskListDetailView(LoginRequiredMixin, DetailView):
    model = TaskList
    template_name = 'tasks/tasklist_detail.html'
    context_object_name = 'tasklist'

    def get_queryset(self):
        return TaskList.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tasks = self.object.tasks.all()
        context['tasks_by_status'] = {
            'pending': tasks.filter(completed=False),
            'completed': tasks.filter(completed=True)
        }
        return context

class TaskCreateView(LoginRequiredMixin, CreateView):
    model = Task
    template_name = 'tasks/task_form.html'
    fields = ['title', 'description', 'due_date', 'task_list']
    success_url = reverse_lazy('tasks:tasklist-list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['task_list'].queryset = TaskList.objects.filter(owner=self.request.user)
        return form

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_lists'] = TaskList.objects.filter(owner=self.request.user)
        return context
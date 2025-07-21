from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.contrib import messages
from .models import Project
from .forms import ProjectForm

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'

    def get_queryset(self):
        return Project.objects.filter(members=self.request.user)

class ProjectDetailView(LoginRequiredMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    success_url = reverse_lazy('projects:project-list')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        self.object.members.add(self.request.user)
        messages.success(self.request, 'Project created successfully!')
        return response

class ProjectUpdateView(LoginRequiredMixin, UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = 'projects/project_form.html'
    
    def get_success_url(self):
        return reverse_lazy('projects:project-detail', kwargs={'pk': self.object.pk})

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if request.user not in project.members.all():
            messages.error(request, "You don't have permission to edit this project.")
            return redirect('projects:project-list')
        return super().dispatch(request, *args, **kwargs)

class ProjectDeleteView(LoginRequiredMixin, DeleteView):
    model = Project
    success_url = reverse_lazy('projects:project-list')
    template_name = 'projects/project_confirm_delete.html'

    def dispatch(self, request, *args, **kwargs):
        project = self.get_object()
        if request.user != project.created_by:
            messages.error(request, "You don't have permission to delete this project.")
            return redirect('projects:project-list')
        return super().dispatch(request, *args, **kwargs)

@login_required
def project_members_update(request, pk):
    if request.method == 'POST' and request.is_ajax():
        project = get_object_or_404(Project, pk=pk)
        if request.user != project.created_by:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        member_id = request.POST.get('member_id')
        action = request.POST.get('action')
        
        try:
            if action == 'add':
                project.members.add(member_id)
            elif action == 'remove':
                project.members.remove(member_id)
            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def index(request):
    context = {
        'projects_count': Project.objects.filter(members=request.user).count(),
        'recent_projects': Project.objects.filter(members=request.user).order_by('-created_at')[:5]
    }
    return render(request, 'projects/index.html', context)
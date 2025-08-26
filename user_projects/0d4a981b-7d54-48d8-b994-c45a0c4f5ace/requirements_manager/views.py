from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.urls import reverse_lazy
from .models import Project, Requirement
from .forms import RequirementsUploadForm
import os

class ProjectListView(LoginRequiredMixin, ListView):
    model = Project
    template_name = 'requirements_manager/project_list.html'
    context_object_name = 'projects'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        validation_stats = {
            'total_projects': Project.objects.count(),
            'valid_requirements': Project.objects.filter(requirements__is_valid=True).distinct().count(),
            'invalid_requirements': Project.objects.filter(requirements__is_valid=False).distinct().count(),
        }
        context['validation_stats'] = validation_stats
        return context

class RequirementsValidatorView(LoginRequiredMixin, CreateView):
    template_name = 'requirements_manager/validate.html'
    form_class = RequirementsUploadForm
    success_url = reverse_lazy('requirements_manager:project_list')

    def form_valid(self, form):
        requirements_file = form.cleaned_data['requirements_file']
        project = form.cleaned_data['project']
        
        try:
            # Read and validate requirements file
            requirements_content = requirements_file.read().decode('utf-8')
            requirements_list = requirements_content.split('\n')
            
            # Create requirement objects
            for req in requirements_list:
                if req.strip():
                    Requirement.objects.create(
                        project=project,
                        package_name=req.split('==')[0].strip() if '==' in req else req.strip(),
                        version=req.split('==')[1].strip() if '==' in req else None,
                        is_valid=True  # Basic validation, enhance as needed
                    )
            
            return JsonResponse({
                'status': 'success',
                'message': 'Requirements validated successfully'
            }) if self.request.is_ajax() else super().form_valid(form)
            
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            }) if self.request.is_ajax() else self.form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['validation_result'] = None
        if self.request.GET.get('project_id'):
            project = Project.objects.get(id=self.request.GET.get('project_id'))
            context['validation_result'] = {
                'project': project,
                'requirements': project.requirement_set.all()
            }
        return context

def index(request):
    """Basic index view for the requirements manager app"""
    context = {
        'total_projects': Project.objects.count(),
        'total_requirements': Requirement.objects.count(),
    }
    return render(request, 'requirements_manager/index.html', context)
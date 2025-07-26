from django.shortcuts import render, redirect
from .models import Project

def create_project(request):
    # Import form here to avoid circular import
    from .forms import ProjectForm
    
    if request.method == 'POST':
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('project_list')
    else:
        form = ProjectForm()
    
    return render(request, 'projects/create_project.html', {'form': form})
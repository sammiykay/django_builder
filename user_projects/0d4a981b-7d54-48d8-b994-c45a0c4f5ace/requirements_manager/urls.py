from django.urls import path
from . import views

app_name = 'requirements_manager'

urlpatterns = [
    path('projects/', views.ProjectListView.as_view(), name='project_list'),
    path('validate/', views.RequirementsValidatorView.as_view(), name='validate_requirements'),
    path('projects/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    path('projects/create/', views.ProjectCreateView.as_view(), name='project_create'),
    path('projects/<int:pk>/update/', views.ProjectUpdateView.as_view(), name='project_update'),
    path('projects/<int:pk>/delete/', views.ProjectDeleteView.as_view(), name='project_delete'),
    path('requirements/create/', views.RequirementCreateView.as_view(), name='requirement_create'),
    path('requirements/<int:pk>/update/', views.RequirementUpdateView.as_view(), name='requirement_update'),
    path('requirements/<int:pk>/delete/', views.RequirementDeleteView.as_view(), name='requirement_delete'),
]
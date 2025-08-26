from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    path('', views.task_list, name='task_list'),
    path('lists/', views.tasklist_list, name='tasklist_list'),
    path('lists/create/', views.tasklist_create, name='tasklist_create'),
    path('lists/<int:pk>/', views.tasklist_detail, name='tasklist_detail'),
    path('lists/<int:pk>/update/', views.tasklist_update, name='tasklist_update'),
    path('lists/<int:pk>/delete/', views.tasklist_delete, name='tasklist_delete'),
    path('create/', views.task_create, name='task_create'),
    path('<int:pk>/', views.task_detail, name='task_detail'),
    path('<int:pk>/update/', views.task_update, name='task_update'),
    path('<int:pk>/delete/', views.task_delete, name='task_delete'),
    path('<int:pk>/toggle/', views.task_toggle_complete, name='task_toggle_complete'),
]
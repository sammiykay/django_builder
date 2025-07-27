from django.urls import path
from . import views

app_name = 'recipes'

urlpatterns = [
    path('', views.RecipeListView.as_view(), name='recipe_list'),
    path('<slug:slug>/', views.RecipeDetailView.as_view(), name='recipe_detail'),
    path('create/', views.RecipeCreateView.as_view(), name='recipe_create'),
    path('<slug:slug>/update/', views.RecipeUpdateView.as_view(), name='recipe_update'),
    path('<slug:slug>/delete/', views.RecipeDeleteView.as_view(), name='recipe_delete'),
]
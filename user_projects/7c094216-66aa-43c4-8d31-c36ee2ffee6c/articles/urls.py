from django.urls import path
from . import views

app_name = 'articles'

urlpatterns = [
    path('', views.article_list, name='article_list'),
    path('create/', views.article_create, name='article_create'),
    path('<int:pk>/', views.article_detail, name='article_detail'),
    path('<int:pk>/edit/', views.article_update, name='article_update'),
    path('<int:pk>/delete/', views.article_delete, name='article_delete'),
    path('<int:article_pk>/comment/create/', views.comment_create, name='comment_create'),
    path('<int:article_pk>/comment/<int:pk>/delete/', views.comment_delete, name='comment_delete'),
]
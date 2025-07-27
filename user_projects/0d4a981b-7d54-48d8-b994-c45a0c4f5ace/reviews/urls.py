from django.urls import path
from . import views

app_name = 'reviews'

urlpatterns = [
    path('', views.review_list, name='review_list'),
    path('create/', views.review_create, name='review_create'),
    path('<int:pk>/', views.review_detail, name='review_detail'),
    path('<int:pk>/update/', views.review_update, name='review_update'),
    path('<int:pk>/delete/', views.review_delete, name='review_delete'),
    path('ratings/', views.rating_list, name='rating_list'),
    path('ratings/create/', views.rating_create, name='rating_create'),
    path('ratings/<int:pk>/', views.rating_detail, name='rating_detail'),
    path('ratings/<int:pk>/update/', views.rating_update, name='rating_update'),
    path('ratings/<int:pk>/delete/', views.rating_delete, name='rating_delete'),
]
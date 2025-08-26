from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    path('', views.FeedView.as_view(), name='feed'),
    path('post/<int:pk>/', views.PostDetailView.as_view(), name='post_detail'),
    path('post/new/', views.PostCreateView.as_view(), name='post_create'),
    path('post/<int:pk>/edit/', views.PostUpdateView.as_view(), name='post_update'),
    path('post/<int:pk>/delete/', views.PostDeleteView.as_view(), name='post_delete'),
    path('post/<int:pk>/like/', views.like_post, name='like_post'),
    path('post/<int:pk>/comment/', views.add_comment, name='add_comment'),
    path('profile/<str:username>/', views.ProfileView.as_view(), name='profile'),
    path('profile/<str:username>/follow/', views.follow_user, name='follow_user'),
    path('settings/profile/', views.ProfileUpdateView.as_view(), name='profile_update'),
    path('users/', views.UserListView.as_view(), name='user_list'),
]
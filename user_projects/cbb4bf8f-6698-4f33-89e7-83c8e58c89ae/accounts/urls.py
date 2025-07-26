from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('profile/', views.ProfileUpdateView.as_view(), name='profile_update'),
]
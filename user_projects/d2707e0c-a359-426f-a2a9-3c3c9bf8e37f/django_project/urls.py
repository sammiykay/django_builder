"""
URL configuration for django_project project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('main/', include('main.urls')),

    path('admin/', admin.site.urls),
]

from django.urls import path
from . import views

urlpatterns = [
    # Your existing URL patterns
    path('contact/', views.contact, name='contact'),
]
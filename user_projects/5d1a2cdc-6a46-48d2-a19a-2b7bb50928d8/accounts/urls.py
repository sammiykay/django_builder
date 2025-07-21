from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # The homepage or index page
    path('', views.dashboard, name='index'),  # Assuming you want to show the user's dashboard here

    # Team-related URLs
    path('teams/', views.TeamListView.as_view(), name='team_list'),  # List of teams
    path('teams/create/', views.TeamCreateView.as_view(), name='team_create'),  # Create a new team
    path('teams/<int:pk>/', views.TeamDetailView.as_view(), name='team_detail'),  # Team detail
    # path('teams/<int:pk>/update/', views.TeamUpdateView.as_view(), name='team_update'),  # Team update (add this view if needed)
    # path('teams/<int:pk>/delete/', views.TeamDeleteView.as_view(), name='team_delete'),  # Team delete (add this view if needed)

    # AJAX-based URLs for adding/removing team members
    path('teams/<int:team_id>/add_member/', views.add_team_member, name='add_team_member'),  # Add member to a team
    path('teams/<int:team_id>/remove_member/<int:member_id>/', views.remove_team_member, name='remove_team_member'),  # Remove member from a team

    # Optional: Add more URLs for team members or other related views if needed
]

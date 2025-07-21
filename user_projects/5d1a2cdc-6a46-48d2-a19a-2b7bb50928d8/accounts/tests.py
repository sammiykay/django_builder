from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import TeamMember, Team
import pytest
from django.core.exceptions import ValidationError

@pytest.mark.django_db
class TestTeamModel:
    def test_team_creation(self):
        team = Team.objects.create(
            name="Test Team",
            description="Test Description"
        )
        assert team.name == "Test Team"
        assert team.description == "Test Description"

    def test_team_str_representation(self):
        team = Team.objects.create(name="Test Team")
        assert str(team) == "Test Team"

    def test_team_name_max_length(self):
        with pytest.raises(ValidationError):
            team = Team.objects.create(
                name="A" * 256,  # Assuming max_length is 255
                description="Test Description"
            )
            team.full_clean()

@pytest.mark.django_db
class TestTeamMemberModel:
    def test_team_member_creation(self):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        team = Team.objects.create(name="Test Team")
        team_member = TeamMember.objects.create(
            user=user,
            team=team,
            role="member"
        )
        assert team_member.user == user
        assert team_member.team == team
        assert team_member.role == "member"

    def test_team_member_str_representation(self):
        user = User.objects.create_user(username="testuser")
        team = Team.objects.create(name="Test Team")
        team_member = TeamMember.objects.create(
            user=user,
            team=team,
            role="member"
        )
        assert str(team_member) == "testuser - Test Team"

@pytest.mark.django_db
class TestTeamCreateView:
    def test_team_create_view_get(self, client):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        response = client.get(reverse('team-create'))
        assert response.status_code == 200
        assert 'form' in response.context

    def test_team_create_view_post(self, client):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        data = {
            'name': 'New Team',
            'description': 'New Team Description'
        }
        response = client.post(reverse('team-create'), data)
        assert response.status_code == 302  # Redirect after successful creation
        assert Team.objects.filter(name='New Team').exists()

    def test_team_create_view_unauthorized(self, client):
        response = client.get(reverse('team-create'))
        assert response.status_code == 302  # Redirect to login page

    def test_team_create_view_invalid_data(self, client):
        user = User.objects.create_user(
            username="testuser",
            password="testpass123"
        )
        client.login(username="testuser", password="testpass123")
        data = {
            'name': '',  # Invalid: empty name
            'description': 'New Team Description'
        }
        response = client.post(reverse('team-create'), data)
        assert response.status_code == 200  # Form redisplay
        assert not Team.objects.filter(description='New Team Description').exists()

@pytest.fixture
def authenticated_client():
    client = Client()
    user = User.objects.create_user(
        username="testuser",
        password="testpass123"
    )
    client.login(username="testuser", password="testpass123")
    return client

@pytest.mark.django_db
class TestTeamMemberIntegration:
    def test_add_multiple_members_to_team(self):
        team = Team.objects.create(name="Test Team")
        users = [
            User.objects.create_user(username=f"user{i}")
            for i in range(3)
        ]
        
        for user in users:
            TeamMember.objects.create(
                user=user,
                team=team,
                role="member"
            )
        
        assert team.teammember_set.count() == 3

    def test_team_member_unique_constraint(self):
        user = User.objects.create_user(username="testuser")
        team = Team.objects.create(name="Test Team")
        TeamMember.objects.create(user=user, team=team, role="member")
        
        with pytest.raises(Exception):  # Should raise unique constraint violation
            TeamMember.objects.create(user=user, team=team, role="admin")

@pytest.mark.django_db
class TestTeamEdgeCases:
    def test_team_with_special_characters(self):
        team = Team.objects.create(
            name="Test!@#$%^&*()",
            description="Special chars test"
        )
        assert Team.objects.filter(name="Test!@#$%^&*()").exists()

    def test_team_with_long_description(self):
        long_description = "A" * 1000
        team = Team.objects.create(
            name="Test Team",
            description=long_description
        )
        assert team.description == long_description

    def test_delete_team_cascade(self):
        team = Team.objects.create(name="Test Team")
        user = User.objects.create_user(username="testuser")
        team_member = TeamMember.objects.create(
            user=user,
            team=team,
            role="member"
        )
        
        team.delete()
        assert not TeamMember.objects.filter(id=team_member.id).exists()
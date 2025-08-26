from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
from accounts.forms import UserProfileForm
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
class TestUserProfile:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def user_profile(self, user):
        return UserProfile.objects.create(
            user=user,
            bio='Test bio',
            location='Test location'
        )

    @pytest.fixture
    def client(self):
        return Client()

    def test_user_profile_creation(self, user):
        profile = UserProfile.objects.create(
            user=user,
            bio='Test bio',
            location='Test location'
        )
        assert profile.user == user
        assert profile.bio == 'Test bio'
        assert profile.location == 'Test location'

    def test_user_profile_str_method(self, user_profile):
        assert str(user_profile) == f'Profile for {user_profile.user.username}'

    def test_profile_update_view_get(self, client, user, user_profile):
        client.force_login(user)
        url = reverse('profile_update')
        response = client.get(url)
        assert response.status_code == 200
        assert 'form' in response.context

    def test_profile_update_view_post(self, client, user, user_profile):
        client.force_login(user)
        url = reverse('profile_update')
        data = {
            'bio': 'Updated bio',
            'location': 'Updated location'
        }
        response = client.post(url, data)
        assert response.status_code == 302
        user_profile.refresh_from_db()
        assert user_profile.bio == 'Updated bio'
        assert user_profile.location == 'Updated location'

    def test_profile_update_view_unauthorized(self, client):
        url = reverse('profile_update')
        response = client.get(url)
        assert response.status_code == 302
        assert '/login/' in response.url

    def test_profile_update_with_invalid_data(self, client, user, user_profile):
        client.force_login(user)
        url = reverse('profile_update')
        data = {
            'bio': 'x' * 1000,  # Exceeding max length
            'location': ''
        }
        response = client.post(url, data)
        assert response.status_code == 200
        assert 'form' in response.context
        assert response.context['form'].errors

    def test_profile_update_with_image(self, client, user, user_profile):
        client.force_login(user)
        url = reverse('profile_update')
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        data = {
            'bio': 'Test bio',
            'location': 'Test location',
            'profile_picture': image
        }
        response = client.post(url, data, format='multipart')
        assert response.status_code == 302
        user_profile.refresh_from_db()
        assert user_profile.profile_picture is not None

    def test_profile_max_length_constraints(self, user):
        with pytest.raises(Exception):
            UserProfile.objects.create(
                user=user,
                bio='x' * 1001,
                location='x' * 101
            )

    def test_profile_unique_user_constraint(self, user, user_profile):
        with pytest.raises(Exception):
            UserProfile.objects.create(
                user=user,
                bio='Another bio',
                location='Another location'
            )

class TestUserProfileForm:
    def test_valid_form(self):
        form_data = {
            'bio': 'Test bio',
            'location': 'Test location'
        }
        form = UserProfileForm(data=form_data)
        assert form.is_valid()

    def test_invalid_form(self):
        form_data = {
            'bio': 'x' * 1000,
            'location': ''
        }
        form = UserProfileForm(data=form_data)
        assert not form.is_valid()

    def test_form_empty_data(self):
        form = UserProfileForm(data={})
        assert not form.is_valid()
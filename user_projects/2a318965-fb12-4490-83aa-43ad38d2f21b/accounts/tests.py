from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import Profile
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

@pytest.mark.django_db
class TestProfile:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def profile(self, user):
        return Profile.objects.create(
            user=user,
            bio='Test bio',
            location='Test location'
        )

    @pytest.fixture
    def client(self):
        return Client()

    def test_profile_creation(self, profile):
        assert profile.user.username == 'testuser'
        assert profile.bio == 'Test bio'
        assert profile.location == 'Test location'

    def test_profile_str_method(self, profile):
        assert str(profile) == 'testuser Profile'

    def test_profile_auto_creation_on_user_save(self):
        user = User.objects.create_user(
            username='newuser',
            email='new@example.com',
            password='newpass123'
        )
        assert Profile.objects.filter(user=user).exists()

    def test_profile_detail_view(self, client, profile):
        url = reverse('profile-detail', kwargs={'pk': profile.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert 'Test bio' in str(response.content)

    def test_profile_detail_view_not_found(self, client):
        url = reverse('profile-detail', kwargs={'pk': 999})
        response = client.get(url)
        assert response.status_code == 404

    def test_profile_update(self, profile):
        profile.bio = 'Updated bio'
        profile.save()
        updated_profile = Profile.objects.get(id=profile.id)
        assert updated_profile.bio == 'Updated bio'

    def test_profile_delete(self, profile):
        profile_id = profile.id
        profile.delete()
        with pytest.raises(Profile.DoesNotExist):
            Profile.objects.get(id=profile_id)

    def test_profile_with_image(self, user):
        image = SimpleUploadedFile(
            "test_image.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        profile = Profile.objects.create(
            user=user,
            bio='Test bio',
            location='Test location',
            profile_picture=image
        )
        assert profile.profile_picture.name is not None

    def test_profile_detail_view_context(self, client, profile):
        url = reverse('profile-detail', kwargs={'pk': profile.pk})
        response = client.get(url)
        assert response.context['profile'] == profile

    def test_profile_detail_view_template(self, client, profile):
        url = reverse('profile-detail', kwargs={'pk': profile.pk})
        response = client.get(url)
        assert 'accounts/profile_detail.html' in [t.name for t in response.templates]

    @pytest.mark.parametrize(
        'bio,location',
        [
            ('', ''),  # Empty fields
            ('A' * 500, 'Test'),  # Long bio
            ('Test', 'A' * 100),  # Long location
            (None, None),  # Null values
        ]
    )
    def test_profile_edge_cases(self, user, bio, location):
        profile = Profile.objects.create(
            user=user,
            bio=bio,
            location=location
        )
        assert Profile.objects.filter(id=profile.id).exists()

    def test_unauthorized_profile_access(self, client, profile):
        # Test accessing profile detail view without authentication
        url = reverse('profile-detail', kwargs={'pk': profile.pk})
        response = client.get(url)
        assert response.status_code == 200  # or 302 if login required

    def test_profile_unique_user_constraint(self, user):
        Profile.objects.create(
            user=user,
            bio='First profile'
        )
        with pytest.raises(Exception):
            Profile.objects.create(
                user=user,
                bio='Second profile'
            )
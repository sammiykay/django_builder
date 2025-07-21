from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from accounts.models import UserProfile
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
            location='Test City'
        )

    @pytest.fixture
    def client(self):
        return Client()

    def test_user_profile_creation(self, user_profile):
        assert user_profile.user.username == 'testuser'
        assert user_profile.bio == 'Test bio'
        assert user_profile.location == 'Test City'

    def test_user_profile_str_method(self, user_profile):
        assert str(user_profile) == 'testuser Profile'

    def test_profile_detail_view_authenticated(self, client, user_profile):
        client.login(username='testuser', password='testpass123')
        url = reverse('profile-detail', kwargs={'pk': user_profile.pk})
        response = client.get(url)
        assert response.status_code == 200
        assert 'testuser' in str(response.content)

    def test_profile_detail_view_unauthenticated(self, client, user_profile):
        url = reverse('profile-detail', kwargs={'pk': user_profile.pk})
        response = client.get(url)
        assert response.status_code == 302  # Redirects to login

    def test_profile_update(self, user_profile):
        user_profile.bio = 'Updated bio'
        user_profile.save()
        updated_profile = UserProfile.objects.get(pk=user_profile.pk)
        assert updated_profile.bio == 'Updated bio'

    def test_profile_with_avatar(self, user):
        avatar = SimpleUploadedFile(
            "test_avatar.jpg",
            b"file_content",
            content_type="image/jpeg"
        )
        profile = UserProfile.objects.create(
            user=user,
            bio='Test bio',
            avatar=avatar
        )
        assert profile.avatar is not None

    def test_profile_detail_view_nonexistent_profile(self, client):
        client.login(username='testuser', password='testpass123')
        url = reverse('profile-detail', kwargs={'pk': 99999})
        response = client.get(url)
        assert response.status_code == 404

    @pytest.mark.parametrize(
        'bio_text',
        [
            'Short bio',
            'A' * 500,  # Test max length
            '',  # Empty bio
            None,  # Null bio
        ]
    )
    def test_profile_bio_variations(self, user, bio_text):
        profile = UserProfile.objects.create(
            user=user,
            bio=bio_text
        )
        assert profile.bio == (bio_text or '')

    def test_multiple_profiles_same_location(self, user):
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        profile1 = UserProfile.objects.create(
            user=user,
            location='Same City'
        )
        profile2 = UserProfile.objects.create(
            user=user2,
            location='Same City'
        )
        assert profile1.location == profile2.location

    def test_profile_deletion_cascade(self, user_profile):
        user_id = user_profile.user.id
        user_profile.user.delete()
        with pytest.raises(UserProfile.DoesNotExist):
            UserProfile.objects.get(user_id=user_id)

    def test_profile_detail_view_post_method(self, client, user_profile):
        client.login(username='testuser', password='testpass123')
        url = reverse('profile-detail', kwargs={'pk': user_profile.pk})
        response = client.post(url, {'bio': 'Updated via POST'})
        assert response.status_code == 405  # Method not allowed

    def test_profile_without_optional_fields(self, user):
        profile = UserProfile.objects.create(user=user)
        assert profile.bio == ''
        assert profile.location == ''
        assert profile.avatar == ''
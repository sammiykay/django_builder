from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from blog.models import Post, Comment
from blog.forms import PostForm, CommentForm
import pytest
from django.utils import timezone

@pytest.mark.django_db
class TestPostModel:
    def test_post_creation(self):
        user = User.objects.create_user(username='testuser', password='12345')
        post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=user
        )
        assert post.title == 'Test Post'
        assert post.content == 'Test Content'
        assert post.author == user
        assert isinstance(post.created_date, timezone.datetime)

    def test_post_str_representation(self):
        user = User.objects.create_user(username='testuser', password='12345')
        post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=user
        )
        assert str(post) == 'Test Post'

@pytest.mark.django_db
class TestCommentModel:
    def test_comment_creation(self):
        user = User.objects.create_user(username='testuser', password='12345')
        post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=user
        )
        comment = Comment.objects.create(
            post=post,
            author=user,
            content='Test Comment'
        )
        assert comment.content == 'Test Comment'
        assert comment.post == post
        assert comment.author == user

@pytest.mark.django_db
class TestPostViews:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=self.user
        )

    def test_post_list_view(self):
        response = self.client.get(reverse('post_list'))
        assert response.status_code == 200
        assert 'Test Post' in str(response.content)

    def test_post_detail_view(self):
        response = self.client.get(reverse('post_detail', kwargs={'pk': self.post.pk}))
        assert response.status_code == 200
        assert 'Test Post' in str(response.content)

    def test_post_create_view_unauthorized(self):
        response = self.client.get(reverse('post_create'))
        assert response.status_code == 302  # Redirect to login

    def test_post_create_view_authorized(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.get(reverse('post_create'))
        assert response.status_code == 200

    def test_post_create_view_submission(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('post_create'), {
            'title': 'New Post',
            'content': 'New Content'
        })
        assert response.status_code == 302  # Redirect after successful creation
        assert Post.objects.filter(title='New Post').exists()

@pytest.mark.django_db
class TestForms:
    def test_post_form_valid(self):
        form_data = {
            'title': 'Test Title',
            'content': 'Test Content'
        }
        form = PostForm(data=form_data)
        assert form.is_valid()

    def test_post_form_invalid(self):
        form_data = {
            'title': '',  # Title is required
            'content': 'Test Content'
        }
        form = PostForm(data=form_data)
        assert not form.is_valid()

    def test_comment_form_valid(self):
        form_data = {
            'content': 'Test Comment'
        }
        form = CommentForm(data=form_data)
        assert form.is_valid()

@pytest.mark.django_db
class TestEdgeCases:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_post_with_long_title(self):
        long_title = 'x' * 300  # Assuming max_length is less than this
        post = Post(title=long_title, content='Test Content', author=self.user)
        with pytest.raises(Exception):
            post.save()

    def test_nonexistent_post_detail(self):
        response = self.client.get(reverse('post_detail', kwargs={'pk': 99999}))
        assert response.status_code == 404

    def test_create_post_with_special_characters(self):
        self.client.login(username='testuser', password='12345')
        response = self.client.post(reverse('post_create'), {
            'title': '!@#$%^&*()',
            'content': 'Test Content'
        })
        assert response.status_code == 302
        assert Post.objects.filter(title='!@#$%^&*()').exists()

    def test_empty_comment(self):
        post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=self.user
        )
        comment = Comment(post=post, author=self.user, content='')
        with pytest.raises(Exception):
            comment.save()
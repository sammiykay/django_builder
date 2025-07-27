from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from blog.models import Post, Comment
from blog.forms import CommentForm
import pytest
from django.utils import timezone

@pytest.mark.django_db
class TestPostModel:
    def test_post_creation(self):
        user = User.objects.create_user(username='testuser', password='12345')
        post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=user,
            status='published'
        )
        assert post.title == 'Test Post'
        assert post.author == user
        assert str(post) == 'Test Post'

    def test_post_slug_generation(self):
        user = User.objects.create_user(username='testuser', password='12345')
        post = Post.objects.create(
            title='Test Post Title',
            content='Test Content',
            author=user
        )
        assert post.slug == 'test-post-title'

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
            name='Test Commenter',
            email='test@example.com',
            body='Test Comment'
        )
        assert comment.post == post
        assert str(comment) == f'Comment by Test Commenter on Test Post'

@pytest.mark.django_db
class TestPostViews:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=self.user,
            status='published'
        )

    def test_post_list_view(self):
        response = self.client.get(reverse('blog:post_list'))
        assert response.status_code == 200
        assert 'Test Post' in str(response.content)

    def test_post_detail_view(self):
        response = self.client.get(reverse('blog:post_detail', args=[self.post.slug]))
        assert response.status_code == 200
        assert 'Test Post' in str(response.content)

    def test_post_detail_view_404(self):
        response = self.client.get(reverse('blog:post_detail', args=['non-existent-post']))
        assert response.status_code == 404

@pytest.mark.django_db
class TestCommentForm:
    def setup_method(self):
        self.user = User.objects.create_user(username='testuser', password='12345')
        self.post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=self.user
        )

    def test_valid_comment_form(self):
        form_data = {
            'name': 'Test Commenter',
            'email': 'test@example.com',
            'body': 'Test Comment'
        }
        form = CommentForm(data=form_data)
        assert form.is_valid()

    def test_invalid_comment_form(self):
        form_data = {
            'name': '',
            'email': 'invalid-email',
            'body': ''
        }
        form = CommentForm(data=form_data)
        assert not form.is_valid()

@pytest.mark.django_db
class TestEdgeCases:
    def setup_method(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')

    def test_very_long_post_title(self):
        long_title = 'x' * 200
        post = Post.objects.create(
            title=long_title,
            content='Test Content',
            author=self.user
        )
        assert len(post.slug) <= 50

    def test_duplicate_post_titles(self):
        post1 = Post.objects.create(
            title='Same Title',
            content='Content 1',
            author=self.user
        )
        post2 = Post.objects.create(
            title='Same Title',
            content='Content 2',
            author=self.user
        )
        assert post1.slug != post2.slug

    def test_empty_content_post(self):
        post = Post.objects.create(
            title='Test Title',
            content='',
            author=self.user
        )
        assert post.content == ''

    def test_future_dated_post(self):
        future_post = Post.objects.create(
            title='Future Post',
            content='Future Content',
            author=self.user,
            publish=timezone.now() + timezone.timedelta(days=10)
        )
        response = self.client.get(reverse('blog:post_list'))
        assert 'Future Post' not in str(response.content)
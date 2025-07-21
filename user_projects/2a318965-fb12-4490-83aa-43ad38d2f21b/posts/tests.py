from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from .models import Post, Comment
import pytest

User = get_user_model()

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
        assert str(post) == 'Test Post'

    def test_post_update(self):
        user = User.objects.create_user(username='testuser', password='12345')
        post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=user
        )
        post.title = 'Updated Title'
        post.save()
        assert post.title == 'Updated Title'

    def test_post_deletion(self):
        user = User.objects.create_user(username='testuser', password='12345')
        post = Post.objects.create(
            title='Test Post',
            content='Test Content',
            author=user
        )
        post_id = post.id
        post.delete()
        with pytest.raises(Post.DoesNotExist):
            Post.objects.get(id=post_id)

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
        assert comment.author == user
        assert comment.post == post
        assert str(comment) == 'Comment by testuser on Test Post'

    def test_comment_update(self):
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
        comment.content = 'Updated Comment'
        comment.save()
        assert comment.content == 'Updated Comment'

    def test_comment_deletion(self):
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
        comment_id = comment.id
        comment.delete()
        with pytest.raises(Comment.DoesNotExist):
            Comment.objects.get(id=comment_id)

    def test_cascade_delete(self):
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
        post.delete()
        with pytest.raises(Comment.DoesNotExist):
            Comment.objects.get(id=comment.id)

@pytest.mark.django_db
class TestEdgeCases:
    def test_empty_fields(self):
        user = User.objects.create_user(username='testuser', password='12345')
        with pytest.raises(Exception):
            Post.objects.create(
                title='',
                content='',
                author=user
            )

    def test_long_content(self):
        user = User.objects.create_user(username='testuser', password='12345')
        long_content = 'x' * 10000
        post = Post.objects.create(
            title='Test Post',
            content=long_content,
            author=user
        )
        assert post.content == long_content

    def test_special_characters(self):
        user = User.objects.create_user(username='testuser', password='12345')
        special_title = '!@#$%^&*()'
        post = Post.objects.create(
            title=special_title,
            content='Test Content',
            author=user
        )
        assert post.title == special_title

@pytest.fixture
def client():
    return Client()

@pytest.fixture
def test_user():
    return User.objects.create_user(username='testuser', password='12345')

@pytest.fixture
def test_post(test_user):
    return Post.objects.create(
        title='Test Post',
        content='Test Content',
        author=test_user
    )

@pytest.fixture
def test_comment(test_post, test_user):
    return Comment.objects.create(
        post=test_post,
        author=test_user,
        content='Test Comment'
    )
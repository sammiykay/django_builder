from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse

User = get_user_model()

class Post(models.Model):
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Author',
        help_text='User who created this post'
    )
    content = models.TextField(
        verbose_name='Content',
        help_text='Post content'
    )
    media = models.FileField(
        upload_to='posts/',
        blank=True,
        verbose_name='Media',
        help_text='Image, video, or other media files'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Updated at'
    )
    likes = models.ManyToManyField(
        User,
        related_name='liked_posts',
        blank=True,
        verbose_name='Likes',
        help_text='Users who liked this post'
    )
    hashtags = models.ManyToManyField(
        'Hashtag',
        blank=True,
        verbose_name='Hashtags',
        help_text='Hashtags associated with this post'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Post'
        verbose_name_plural = 'Posts'

    def __str__(self):
        return f'{self.author.username} - {self.created_at.strftime("%Y-%m-%d %H:%M")}'

    def get_absolute_url(self):
        return reverse('post-detail', kwargs={'pk': self.pk})

    def get_likes_count(self):
        return self.likes.count()

    def get_comments_count(self):
        return self.comment_set.count()

class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        verbose_name='Post',
        help_text='Post this comment belongs to'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Author',
        help_text='User who wrote this comment'
    )
    content = models.TextField(
        verbose_name='Content',
        help_text='Comment content'
    )
    parent = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        related_name='replies',
        on_delete=models.CASCADE,
        verbose_name='Parent comment',
        help_text='Parent comment if this is a reply'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post}'

    def get_replies(self):
        return self.replies.all()

class Hashtag(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name='Name',
        help_text='Hashtag name without # symbol'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created at'
    )

    class Meta:
        verbose_name = 'Hashtag'
        verbose_name_plural = 'Hashtags'

    def __str__(self):
        return f'#{self.name}'
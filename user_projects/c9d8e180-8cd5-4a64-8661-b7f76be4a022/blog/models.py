from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from ckeditor.fields import RichTextField
from django.utils.text import slugify

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = RichTextField()
    excerpt = models.TextField(blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    featured_image = models.ImageField(upload_to='blog/', blank=True, null=True)
    reading_time = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def calculate_reading_time(self):
        words_per_minute = 200
        word_count = len(self.content.split())
        self.reading_time = max(1, round(word_count / words_per_minute))
        return self.reading_time

    def get_related_posts(self):
        return Post.objects.filter(status='published').exclude(id=self.id)[:3]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        self.calculate_reading_time()
        super().save(*args, **kwargs)

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'

    def __str__(self):
        return f'Comment by {self.author.username} on {self.post.title}'

    def get_replies(self):
        return Comment.objects.filter(parent=self)
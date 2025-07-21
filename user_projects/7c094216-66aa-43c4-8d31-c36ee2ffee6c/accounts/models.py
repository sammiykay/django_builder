from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Count

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name='User'
    )
    bio = models.TextField(
        blank=True,
        verbose_name='Biography',
        help_text='A brief description about yourself'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        verbose_name='Profile Picture',
        help_text='Upload your profile picture'
    )
    website = models.URLField(
        blank=True,
        verbose_name='Website',
        help_text='Your personal or professional website'
    )
    social_links = models.JSONField(
        default=dict,
        verbose_name='Social Media Links',
        help_text='Your social media profile links'
    )

    class Meta:
        ordering = ['-user__date_joined']
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'username': self.user.username})

    def get_total_articles(self):
        return self.user.articles.count()
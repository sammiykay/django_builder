from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name='User',
        help_text='User associated with this profile'
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        verbose_name='Profile Picture',
        help_text='Upload a profile picture',
        blank=True
    )
    bio = models.TextField(
        max_length=500,
        blank=True,
        verbose_name='Biography',
        help_text='Tell us about yourself'
    )
    location = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Location',
        help_text='Where are you located?'
    )
    website = models.URLField(
        blank=True,
        verbose_name='Website',
        help_text='Your personal website or blog'
    )
    following = models.ManyToManyField(
        User,
        related_name='followers',
        blank=True,
        verbose_name='Following',
        help_text='Users that this profile is following'
    )

    class Meta:
        ordering = ['-user__date_joined']
        verbose_name = 'Profile'
        verbose_name_plural = 'Profiles'

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_absolute_url(self):
        return reverse('profile_detail', kwargs={'username': self.user.username})

    def get_following_count(self):
        return self.following.count()

    def get_followers_count(self):
        return self.user.followers.count()
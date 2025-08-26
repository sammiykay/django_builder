from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class UserProfile(models.Model):
    THEME_CHOICES = [
        ('LIGHT', 'Light'),
        ('DARK', 'Dark'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='The user this profile belongs to'
    )
    
    theme_preference = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='LIGHT',
        help_text='User preferred theme for the application'
    )
    
    notification_preference = models.BooleanField(
        default=True,
        help_text='Whether the user wants to receive notifications'
    )

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'

    def __str__(self):
        return f'{self.user.username}\'s Profile'

    def get_absolute_url(self):
        return reverse('profile-detail', kwargs={'pk': self.pk})
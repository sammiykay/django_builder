from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models import Avg

THEME_CHOICES = [
    ('LIGHT', 'Light Theme'),
    ('DARK', 'Dark Theme'),
]

class UserProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    theme_preference = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='LIGHT',
        help_text='Select your preferred theme'
    )
    notification_preference = models.BooleanField(
        default=True,
        help_text='Receive notifications for tasks'
    )

    def __str__(self):
        return f"{self.user.username}'s Profile"

    def get_absolute_url(self):
        return reverse('profile-detail', kwargs={'pk': self.pk})

    def get_completion_rate(self):
        tasks = self.user.tasks.all()
        if not tasks:
            return 0
        completed = tasks.filter(completed=True).count()
        return (completed / tasks.count()) * 100

    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
        ordering = ['user__username']
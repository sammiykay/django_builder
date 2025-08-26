from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField()
    theme_preference = models.CharField(max_length=10)
    notification_preference = models.BooleanField()

    def __str__(self):
        return self.user


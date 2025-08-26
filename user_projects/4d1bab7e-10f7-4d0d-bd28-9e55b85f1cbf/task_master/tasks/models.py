from django.db import models
from django.contrib.auth.models import User

class TaskList(models.Model):
    name = models.CharField(max_length=100)
    owner = models.ForeignKey()
    shared_with = models.ManyToManyField()

    def __str__(self):
        return self.name

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    task_list = models.ForeignKey()
    due_date = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


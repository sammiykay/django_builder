from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone

class TaskList(models.Model):
    name = models.CharField(max_length=100, verbose_name="List Name", help_text="Enter the name of your task list")
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_lists', verbose_name="Owner")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    is_shared = models.BooleanField(default=False, verbose_name="Shared List", help_text="Allow others to view this list")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task List"
        verbose_name_plural = "Task Lists"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('tasklist-detail', kwargs={'pk': self.pk})

    def get_task_count(self):
        return self.tasks.count()

class Task(models.Model):
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
    ]

    STATUS_CHOICES = [
        ('TODO', 'To Do'),
        ('IN_PROGRESS', 'In Progress'),
        ('DONE', 'Done'),
    ]

    title = models.CharField(max_length=200, verbose_name="Title", help_text="Enter the task title")
    description = models.TextField(blank=True, verbose_name="Description", help_text="Enter task details (optional)")
    task_list = models.ForeignKey(TaskList, on_delete=models.CASCADE, related_name='tasks', verbose_name="Task List")
    due_date = models.DateTimeField(null=True, blank=True, verbose_name="Due Date")
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, verbose_name="Priority")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, verbose_name="Status")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Completed At")

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('task-detail', kwargs={'pk': self.pk})

    def mark_complete(self):
        self.status = 'DONE'
        self.completed_at = timezone.now()
        self.save()

    def is_overdue(self):
        if self.due_date and self.status != 'DONE':
            return timezone.now() > self.due_date
        return False
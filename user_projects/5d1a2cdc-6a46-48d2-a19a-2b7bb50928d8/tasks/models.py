from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

class Project(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class TeamMember(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=100)
    projects = models.ManyToManyField(Project)

    def __str__(self):
        return self.user.username

class Task(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium'),
        (3, 'High'),
        (4, 'Urgent')
    ]

    title = models.CharField(max_length=200, verbose_name='Task Title', help_text='Enter the task title')
    description = models.TextField(blank=True, help_text='Detailed description of the task')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='tasks')
    assignee = models.ForeignKey(TeamMember, on_delete=models.SET_NULL, null=True, related_name='assigned_tasks')
    status = models.CharField(max_length=50, default='New', help_text='Current status of the task')
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2)
    due_date = models.DateTimeField(help_text='When is this task due?')
    estimated_hours = models.DecimalField(max_digits=5, decimal_places=2, help_text='Estimated hours to complete')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'due_date']
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'

    def __str__(self):
        return f"{self.title} - {self.get_priority_display()}"

    def is_overdue(self):
        if self.due_date < timezone.now():
            return True
        return False

    def get_time_spent(self):
        # Placeholder for actual time tracking logic
        return 0.0

class TimeLog(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='time_logs')
    team_member = models.ForeignKey(TeamMember, on_delete=models.CASCADE)
    hours_spent = models.DecimalField(max_digits=5, decimal_places=2)
    date = models.DateField()
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.task.title} - {self.hours_spent} hours on {self.date}"
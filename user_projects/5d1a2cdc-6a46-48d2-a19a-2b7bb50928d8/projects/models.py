from django.db import models
from django.utils import timezone

class Project(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name="Project Name",
        help_text="Enter the name of the project"
    )
    description = models.TextField(
        verbose_name="Project Description",
        help_text="Detailed description of the project"
    )
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name="Team",
        help_text="Team assigned to this project"
    )
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name="Project Status",
        help_text="Current status of the project"
    )
    start_date = models.DateField(
        verbose_name="Start Date",
        help_text="Project start date"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="End Date",
        help_text="Expected project completion date"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return self.name

    def get_completion_percentage(self):
        """
        Calculate and return the project completion percentage based on completed tasks
        """
        total_tasks = self.tasks.count()
        if total_tasks == 0:
            return 0
        completed_tasks = self.tasks.filter(status='completed').count()
        return (completed_tasks / total_tasks) * 100

    def get_active_tasks(self):
        """
        Return all active tasks for this project
        """
        return self.tasks.filter(status='in_progress')
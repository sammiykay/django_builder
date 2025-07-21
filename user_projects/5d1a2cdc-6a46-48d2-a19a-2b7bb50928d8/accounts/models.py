from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext_lazy as _

ROLE_CHOICES = [
    ('ADMIN', 'Administrator'),
    ('MANAGER', 'Project Manager'),
    ('MEMBER', 'Team Member'),
]

class Team(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name=_('Team Name'),
        help_text=_('Name of the team')
    )
    description = models.TextField(
        blank=True,
        verbose_name=_('Description'),
        help_text=_('Team description and details')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    workspace_icon = models.ImageField(
        upload_to='team_icons/',
        verbose_name=_('Team Icon'),
        help_text=_('Upload team workspace icon')
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Team')
        verbose_name_plural = _('Teams')

    def __str__(self):
        return self.name

    def get_members(self):
        return self.teammember_set.all()

    def get_active_projects(self):
        return self.project_set.filter(status='active')

class TeamMember(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name=_('User'),
        help_text=_('Associated user account')
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        verbose_name=_('Role'),
        help_text=_('Team member role')
    )
    teams = models.ManyToManyField(
        Team,
        verbose_name=_('Teams'),
        help_text=_('Teams this member belongs to')
    )

    class Meta:
        ordering = ['user__username']
        verbose_name = _('Team Member')
        verbose_name_plural = _('Team Members')

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def get_active_tasks(self):
        return self.task_set.filter(status='active')

    def calculate_workload(self):
        active_tasks = self.get_active_tasks()
        return {
            'total_tasks': active_tasks.count(),
            'high_priority': active_tasks.filter(priority='high').count(),
            'estimated_hours': sum(task.estimated_hours for task in active_tasks)
        }
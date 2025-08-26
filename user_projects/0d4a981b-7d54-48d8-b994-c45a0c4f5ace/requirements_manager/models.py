import uuid
from django.db import models

class Project(models.Model):
    STATUS_CHOICES = [
        ('VALID', 'Valid'),
        ('INVALID', 'Invalid'),
        ('PENDING', 'Pending')
    ]

    project_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, verbose_name="Project Name")
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"{self.name} ({self.status})"

    def validate_requirements(self):
        requirements = self.requirement_set.all()
        valid = all(req.check_compatibility() for req in requirements)
        self.status = 'VALID' if valid else 'INVALID'
        self.save()
        return valid

    def generate_requirements(self):
        requirements = self.requirement_set.all()
        return '\n'.join([f"{req.package_name}=={req.version}" for req in requirements])

class Requirement(models.Model):
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='requirements',
        verbose_name="Associated Project"
    )
    package_name = models.CharField(
        max_length=200,
        verbose_name="Package Name",
        help_text="Name of the Python package"
    )
    version = models.CharField(
        max_length=50,
        verbose_name="Version",
        help_text="Version specification of the package"
    )
    is_valid = models.BooleanField(
        default=True,
        verbose_name="Is Valid",
        help_text="Indicates if the requirement is valid and compatible"
    )

    class Meta:
        ordering = ['package_name']
        verbose_name = "Requirement"
        verbose_name_plural = "Requirements"
        unique_together = ['project', 'package_name']

    def __str__(self):
        return f"{self.package_name} {self.version}"

    def check_compatibility(self):
        # Implementation for checking package compatibility
        # This would typically involve checking against PyPI or similar
        return self.is_valid

    def get_latest_version(self):
        # Implementation for fetching the latest version from PyPI
        # This would typically use the packaging or PyPI API
        pass
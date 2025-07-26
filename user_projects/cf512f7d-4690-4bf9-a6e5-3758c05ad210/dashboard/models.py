from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

User = get_user_model()

class Dashboard(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name=_("User"),
        help_text=_("User who owns this dashboard")
    )
    name = models.CharField(
        max_length=100,
        verbose_name=_("Dashboard Name"),
        help_text=_("Name of the dashboard")
    )
    layout = models.JSONField(
        default=dict,
        verbose_name=_("Layout Configuration"),
        help_text=_("JSON configuration for dashboard layout")
    )
    is_default = models.BooleanField(
        default=False,
        verbose_name=_("Default Dashboard"),
        help_text=_("Whether this is the user's default dashboard")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = _("Dashboard")
        verbose_name_plural = _("Dashboards")

    def __str__(self):
        return f"{self.name} - {self.user.username}"

    def get_absolute_url(self):
        return reverse('dashboard:detail', kwargs={'pk': self.pk})

    def get_widgets(self):
        return self.widget_set.all()

class Widget(models.Model):
    dashboard = models.ForeignKey(
        Dashboard,
        on_delete=models.CASCADE,
        verbose_name=_("Dashboard"),
        help_text=_("Dashboard this widget belongs to")
    )
    widget_type = models.CharField(
        max_length=50,
        verbose_name=_("Widget Type"),
        help_text=_("Type of social media widget")
    )
    configuration = models.JSONField(
        verbose_name=_("Widget Configuration"),
        help_text=_("JSON configuration for widget settings")
    )
    position = models.JSONField(
        verbose_name=_("Widget Position"),
        help_text=_("JSON data for widget position in dashboard")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At")
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_("Updated At")
    )

    class Meta:
        ordering = ['position']
        verbose_name = _("Widget")
        verbose_name_plural = _("Widgets")

    def __str__(self):
        return f"{self.widget_type} - {self.dashboard.name}"

    def get_data(self):
        """
        Retrieve widget data based on configuration
        """
        # Implementation depends on widget type
        pass

    def update_configuration(self, new_config):
        """
        Update widget configuration
        """
        self.configuration.update(new_config)
        self.save()
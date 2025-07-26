from django.db import models
from django.utils.translation import gettext_lazy as _

class MetricSnapshot(models.Model):
    platform = models.CharField(
        max_length=50,
        verbose_name=_('Platform'),
        help_text=_('Social media platform name')
    )
    
    metric_type = models.CharField(
        max_length=50,
        verbose_name=_('Metric Type'),
        help_text=_('Type of metric being measured')
    )
    
    value = models.JSONField(
        verbose_name=_('Value'),
        help_text=_('Metric value data in JSON format')
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Timestamp'),
        help_text=_('When this metric snapshot was taken')
    )

    class Meta:
        verbose_name = _('Metric Snapshot')
        verbose_name_plural = _('Metric Snapshots')
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['platform', 'metric_type']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.platform} - {self.metric_type} ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"

    def get_value_display(self):
        """
        Returns a formatted string representation of the JSON value
        """
        if isinstance(self.value, dict):
            return ', '.join(f"{k}: {v}" for k, v in self.value.items())
        return str(self.value)
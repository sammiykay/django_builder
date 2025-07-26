from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

User = get_user_model()

ORDER_STATUSES = (
    ('pending', _('Pending')),
    ('processing', _('Processing')),
    ('paid', _('Paid')),
    ('shipped', _('Shipped')),
    ('delivered', _('Delivered')),
    ('cancelled', _('Cancelled')),
)

class Order(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        verbose_name=_('User'),
        help_text=_('User who placed the order')
    )
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUSES,
        default='pending',
        verbose_name=_('Status'),
        help_text=_('Current status of the order')
    )
    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Total Amount'),
        help_text=_('Total order amount')
    )
    payment_intent = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name=_('Payment Intent ID'),
        help_text=_('Payment provider intent ID')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At'),
        help_text=_('Date and time when the order was created')
    )

    class Meta:
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.id} - {self.user.username}"

    def get_total_display(self):
        return f"${self.total:.2f}"

    def can_cancel(self):
        return self.status in ['pending', 'processing']

    def can_update_status(self, new_status):
        valid_transitions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['paid', 'cancelled'],
            'paid': ['shipped'],
            'shipped': ['delivered'],
        }
        return new_status in valid_transitions.get(self.status, [])
import pytest
from django.test import TestCase, Client
from django.urls import reverse
from orders.models import Order
from django.contrib.auth import get_user_model
from decimal import Decimal

User = get_user_model()

@pytest.mark.django_db
class TestOrderModel:
    @pytest.fixture
    def user(self):
        return User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    @pytest.fixture
    def order(self, user):
        return Order.objects.create(
            user=user,
            total_amount=Decimal('99.99'),
            status='pending'
        )

    def test_order_creation(self, order):
        assert order.total_amount == Decimal('99.99')
        assert order.status == 'pending'
        assert str(order) == f'Order #{order.id}'

    def test_order_status_choices(self, order):
        valid_statuses = ['pending', 'processing', 'completed', 'cancelled']
        for status in valid_statuses:
            order.status = status
            order.save()
            assert order.status == status

    def test_order_total_amount_validation(self, user):
        with pytest.raises(Exception):
            Order.objects.create(
                user=user,
                total_amount=Decimal('-50.00'),
                status='pending'
            )

    def test_order_user_deletion_cascade(self, order, user):
        user.delete()
        assert Order.objects.filter(id=order.id).count() == 0

    def test_order_default_values(self, user):
        order = Order.objects.create(
            user=user,
            total_amount=Decimal('100.00')
        )
        assert order.status == 'pending'  # Assuming 'pending' is the default status
        assert order.created_at is not None
        assert order.updated_at is not None

    def test_order_timestamps(self, order):
        original_updated_at = order.updated_at
        order.total_amount = Decimal('150.00')
        order.save()
        assert order.updated_at > original_updated_at

    def test_order_max_total_amount(self, user):
        max_amount = Decimal('999999.99')
        order = Order.objects.create(
            user=user,
            total_amount=max_amount,
            status='pending'
        )
        assert order.total_amount == max_amount

    def test_order_status_transition(self, order):
        # Test valid status transition
        order.status = 'processing'
        order.save()
        assert order.status == 'processing'

        order.status = 'completed'
        order.save()
        assert order.status == 'completed'

    def test_order_queryset_methods(self, user):
        # Create multiple orders with different statuses
        Order.objects.create(user=user, total_amount=Decimal('100.00'), status='pending')
        Order.objects.create(user=user, total_amount=Decimal('200.00'), status='completed')
        Order.objects.create(user=user, total_amount=Decimal('300.00'), status='cancelled')

        assert Order.objects.filter(status='pending').count() == 1
        assert Order.objects.filter(status='completed').count() == 1
        assert Order.objects.filter(status='cancelled').count() == 1

    def test_order_total_amount_precision(self, user):
        # Test decimal precision
        order = Order.objects.create(
            user=user,
            total_amount=Decimal('99.999'),
            status='pending'
        )
        # Should be rounded to 2 decimal places
        assert order.total_amount == Decimal('100.00')

# Add more test classes if needed for forms, views, or API endpoints
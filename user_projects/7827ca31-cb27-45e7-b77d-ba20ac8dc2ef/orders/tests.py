import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from .models import Order
from decimal import Decimal

@pytest.mark.django_db
class TestOrderModel:
    def test_order_creation(self):
        order = Order.objects.create(
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="pending"
        )
        assert order.order_number == "ORD-001"
        assert order.total_amount == Decimal("99.99")
        assert order.status == "pending"
        assert order.created_at is not None

    def test_order_str_representation(self):
        order = Order.objects.create(
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="pending"
        )
        assert str(order) == "ORD-001"

    def test_order_status_choices(self):
        order = Order.objects.create(
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="pending"
        )
        order.status = "completed"
        order.save()
        assert order.status == "completed"

        with pytest.raises(Exception):
            order.status = "invalid_status"
            order.save()

    def test_order_total_amount_validation(self):
        with pytest.raises(Exception):
            Order.objects.create(
                order_number="ORD-001",
                total_amount=Decimal("-10.00"),
                status="pending"
            )

    def test_order_number_unique(self):
        Order.objects.create(
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="pending"
        )
        
        with pytest.raises(Exception):
            Order.objects.create(
                order_number="ORD-001",
                total_amount=Decimal("150.00"),
                status="pending"
            )

    def test_order_timestamps(self):
        order = Order.objects.create(
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="pending"
        )
        assert order.created_at <= timezone.now()
        
        original_updated_at = order.updated_at
        order.total_amount = Decimal("150.00")
        order.save()
        assert order.updated_at > original_updated_at

    @pytest.mark.parametrize(
        "order_number,total_amount,status,expected_valid",
        [
            ("ORD-001", Decimal("99.99"), "pending", True),
            ("ORD-002", Decimal("0.00"), "pending", True),
            ("ORD-003", Decimal("999999.99"), "completed", True),
            ("", Decimal("99.99"), "pending", False),
            ("ORD-004", Decimal("-1.00"), "pending", False),
            ("ORD-005", Decimal("99.99"), "invalid_status", False),
        ]
    )
    def test_order_validation_cases(self, order_number, total_amount, status, expected_valid):
        if expected_valid:
            order = Order.objects.create(
                order_number=order_number,
                total_amount=total_amount,
                status=status
            )
            assert order.pk is not None
        else:
            with pytest.raises(Exception):
                Order.objects.create(
                    order_number=order_number,
                    total_amount=total_amount,
                    status=status
                )

    def test_order_default_values(self):
        order = Order.objects.create(
            order_number="ORD-001",
            total_amount=Decimal("99.99")
        )
        assert order.status == "pending"  # Assuming 'pending' is the default status

    def test_bulk_order_creation(self):
        orders = [
            Order(
                order_number=f"ORD-{i}",
                total_amount=Decimal("99.99"),
                status="pending"
            )
            for i in range(1, 4)
        ]
        created_orders = Order.objects.bulk_create(orders)
        assert len(created_orders) == 3
        assert Order.objects.count() == 3

    def test_order_filtering(self):
        Order.objects.create(
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="pending"
        )
        Order.objects.create(
            order_number="ORD-002",
            total_amount=Decimal("149.99"),
            status="completed"
        )
        
        pending_orders = Order.objects.filter(status="pending")
        completed_orders = Order.objects.filter(status="completed")
        expensive_orders = Order.objects.filter(total_amount__gt=Decimal("100.00"))
        
        assert pending_orders.count() == 1
        assert completed_orders.count() == 1
        assert expensive_orders.count() == 1

class TestOrderQuerySet:
    @pytest.mark.django_db
    def test_order_queryset_methods(self):
        # Create test orders
        Order.objects.create(
            order_number="ORD-001",
            total_amount=Decimal("99.99"),
            status="pending"
        )
        Order.objects.create(
            order_number="ORD-002",
            total_amount=Decimal("149.99"),
            status="completed"
        )
        
        # Test basic queryset operations
        assert Order.objects.count() == 2
        assert Order.objects.filter(status="pending").exists()
        assert Order.objects.filter(total_amount__gt=Decimal("100")).count() == 1
        
        # Test ordering
        orders = Order.objects.order_by("-total_amount")
        assert orders.first().total_amount == Decimal("149.99")
        
        # Test aggregation
        from django.db.models import Sum
        total_sum = Order.objects.aggregate(Sum("total_amount"))
        assert total_sum["total_amount__sum"] == Decimal("249.98")
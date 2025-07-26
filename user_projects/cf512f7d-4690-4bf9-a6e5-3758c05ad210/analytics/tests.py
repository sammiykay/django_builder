import pytest
from django.test import TestCase
from django.utils import timezone
from analytics.models import MetricSnapshot
from django.core.exceptions import ValidationError

@pytest.mark.django_db
class TestMetricSnapshot:
    def test_create_metric_snapshot(self):
        snapshot = MetricSnapshot.objects.create(
            metric_name="test_metric",
            value=100,
            timestamp=timezone.now()
        )
        assert snapshot.metric_name == "test_metric"
        assert snapshot.value == 100
        assert snapshot.timestamp is not None

    def test_metric_name_max_length(self):
        with pytest.raises(ValidationError):
            snapshot = MetricSnapshot(
                metric_name="x" * 256,
                value=100,
                timestamp=timezone.now()
            )
            snapshot.full_clean()

    def test_negative_value(self):
        snapshot = MetricSnapshot.objects.create(
            metric_name="negative_metric",
            value=-100,
            timestamp=timezone.now()
        )
        assert snapshot.value == -100

    def test_zero_value(self):
        snapshot = MetricSnapshot.objects.create(
            metric_name="zero_metric",
            value=0,
            timestamp=timezone.now()
        )
        assert snapshot.value == 0

    def test_large_value(self):
        snapshot = MetricSnapshot.objects.create(
            metric_name="large_metric",
            value=999999999,
            timestamp=timezone.now()
        )
        assert snapshot.value == 999999999

    def test_future_timestamp(self):
        future_time = timezone.now() + timezone.timedelta(days=1)
        snapshot = MetricSnapshot.objects.create(
            metric_name="future_metric",
            value=100,
            timestamp=future_time
        )
        assert snapshot.timestamp == future_time

    def test_past_timestamp(self):
        past_time = timezone.now() - timezone.timedelta(days=30)
        snapshot = MetricSnapshot.objects.create(
            metric_name="past_metric",
            value=100,
            timestamp=past_time
        )
        assert snapshot.timestamp == past_time

    def test_duplicate_metric_same_timestamp(self):
        timestamp = timezone.now()
        MetricSnapshot.objects.create(
            metric_name="duplicate_metric",
            value=100,
            timestamp=timestamp
        )
        MetricSnapshot.objects.create(
            metric_name="duplicate_metric",
            value=200,
            timestamp=timestamp
        )
        assert MetricSnapshot.objects.filter(metric_name="duplicate_metric").count() == 2

    def test_update_metric_snapshot(self):
        snapshot = MetricSnapshot.objects.create(
            metric_name="update_metric",
            value=100,
            timestamp=timezone.now()
        )
        snapshot.value = 200
        snapshot.save()
        updated_snapshot = MetricSnapshot.objects.get(id=snapshot.id)
        assert updated_snapshot.value == 200

    def test_delete_metric_snapshot(self):
        snapshot = MetricSnapshot.objects.create(
            metric_name="delete_metric",
            value=100,
            timestamp=timezone.now()
        )
        snapshot_id = snapshot.id
        snapshot.delete()
        with pytest.raises(MetricSnapshot.DoesNotExist):
            MetricSnapshot.objects.get(id=snapshot_id)

    def test_metric_name_blank(self):
        with pytest.raises(ValidationError):
            snapshot = MetricSnapshot(
                metric_name="",
                value=100,
                timestamp=timezone.now()
            )
            snapshot.full_clean()

    def test_timestamp_auto_now(self):
        snapshot = MetricSnapshot.objects.create(
            metric_name="auto_timestamp",
            value=100
        )
        assert snapshot.timestamp is not None

    def test_str_representation(self):
        snapshot = MetricSnapshot.objects.create(
            metric_name="test_metric",
            value=100,
            timestamp=timezone.now()
        )
        assert str(snapshot) == f"test_metric: 100 at {snapshot.timestamp}"

    def test_ordering(self):
        time1 = timezone.now()
        time2 = time1 + timezone.timedelta(hours=1)
        time3 = time2 + timezone.timedelta(hours=1)

        snapshot3 = MetricSnapshot.objects.create(
            metric_name="test_metric",
            value=300,
            timestamp=time3
        )
        snapshot1 = MetricSnapshot.objects.create(
            metric_name="test_metric",
            value=100,
            timestamp=time1
        )
        snapshot2 = MetricSnapshot.objects.create(
            metric_name="test_metric",
            value=200,
            timestamp=time2
        )

        snapshots = MetricSnapshot.objects.all()
        assert snapshots[0] == snapshot1
        assert snapshots[1] == snapshot2
        assert snapshots[2] == snapshot3
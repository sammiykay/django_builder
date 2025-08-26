from rest_framework import serializers
from .models import TaskList, Task

class TaskListSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaskList
        fields = ['id', 'name', 'description', 'created_at']

class TaskSerializer(serializers.ModelSerializer):
    task_list = TaskListSerializer(read_only=True)
    task_list_id = serializers.PrimaryKeyRelatedField(
        queryset=TaskList.objects.all(),
        source='task_list',
        write_only=True
    )

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'due_date', 'status', 
                 'priority', 'created_at', 'updated_at', 'task_list', 
                 'task_list_id']
        read_only_fields = ['created_at', 'updated_at']

    def validate_due_date(self, value):
        from django.utils import timezone
        if value and value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past")
        return value

    def validate_status(self, value):
        valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        if value not in valid_statuses:
            raise serializers.ValidationError(f"Status must be one of {valid_statuses}")
        return value

    def validate_priority(self, value):
        valid_priorities = ['low', 'medium', 'high']
        if value not in valid_priorities:
            raise serializers.ValidationError(f"Priority must be one of {valid_priorities}")
        return value
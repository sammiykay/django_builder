from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import models
from .models import (
    Project, ProjectFile, ChatMessage, CommandExecution, ChatThread,
    UserProfile, ProjectSession, ProjectTemplate, ErrorLog, UsageAnalytics,
    BillingPlan, UserSubscription, TokenUsage, BillingInvoice,
    PaymentMethod, Payment, CryptoWallet, PaymentWebhook
)

class ProjectFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectFile
        fields = ['id', 'path', 'content', 'file_type', 'size', 'created_at', 'updated_at', 
                 'is_ai_generated', 'ai_merge_status', 'original_content']
        read_only_fields = ['id', 'size', 'created_at', 'updated_at']

class ProjectSerializer(serializers.ModelSerializer):
    files_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'python_version', 'django_version',
            'container_id', 'container_port', 'is_running', 'files_count',
            'django_project_created', 'main_app_name', 'last_prompt', 'ai_generation_status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'container_id', 'container_port', 'is_running', 'created_at', 'updated_at']
    
    def get_files_count(self, obj):
        return obj.files.count()
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        return super().create(validated_data)

class ChatThreadSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatThread
        fields = ['id', 'thread_id', 'created_at', 'last_activity', 'is_active', 'context_length']
        read_only_fields = ['id', 'thread_id', 'created_at', 'last_activity']

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id', 'role', 'content', 'message_type', 'timestamp', 'tokens_used', 
            'processing_time', 'is_error_report', 'error_type', 'error_source',
            'files_modified', 'code_changes', 'created_at'
        ]
        read_only_fields = ['id', 'timestamp', 'created_at']

class CommandExecutionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommandExecution
        fields = ['id', 'command', 'output', 'error_output', 'exit_code', 'execution_time', 'executed_at']


# Enhanced User Profile Serializers
class UserProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    last_name = serializers.CharField(source='user.last_name', read_only=True)
    full_name = serializers.CharField(read_only=True)
    display_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            # User info
            'username', 'email', 'first_name', 'last_name', 'full_name', 'display_name',
            # Personal info
            'bio', 'avatar', 'phone_number', 'date_of_birth', 'location', 
            'website', 'github_username', 'linkedin_url',
            # Preferences
            'preferred_theme', 'preferred_language', 'email_notifications', 'project_updates',
            # App-specific preferences
            'default_project_type', 'default_complexity', 'auto_fix_errors', 'enable_analytics',
            # Usage stats
            'total_projects_created', 'total_ai_requests', 'total_tokens_used',
            # Subscription
            'plan_type', 'monthly_token_limit', 'monthly_tokens_used', 'billing_cycle_start',
            # Timestamps
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'username', 'email', 'first_name', 'last_name', 'full_name', 'display_name',
            'total_projects_created', 'total_ai_requests', 'total_tokens_used', 
            'monthly_tokens_used', 'billing_cycle_start', 'created_at', 'updated_at'
        ]

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    # User fields that can be updated
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    email = serializers.EmailField(source='user.email', required=False)
    
    class Meta:
        model = UserProfile
        fields = [
            # User fields
            'first_name', 'last_name', 'email',
            # Personal info
            'bio', 'avatar', 'phone_number', 'date_of_birth', 'location',
            'website', 'github_username', 'linkedin_url',
            # Preferences
            'preferred_theme', 'preferred_language', 'email_notifications', 'project_updates',
            'default_project_type', 'default_complexity', 'auto_fix_errors', 'enable_analytics'
        ]
    
    def update(self, instance, validated_data):
        # Handle user fields
        user_data = validated_data.pop('user', {})
        if user_data:
            user = instance.user
            for attr, value in user_data.items():
                setattr(user, attr, value)
            user.save()
        
        # Handle profile fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance


class ProjectSessionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    duration_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ProjectSession
        fields = [
            'session_id', 'start_time', 'end_time', 'duration_seconds', 
            'duration_formatted', 'messages_sent', 'files_modified', 
            'commands_executed', 'errors_encountered', 'user_name', 'project_name'
        ]
        read_only_fields = [
            'session_id', 'start_time', 'end_time', 'duration_seconds',
            'user_name', 'project_name'
        ]
    
    def get_duration_formatted(self, obj):
        if obj.duration_seconds:
            hours = obj.duration_seconds // 3600
            minutes = (obj.duration_seconds % 3600) // 60
            seconds = obj.duration_seconds % 60
            if hours > 0:
                return f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                return f"{minutes}m {seconds}s"
            else:
                return f"{seconds}s"
        return "Active"


class ProjectTemplateSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    source_project_name = serializers.CharField(source='source_project.name', read_only=True)
    
    class Meta:
        model = ProjectTemplate
        fields = [
            'id', 'name', 'description', 'creator_name', 'source_project_name',
            'project_type', 'complexity_level', 'template_data', 'times_used',
            'rating', 'is_public', 'is_featured', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'creator_name', 'source_project_name', 'times_used', 'rating',
            'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        validated_data['creator'] = self.context['request'].user
        return super().create(validated_data)


class ErrorLogSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    time_since_error = serializers.SerializerMethodField()
    
    class Meta:
        model = ErrorLog
        fields = [
            'id', 'project_name', 'error_type', 'error_message', 'error_traceback',
            'file_path', 'line_number', 'command_executed', 'user_action',
            'is_resolved', 'auto_fix_attempted', 'auto_fix_successful',
            'fix_description', 'fix_applied_at', 'tokens_used_for_fix',
            'created_at', 'time_since_error'
        ]
        read_only_fields = [
            'id', 'project_name', 'created_at', 'time_since_error'
        ]
    
    def get_time_since_error(self, obj):
        from django.utils import timezone
        diff = timezone.now() - obj.created_at
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"


class UsageAnalyticsSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    
    class Meta:
        model = UsageAnalytics
        fields = [
            'id', 'user_name', 'project_name', 'action_type', 'action_data',
            'response_time_ms', 'tokens_used', 'success', 'timestamp'
        ]
        read_only_fields = ['id', 'user_name', 'project_name', 'timestamp']


# Enhanced Project Serializer with more details
class ProjectDetailSerializer(serializers.ModelSerializer):
    owner_name = serializers.CharField(source='owner.username', read_only=True)
    files_count = serializers.SerializerMethodField()
    total_size = serializers.SerializerMethodField()
    messages_count = serializers.SerializerMethodField()
    executions_count = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    error_count = serializers.SerializerMethodField()
    unresolved_errors = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'name', 'description', 'owner_name', 'project_type', 'complexity_level',
            'target_audience', 'key_features', 'technical_requirements', 'python_version',
            'django_version', 'container_id', 'container_port', 'is_running',
            'django_project_created', 'main_app_name', 'last_prompt', 'original_prompt',
            'ai_generation_status', 'prompt_history', 'generated_features',
            'files_count', 'total_size', 'messages_count', 'executions_count',
            'last_activity', 'error_count', 'unresolved_errors',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'owner_name', 'container_id', 'container_port', 'is_running',
            'files_count', 'total_size', 'messages_count', 'executions_count',
            'last_activity', 'error_count', 'unresolved_errors', 'created_at', 'updated_at'
        ]
    
    def get_files_count(self, obj):
        return obj.files.count()
    
    def get_total_size(self, obj):
        return obj.files.aggregate(total=models.Sum('size'))['total'] or 0
    
    def get_messages_count(self, obj):
        return obj.messages.count()
    
    def get_executions_count(self, obj):
        return obj.executions.count()
    
    def get_last_activity(self, obj):
        latest_message = obj.messages.order_by('-timestamp').first()
        latest_execution = obj.executions.order_by('-executed_at').first()
        
        if latest_message and latest_execution:
            return max(latest_message.timestamp, latest_execution.executed_at)
        elif latest_message:
            return latest_message.timestamp
        elif latest_execution:
            return latest_execution.executed_at
        else:
            return obj.updated_at
    
    def get_error_count(self, obj):
        return obj.error_logs.count()
    
    def get_unresolved_errors(self, obj):
        return obj.error_logs.filter(is_resolved=False).count()


class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)

class CommandRequestSerializer(serializers.Serializer):
    command = serializers.CharField(max_length=500)

class FileUpdateSerializer(serializers.Serializer):
    path = serializers.CharField(max_length=500)
    content = serializers.CharField()

class ConversationChatSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=2000)
    is_error = serializers.BooleanField(default=False)
    error_type = serializers.CharField(max_length=100, required=False, allow_blank=True)
    error_source = serializers.CharField(max_length=200, required=False, allow_blank=True)

class ErrorReportSerializer(serializers.Serializer):
    error_message = serializers.CharField(max_length=2000)
    error_type = serializers.CharField(max_length=100, default='runtime_error')
    error_source = serializers.CharField(max_length=200, required=False, allow_blank=True)


# Billing Serializers
class BillingPlanSerializer(serializers.ModelSerializer):
    is_free = serializers.ReadOnlyField()
    
    class Meta:
        model = BillingPlan
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = BillingPlanSerializer(read_only=True)
    plan_id = serializers.IntegerField(write_only=True, required=False)
    user_name = serializers.CharField(source='user.username', read_only=True)
    is_active = serializers.ReadOnlyField()
    tokens_remaining = serializers.ReadOnlyField()
    usage_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = UserSubscription
        fields = '__all__'
        read_only_fields = [
            'user', 'created_at', 'updated_at', 'started_at',
            'tokens_used_this_period', 'bonus_tokens_remaining'
        ]


class TokenUsageSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    project_name = serializers.CharField(source='project.name', read_only=True)
    cost_dollars = serializers.ReadOnlyField()
    
    class Meta:
        model = TokenUsage
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


class BillingInvoiceSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    subscription = UserSubscriptionSerializer(read_only=True)
    
    class Meta:
        model = BillingInvoice
        fields = '__all__'
        read_only_fields = [
            'user', 'invoice_number', 'created_at', 'updated_at', 'issued_date'
        ]


class UsageStatsSerializer(serializers.Serializer):
    """Serializer for usage statistics"""
    total_tokens_used = serializers.IntegerField()
    tokens_remaining = serializers.IntegerField()
    usage_percentage = serializers.FloatField()
    current_plan = BillingPlanSerializer()
    usage_by_type = serializers.DictField()
    daily_usage = serializers.ListField()
    monthly_cost = serializers.DecimalField(max_digits=10, decimal_places=2)


class BillingDashboardSerializer(serializers.Serializer):
    """Comprehensive billing dashboard data"""
    subscription = UserSubscriptionSerializer()
    usage_stats = UsageStatsSerializer()
    recent_usage = TokenUsageSerializer(many=True)
    invoices = BillingInvoiceSerializer(many=True)
    available_plans = BillingPlanSerializer(many=True)


# Payment Serializers
class PaymentMethodSerializer(serializers.ModelSerializer):
    is_crypto = serializers.ReadOnlyField()
    is_flutterwave = serializers.ReadOnlyField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'payment_type', 'is_active', 'is_crypto', 'is_flutterwave',
            'crypto_symbol', 'crypto_network', 'usd_exchange_rate', 'last_rate_update'
        ]
        read_only_fields = ['created_at', 'updated_at', 'last_rate_update']


class PaymentSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.username', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    is_crypto_payment = serializers.ReadOnlyField()
    is_confirmed = serializers.ReadOnlyField()
    purpose_display = serializers.CharField(source='get_purpose_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Payment
        fields = [
            'id', 'payment_id', 'reference', 'user_name', 'payment_method_name',
            'purpose', 'purpose_display', 'amount_usd', 'amount_paid', 'currency',
            'exchange_rate', 'status', 'status_display', 'is_crypto_payment', 'is_confirmed',
            'crypto_address', 'transaction_hash', 'block_confirmations', 'required_confirmations',
            'gateway_transaction_id', 'created_at', 'updated_at', 'completed_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'payment_id', 'reference', 'user_name', 'payment_method_name',
            'is_crypto_payment', 'is_confirmed', 'purpose_display', 'status_display',
            'gateway_transaction_id', 'created_at', 'updated_at', 'completed_at'
        ]


class CryptoWalletSerializer(serializers.ModelSerializer):
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)
    crypto_symbol = serializers.CharField(source='payment_method.crypto_symbol', read_only=True)
    
    class Meta:
        model = CryptoWallet
        fields = [
            'id', 'payment_method_name', 'crypto_symbol', 'address', 'is_active',
            'balance', 'last_balance_check', 'total_received', 'payment_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'payment_method_name', 'crypto_symbol', 'balance', 'last_balance_check',
            'total_received', 'payment_count', 'created_at', 'updated_at'
        ]


class PaymentWebhookSerializer(serializers.ModelSerializer):
    payment_reference = serializers.CharField(source='payment.reference', read_only=True)
    
    class Meta:
        model = PaymentWebhook
        fields = [
            'id', 'webhook_type', 'payment_reference', 'webhook_id', 'event_type',
            'processed', 'success', 'error_message', 'actions_taken',
            'signature_valid', 'ip_address', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'payment_reference', 'created_at', 'processed_at'
        ]


# Payment Request Serializers
class FlutterwavePaymentRequestSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    purpose = serializers.ChoiceField(
        choices=['subscription', 'upgrade', 'token_purchase', 'overage'],
        default='subscription'
    )


class CryptoPaymentRequestSerializer(serializers.Serializer):
    plan_id = serializers.IntegerField()
    crypto_type = serializers.ChoiceField(
        choices=['crypto_bitcoin', 'crypto_ethereum', 'crypto_usdt', 'crypto_usdc']
    )
    purpose = serializers.ChoiceField(
        choices=['subscription', 'upgrade', 'token_purchase', 'overage'],
        default='subscription'
    )


class PaymentVerificationSerializer(serializers.Serializer):
    transaction_id = serializers.CharField(max_length=200)
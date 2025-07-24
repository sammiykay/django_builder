from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from .models import (
    Project, ProjectFile, ChatThread, ChatMessage, CommandExecution,
    UserProfile, ProjectSession, ProjectTemplate, ErrorLog, UsageAnalytics,
    BillingPlan, UserSubscription, TokenUsage, BillingInvoice
)

# Unregister the default User admin to register our custom one
admin.site.unregister(User)

# --- Custom User Admin with UserProfile Inline ---
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile'
    fieldsets = (
        ('Personal Information', {
            'fields': ('bio', 'avatar', 'phone_number', 'date_of_birth', 'location', 'website')
        }),
        ('Social Links', {
            'fields': ('github_username', 'linkedin_url')
        }),
        ('Preferences', {
            'fields': ('preferred_theme', 'preferred_language', 'email_notifications', 'project_updates')
        }),
        ('Usage & Limits', {
            'fields': ('total_projects_created', 'total_ai_requests', 'total_tokens_used', 'plan_type', 'monthly_token_limit', 'monthly_tokens_used', 'billing_cycle_start')
        }),
        ('AI & Project Defaults', {
            'fields': ('default_project_type', 'default_complexity', 'auto_fix_errors', 'enable_analytics')
        }),
    )
    readonly_fields = ('total_projects_created', 'total_ai_requests', 'total_tokens_used', 'monthly_tokens_used', 'billing_cycle_start')


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_plan_type')
    # FIX 1: Changed 'userprofile__plan_type' to 'profile__plan_type'
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups', 'profile__plan_type')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('username',)

    def get_plan_type(self, obj):
        return obj.profile.plan_type if hasattr(obj, 'profile') else 'N/A'
    get_plan_type.short_description = 'Plan Type'


# --- Project Administration ---
class ProjectFileInline(admin.TabularInline):
    model = ProjectFile
    extra = 0
    fields = ('path', 'file_type', 'size', 'is_ai_generated', 'ai_merge_status')
    readonly_fields = ('size', 'created_at', 'updated_at')
    show_change_link = True # Allows direct editing of the inline object

class ChatThreadInline(admin.StackedInline):
    model = ChatThread
    can_delete = False
    verbose_name_plural = 'Chat Thread'
    fields = ('thread_id', 'is_active', 'context_length', 'last_activity')
    readonly_fields = ('thread_id', 'created_at', 'last_activity')
    show_change_link = True

class CommandExecutionInline(admin.TabularInline):
    model = CommandExecution
    extra = 0
    fields = ('command', 'exit_code', 'execution_time', 'executed_at')
    readonly_fields = ('executed_at',)
    show_change_link = True

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'owner', 'project_type', 'complexity_level', 'is_running',
        'django_project_created', 'ai_generation_status', 'created_at_display',
        'view_chat_link', 'view_files_link'
    )
    list_filter = (
        'project_type', 'complexity_level', 'is_running',
        'django_project_created', 'ai_generation_status', 'created_at'
    )
    search_fields = ('name', 'description', 'owner__username')
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at', 'container_id', 'container_port')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'owner')
        }),
        ('Project Configuration', {
            'fields': (
                'project_type', 'complexity_level', 'target_audience',
                'key_features', 'technical_requirements'
            ),
            'description': "Details about the project's purpose and requirements."
        }),
        ('Development Environment', {
            'fields': ('python_version', 'django_version', 'container_id', 'container_port', 'is_running')
        }),
        ('AI Generation Status', {
            'fields': (
                'django_project_created', 'main_app_name', 'ai_generation_status',
                'last_prompt', 'original_prompt', 'prompt_history', 'generated_features'
            ),
            'description': "Track the progress and details of AI-driven project generation."
        }),
    )
    inlines = [ChatThreadInline, ProjectFileInline, CommandExecutionInline]

    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.admin_order_field = 'created_at'
    created_at_display.short_description = 'Created At'

    def view_chat_link(self, obj):
        if hasattr(obj, 'chat_thread') and obj.chat_thread:
            # Assuming 'main' is your app name for reversing
            url = reverse('admin:ai_builder_chatthread_change', args=[obj.chat_thread.pk])
            return format_html('<a href="{}">View Chat</a>', url)
        return "No Chat"
    view_chat_link.short_description = 'Chat'

    def view_files_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_projectfile_changelist') + f'?project__id__exact={obj.pk}'
        return format_html('<a href="{}">View Files ({})</a>', url, obj.files.count())
    view_files_link.short_description = 'Files'

    # Custom Admin Actions
    actions = ['mark_as_running', 'mark_as_stopped', 'mark_ai_generation_complete']

    @admin.action(description='Mark selected projects as Running')
    def mark_as_running(self, request, queryset):
        updated = queryset.update(is_running=True)
        self.message_user(request, f'{updated} projects marked as running.')

    @admin.action(description='Mark selected projects as Stopped')
    def mark_as_stopped(self, request, queryset):
        updated = queryset.update(is_running=False)
        self.message_user(request, f'{updated} projects marked as stopped.')

    @admin.action(description='Mark selected projects AI generation as Completed')
    def mark_ai_generation_complete(self, request, queryset):
        updated = queryset.update(ai_generation_status='completed')
        self.message_user(request, f'{updated} projects AI generation status updated to completed.')


# --- ProjectFile Administration ---
@admin.register(ProjectFile)
class ProjectFileAdmin(admin.ModelAdmin):
    # FIX 2: Changed 'created_at_display' to 'created_at' as it's a direct field
    list_display = (
        'path', 'project_link', 'file_type', 'size', 'is_ai_generated',
        'ai_merge_status', 'created_at' # Using the direct field 'created_at'
    )
    list_filter = ('file_type', 'is_ai_generated', 'ai_merge_status', 'project')
    search_fields = ('path', 'content', 'project__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('size', 'created_at', 'updated_at', 'original_content')
    raw_id_fields = ('project',) # Improves performance for large numbers of projects

    def project_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_project_change', args=[obj.project.pk])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)
    project_link.short_description = 'Project'


# --- Chat Administration ---
class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    extra = 0
    fields = ('role', 'content', 'message_type', 'timestamp', 'tokens_used')
    readonly_fields = ('timestamp', 'tokens_used', 'processing_time', 'created_at')
    ordering = ('timestamp',)

@admin.register(ChatThread)
class ChatThreadAdmin(admin.ModelAdmin):
    list_display = ('project_link', 'thread_id', 'is_active', 'last_activity_display', 'message_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('project__name', 'thread_id')
    readonly_fields = ('thread_id', 'created_at', 'last_activity')
    inlines = [ChatMessageInline]
    raw_id_fields = ('project',)

    def project_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_project_change', args=[obj.project.pk])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)
    project_link.short_description = 'Project'

    def last_activity_display(self, obj):
        return obj.last_activity.strftime('%Y-%m-%d %H:%M')
    last_activity_display.admin_order_field = 'last_activity'
    last_activity_display.short_description = 'Last Activity'

    def message_count(self, obj):
        return obj.messages.count()
    message_count.short_description = 'Messages'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        'project_link', 'role', 'message_type', 'content_snippet', 'timestamp_display',
        'is_error_report', 'error_type', 'tokens_used'
    )
    list_filter = ('role', 'message_type', 'is_error_report', 'project', 'thread')
    search_fields = ('content', 'project__name', 'error_type', 'error_source')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'created_at', 'files_modified', 'code_changes', 'tokens_used', 'processing_time')
    raw_id_fields = ('project', 'thread')
    fieldsets = (
        (None, {
            'fields': ('project', 'thread', 'role', 'content', 'message_type')
        }),
        ('Error Report Details', {
            'fields': ('is_error_report', 'error_type', 'error_source'),
            'classes': ('collapse',)
        }),
        ('Code Modification Tracking', {
            'fields': ('files_modified', 'code_changes'),
            'classes': ('collapse',)
        }),
        ('Performance & Usage', {
            'fields': ('tokens_used', 'processing_time'),
            'classes': ('collapse',)
        }),
    )

    def project_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_project_change', args=[obj.project.pk])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)
    project_link.short_description = 'Project'

    def content_snippet(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_snippet.short_description = 'Content'

    def timestamp_display(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    timestamp_display.admin_order_field = 'timestamp'
    timestamp_display.short_description = 'Timestamp'


# --- Command Execution Administration ---
@admin.register(CommandExecution)
class CommandExecutionAdmin(admin.ModelAdmin):
    list_display = ('project_link', 'command_snippet', 'exit_code', 'execution_time', 'executed_at_display')
    list_filter = ('exit_code', 'project')
    search_fields = ('command', 'output', 'error_output', 'project__name')
    date_hierarchy = 'executed_at'
    readonly_fields = ('executed_at',)
    raw_id_fields = ('project',)

    def project_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_project_change', args=[obj.project.pk])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)
    project_link.short_description = 'Project'

    def command_snippet(self, obj):
        return obj.command[:75] + '...' if len(obj.command) > 75 else obj.command
    command_snippet.short_description = 'Command'

    def executed_at_display(self, obj):
        return obj.executed_at.strftime('%Y-%m-%d %H:%M:%S')
    executed_at_display.admin_order_field = 'executed_at'
    executed_at_display.short_description = 'Executed At'


# --- ProjectSession Administration ---
@admin.register(ProjectSession)
class ProjectSessionAdmin(admin.ModelAdmin):
    list_display = (
        'session_id', 'user_link', 'project_link', 'start_time_display',
        'end_time_display', 'duration_seconds', 'messages_sent', 'errors_encountered'
    )
    list_filter = ('start_time', 'user', 'project')
    search_fields = ('user__username', 'project__name', 'session_id', 'ip_address')
    date_hierarchy = 'start_time'
    readonly_fields = ('session_id', 'start_time', 'end_time', 'duration_seconds')
    raw_id_fields = ('user', 'project')

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def project_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_project_change', args=[obj.project.pk])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)
    project_link.short_description = 'Project'

    def start_time_display(self, obj):
        return obj.start_time.strftime('%Y-%m-%d %H:%M')
    start_time_display.admin_order_field = 'start_time'
    start_time_display.short_description = 'Start Time'

    def end_time_display(self, obj):
        if obj.end_time:
            return obj.end_time.strftime('%Y-%m-%d %H:%M')
        return "N/A"
    end_time_display.admin_order_field = 'end_time'
    end_time_display.short_description = 'End Time'


# --- ProjectTemplate Administration ---
@admin.register(ProjectTemplate)
class ProjectTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'creator_link', 'project_type', 'complexity_level',
        'is_public', 'is_featured', 'times_used', 'rating', 'created_at_display'
    )
    list_filter = ('project_type', 'complexity_level', 'is_public', 'is_featured', 'created_at')
    search_fields = ('name', 'description', 'creator__username')
    date_hierarchy = 'created_at'
    readonly_fields = ('times_used', 'rating', 'created_at', 'updated_at')
    raw_id_fields = ('creator', 'source_project')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'creator', 'source_project')
        }),
        ('Template Configuration', {
            'fields': ('project_type', 'complexity_level', 'template_data')
        }),
        ('Usage & Visibility', {
            'fields': ('times_used', 'rating', 'is_public', 'is_featured')
        }),
    )

    def creator_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.creator.pk])
        return format_html('<a href="{}">{}</a>', url, obj.creator.username)
    creator_link.short_description = 'Creator'

    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.admin_order_field = 'created_at'
    created_at_display.short_description = 'Created At'


# --- ErrorLog Administration ---
@admin.register(ErrorLog)
class ErrorLogAdmin(admin.ModelAdmin):
    list_display = (
        'project_link', 'error_type', 'error_message_snippet', 'is_resolved',
        'auto_fix_attempted', 'auto_fix_successful', 'created_at_display'
    )
    list_filter = (
        'error_type', 'is_resolved', 'auto_fix_attempted',
        'auto_fix_successful', 'project', 'created_at'
    )
    search_fields = ('error_message', 'error_traceback', 'file_path', 'command_executed', 'project__name')
    date_hierarchy = 'created_at'
    readonly_fields = ('fix_applied_at', 'claude_thread_used', 'tokens_used_for_fix', 'created_at')
    raw_id_fields = ('project', 'session')
    fieldsets = (
        (None, {
            'fields': ('project', 'session', 'error_type', 'error_message', 'error_traceback')
        }),
        ('Context', {
            'fields': ('file_path', 'line_number', 'command_executed', 'user_action')
        }),
        ('Resolution Status', {
            'fields': ('is_resolved', 'auto_fix_attempted', 'auto_fix_successful', 'fix_description', 'fix_applied_at')
        }),
        ('AI Interaction Details', {
            'fields': ('claude_thread_used', 'tokens_used_for_fix'),
            'classes': ('collapse',)
        }),
    )

    def project_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_project_change', args=[obj.project.pk])
        return format_html('<a href="{}">{}</a>', url, obj.project.name)
    project_link.short_description = 'Project'

    def error_message_snippet(self, obj):
        return obj.error_message[:75] + '...' if len(obj.error_message) > 75 else obj.error_message
    error_message_snippet.short_description = 'Error Message'

    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.admin_order_field = 'created_at'
    created_at_display.short_description = 'Created At'


# --- UsageAnalytics Administration ---
@admin.register(UsageAnalytics)
class UsageAnalyticsAdmin(admin.ModelAdmin):
    list_display = (
        'user_link', 'project_link', 'action_type', 'success',
        'response_time_ms', 'tokens_used', 'timestamp_display'
    )
    list_filter = ('action_type', 'success', 'user', 'project', 'timestamp')
    search_fields = ('user__username', 'project__name', 'action_data', 'page_url')
    date_hierarchy = 'timestamp'
    readonly_fields = ('timestamp', 'user_agent', 'page_url', 'referrer')
    raw_id_fields = ('user', 'project', 'session')
    fieldsets = (
        (None, {
            'fields': ('user', 'project', 'session', 'action_type', 'action_data')
        }),
        ('Performance & Outcome', {
            'fields': ('response_time_ms', 'tokens_used', 'success')
        }),
        ('Context', {
            'fields': ('user_agent', 'page_url', 'referrer')
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def project_link(self, obj):
        if obj.project:
            # Assuming 'main' is your app name for reversing
            url = reverse('admin:ai_builder_project_change', args=[obj.project.pk])
            return format_html('<a href="{}">{}</a>', url, obj.project.name)
        return "N/A"
    project_link.short_description = 'Project'

    def timestamp_display(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    timestamp_display.admin_order_field = 'timestamp'
    timestamp_display.short_description = 'Timestamp'


# --- Billing Administration ---
@admin.register(BillingPlan)
class BillingPlanAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'plan_type', 'price', 'billing_interval', 'token_limit',
        'max_projects', 'is_active', 'is_default_free', 'sort_order'
    )
    list_filter = ('plan_type', 'billing_interval', 'is_active', 'is_default_free')
    search_fields = ('name', 'description')
    ordering = ('sort_order', 'name')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'plan_type')
        }),
        ('Token & Resource Limits', {
            'fields': ('token_limit', 'bonus_tokens', 'max_projects', 'max_concurrent_containers')
        }),
        ('Pricing', {
            'fields': ('price', 'billing_interval')
        }),
        ('Advanced Features', {
            'fields': (
                ('enable_ai_chat', 'enable_auto_error_fix'),
                ('enable_advanced_templates', 'enable_custom_containers'),
                ('enable_code_export', 'enable_version_control'),
                ('enable_collaboration', 'enable_analytics'),
                ('enable_priority_support', 'enable_custom_models'),
                ('enable_api_access', 'enable_white_labeling')
            )
        }),
        ('Plan Settings', {
            'fields': ('is_active', 'is_default_free', 'sort_order')
        }),
    )


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'user_link', 'plan_link', 'status', 'started_at_display',
        'current_period_end_display', 'tokens_used_this_period', 'tokens_remaining',
        'usage_percentage_display', 'auto_renew'
    )
    list_filter = ('status', 'plan', 'auto_renew', 'current_period_end')
    search_fields = ('user__username', 'plan__name', 'stripe_subscription_id')
    date_hierarchy = 'started_at'
    readonly_fields = (
        'started_at', 'current_period_start', 'current_period_end', 'canceled_at',
        'tokens_used_this_period', 'bonus_tokens_remaining', 'last_payment_date',
        'next_payment_date'
    )
    raw_id_fields = ('user', 'plan')
    fieldsets = (
        (None, {
            'fields': ('user', 'plan', 'status', 'auto_renew')
        }),
        ('Subscription Dates', {
            'fields': ('started_at', 'current_period_start', 'current_period_end', 'canceled_at')
        }),
        ('Token Usage for Current Period', {
            'fields': ('tokens_used_this_period', 'bonus_tokens_remaining')
        }),
        ('Payment Gateway Details', {
            'fields': ('stripe_subscription_id', 'last_payment_date', 'next_payment_date'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def plan_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_billingplan_change', args=[obj.plan.pk])
        return format_html('<a href="{}">{}</a>', url, obj.plan.name)
    plan_link.short_description = 'Plan'

    def started_at_display(self, obj):
        return obj.started_at.strftime('%Y-%m-%d %H:%M')
    started_at_display.admin_order_field = 'started_at'
    started_at_display.short_description = 'Started At'

    def current_period_end_display(self, obj):
        return obj.current_period_end.strftime('%Y-%m-%d %H:%M')
    current_period_end_display.admin_order_field = 'current_period_end'
    current_period_end_display.short_description = 'Period End'

    def tokens_remaining(self, obj):
        remaining = obj.tokens_remaining
        if remaining == float('inf'):
            return "Unlimited"
        return remaining
    tokens_remaining.short_description = 'Tokens Remaining'

    def usage_percentage_display(self, obj):
        return f"{obj.usage_percentage:.2f}%"
    usage_percentage_display.short_description = 'Usage %'


@admin.register(TokenUsage)
class TokenUsageAdmin(admin.ModelAdmin):
    list_display = (
        'user_link', 'project_link', 'usage_type', 'tokens_used',
        'cost_dollars_display', 'success', 'created_at_display'
    )
    list_filter = ('usage_type', 'success', 'user', 'project', 'billing_period', 'created_at')
    search_fields = ('user__username', 'project__name', 'operation_description', 'error_message')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at', 'cost_cents', 'prompt_tokens', 'completion_tokens', 'response_time_ms', 'error_message')
    raw_id_fields = ('user', 'project', 'subscription')
    fieldsets = (
        (None, {
            'fields': ('user', 'project', 'subscription', 'usage_type', 'tokens_used')
        }),
        ('Detailed Token Breakdown', {
            'fields': ('prompt_tokens', 'completion_tokens')
        }),
        ('Context & Outcome', {
            'fields': ('operation_description', 'request_data', 'response_data', 'success', 'error_message')
        }),
        ('Performance & Billing', {
            'fields': ('response_time_ms', 'cost_cents', 'billing_period')
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def project_link(self, obj):
        if obj.project:
            # Assuming 'main' is your app name for reversing
            url = reverse('admin:ai_builder_project_change', args=[obj.project.pk])
            return format_html('<a href="{}">{}</a>', url, obj.project.name)
        return "N/A"
    project_link.short_description = 'Project'

    def cost_dollars_display(self, obj):
        return f"${obj.cost_dollars:.2f}"
    cost_dollars_display.short_description = 'Cost (USD)'

    def created_at_display(self, obj):
        return obj.created_at.strftime('%Y-%m-%d %H:%M:%S')
    created_at_display.admin_order_field = 'created_at'
    created_at_display.short_description = 'Used At'


@admin.register(BillingInvoice)
class BillingInvoiceAdmin(admin.ModelAdmin):
    list_display = (
        'invoice_number', 'user_link', 'subscription_link', 'total_amount',
        'status', 'issued_date_display', 'due_date', 'paid_date_display'
    )
    list_filter = ('status', 'issued_date', 'due_date', 'user', 'subscription')
    search_fields = ('invoice_number', 'user__username', 'subscription__plan__name')
    date_hierarchy = 'issued_date'
    readonly_fields = ('issued_date', 'paid_date', 'created_at', 'updated_at', 'stripe_invoice_id', 'payment_method')
    raw_id_fields = ('user', 'subscription')
    fieldsets = (
        (None, {
            'fields': ('invoice_number', 'user', 'subscription', 'status')
        }),
        ('Billing Period', {
            'fields': ('billing_period_start', 'billing_period_end')
        }),
        ('Amounts', {
            'fields': ('subscription_amount', 'token_overage_amount', 'tax_amount', 'total_amount')
        }),
        ('Usage Summary', {
            'fields': ('tokens_included', 'tokens_used', 'tokens_overage')
        }),
        ('Dates', {
            'fields': ('issued_date', 'due_date', 'paid_date')
        }),
        ('Payment Details', {
            'fields': ('stripe_invoice_id', 'payment_method'),
            'classes': ('collapse',)
        }),
    )

    def user_link(self, obj):
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'User'

    def subscription_link(self, obj):
        # Assuming 'main' is your app name for reversing
        url = reverse('admin:ai_builder_usersubscription_change', args=[obj.subscription.pk])
        return format_html('<a href="{}">{}</a>', url, obj.subscription.plan.name)
    subscription_link.short_description = 'Subscription Plan'

    def issued_date_display(self, obj):
        return obj.issued_date.strftime('%Y-%m-%d')
    issued_date_display.admin_order_field = 'issued_date'
    issued_date_display.short_description = 'Issued Date'

    def paid_date_display(self, obj):
        if obj.paid_date:
            return obj.paid_date.strftime('%Y-%m-%d')
        return "N/A"
    paid_date_display.admin_order_field = 'paid_date'
    paid_date_display.short_description = 'Paid Date'
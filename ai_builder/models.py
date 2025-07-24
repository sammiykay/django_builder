from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone

class Project(models.Model):
    PROJECT_TYPES = [
        ('web_app', 'Web Application'),
        ('api', 'API Service'),
        ('blog', 'Blog/CMS'),
        ('ecommerce', 'E-commerce'),
        ('dashboard', 'Dashboard/Analytics'),
        ('social', 'Social Platform'),
        ('portfolio', 'Portfolio Site'),
        ('business', 'Business Management'),
        ('education', 'Educational Platform'),
        ('entertainment', 'Entertainment/Media'),
        ('custom', 'Custom Application'),
    ]
    
    COMPLEXITY_LEVELS = [
        ('simple', 'Simple (1-3 models)'),
        ('medium', 'Medium (4-8 models)'),
        ('complex', 'Complex (9+ models)'),
        ('enterprise', 'Enterprise (Advanced features)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Dynamic project configuration
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES, default='custom')
    complexity_level = models.CharField(max_length=20, choices=COMPLEXITY_LEVELS, default='simple')
    target_audience = models.CharField(max_length=200, blank=True, help_text="Who will use this application?")
    key_features = models.JSONField(default=list, blank=True, help_text="List of main features requested")
    technical_requirements = models.JSONField(default=dict, blank=True, help_text="Special technical needs")
    
    # Project settings
    python_version = models.CharField(max_length=10, default='3.11')
    django_version = models.CharField(max_length=10, default='5.0')
    
    # Container info
    container_id = models.CharField(max_length=200, blank=True, null=True)
    container_port = models.IntegerField(blank=True, null=True)
    is_running = models.BooleanField(default=False)
    
    # Django project generation status
    django_project_created = models.BooleanField(default=False)
    main_app_name = models.CharField(max_length=100, blank=True, null=True)
    
    # AI generation tracking
    last_prompt = models.TextField(blank=True)
    original_prompt = models.TextField(blank=True, help_text="The initial user request")
    ai_generation_status = models.CharField(max_length=50, default='ready', choices=[
        ('ready', 'Ready'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('error', 'Error'),
    ])
    
    # Dynamic prompt evolution tracking
    prompt_history = models.JSONField(default=list, blank=True, help_text="History of all user prompts")
    generated_features = models.JSONField(default=list, blank=True, help_text="Features that have been implemented")
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name

class ProjectFile(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    path = models.CharField(max_length=500)  # Relative path from project root
    content = models.TextField()
    file_type = models.CharField(max_length=50)  # py, html, css, js, etc.
    size = models.IntegerField(default=0)  # File size in bytes
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # AI generation tracking
    is_ai_generated = models.BooleanField(default=False)
    ai_merge_status = models.CharField(max_length=50, default='none', choices=[
        ('none', 'No AI Content'),
        ('new', 'New AI Generated'),
        ('merged', 'Merged with Existing'),
        ('conflict', 'Merge Conflict'),
    ])
    original_content = models.TextField(blank=True)  # Store original before AI merge
    
    class Meta:
        unique_together = ['project', 'path']
        ordering = ['path']
    
    def save(self, *args, **kwargs):
        if self.content:
            self.size = len(self.content.encode('utf-8'))
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.project.name}/{self.path}"

class ChatThread(models.Model):
    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name='chat_thread')
    thread_id = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    # Thread settings
    is_active = models.BooleanField(default=True)
    context_length = models.IntegerField(default=20)  # Number of messages to keep in context
    
    def __str__(self):
        return f"Chat Thread for {self.project.name}"

class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]
    
    MESSAGE_TYPES = [
        ('normal', 'Normal Chat'),
        ('error_report', 'Error Report'),
        ('code_request', 'Code Request'),
        ('fix_applied', 'Fix Applied'),
        ('system_notification', 'System Notification'),
    ]
    
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    message_type = models.CharField(max_length=20, choices=MESSAGE_TYPES, default='normal')
    timestamp = models.DateTimeField(auto_now_add=True)
    
    # Error handling specific fields
    is_error_report = models.BooleanField(default=False)
    error_type = models.CharField(max_length=100, blank=True)
    error_source = models.CharField(max_length=200, blank=True)  # File or component where error occurred
    
    # Code modification tracking
    files_modified = models.JSONField(default=list, blank=True)
    code_changes = models.JSONField(default=dict, blank=True)
    
    # Additional metadata
    tokens_used = models.IntegerField(null=True, blank=True)
    processing_time = models.FloatField(null=True, blank=True)  # seconds
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.project.name} - {self.role}: {self.content[:50]}..."

class CommandExecution(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='executions')
    command = models.CharField(max_length=500)
    output = models.TextField(blank=True)
    error_output = models.TextField(blank=True)
    exit_code = models.IntegerField()
    execution_time = models.FloatField()  # seconds
    executed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-executed_at']
    
    def __str__(self):
        return f"{self.project.name}: {self.command}"


class UserProfile(models.Model):
    """
    Extended user profile for enhanced functionality
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Personal Information
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=100, blank=True)
    website = models.URLField(blank=True)
    github_username = models.CharField(max_length=100, blank=True)
    linkedin_url = models.URLField(blank=True)
    
    # Profile settings
    preferred_theme = models.CharField(max_length=20, default='dark', choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('auto', 'Auto'),
    ])
    preferred_language = models.CharField(max_length=10, default='en', choices=[
        ('en', 'English'),
        ('es', 'Spanish'),
        ('fr', 'French'),
        ('de', 'German'),
    ])
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    project_updates = models.BooleanField(default=True)
    
    # Usage statistics
    total_projects_created = models.IntegerField(default=0)
    total_ai_requests = models.IntegerField(default=0)
    total_tokens_used = models.BigIntegerField(default=0)
    
    # Preferences
    default_project_type = models.CharField(max_length=20, blank=True)
    default_complexity = models.CharField(max_length=20, default='simple')
    auto_fix_errors = models.BooleanField(default=True)
    enable_analytics = models.BooleanField(default=True)
    
    # Subscription & limits
    plan_type = models.CharField(max_length=20, default='free', choices=[
        ('free', 'Free'),
        ('pro', 'Pro'),
        ('enterprise', 'Enterprise'),
    ])
    monthly_token_limit = models.BigIntegerField(default=100000)  # Free tier limit
    monthly_tokens_used = models.BigIntegerField(default=0)
    billing_cycle_start = models.DateTimeField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()
    
    @property
    def display_name(self):
        return self.full_name if self.full_name else self.user.username
    
    def reset_monthly_usage(self):
        """Reset monthly token usage"""
        self.monthly_tokens_used = 0
        self.billing_cycle_start = timezone.now()
        self.save()
    
    def can_use_tokens(self, token_count: int) -> bool:
        """Check if user can use the requested number of tokens"""
        return self.monthly_tokens_used + token_count <= self.monthly_token_limit
    
    def use_tokens(self, token_count: int):
        """Record token usage"""
        self.monthly_tokens_used += token_count
        self.total_tokens_used += token_count
        self.save()


class ProjectSession(models.Model):
    """
    Track user sessions within projects for analytics and history
    """
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='sessions')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_sessions')
    
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    # Activity tracking
    messages_sent = models.IntegerField(default=0)
    files_modified = models.IntegerField(default=0)
    commands_executed = models.IntegerField(default=0)
    errors_encountered = models.IntegerField(default=0)
    
    # User agent and context
    user_agent = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    referrer = models.URLField(blank=True)
    
    class Meta:
        ordering = ['-start_time']
    
    def end_session(self):
        """Mark session as ended and calculate duration"""
        self.end_time = timezone.now()
        if self.start_time:
            self.duration_seconds = int((self.end_time - self.start_time).total_seconds())
        self.save()
    
    def __str__(self):
        return f"{self.user.username} - {self.project.name} ({self.start_time.strftime('%Y-%m-%d %H:%M')})"


class ProjectTemplate(models.Model):
    """
    Reusable project templates created from successful projects
    """
    name = models.CharField(max_length=200)
    description = models.TextField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_templates')
    source_project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Template configuration
    project_type = models.CharField(max_length=20)
    complexity_level = models.CharField(max_length=20)
    template_data = models.JSONField(default=dict)  # Store the template structure
    
    # Usage statistics
    times_used = models.IntegerField(default=0)
    rating = models.FloatField(default=0.0)
    
    # Sharing settings
    is_public = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Template: {self.name}"


class ErrorLog(models.Model):
    """
    Enhanced error tracking for auto-fix functionality
    """
    ERROR_TYPES = [
        ('syntax', 'Syntax Error'),
        ('import', 'Import Error'),
        ('runtime', 'Runtime Error'),
        ('database', 'Database Error'),
        ('network', 'Network Error'),
        ('permission', 'Permission Error'),
        ('container', 'Container Error'),
        ('other', 'Other Error'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='error_logs')
    session = models.ForeignKey(ProjectSession, on_delete=models.SET_NULL, null=True, blank=True)
    
    error_type = models.CharField(max_length=20, choices=ERROR_TYPES)
    error_message = models.TextField()
    error_traceback = models.TextField(blank=True)
    file_path = models.CharField(max_length=500, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    
    # Context
    command_executed = models.CharField(max_length=500, blank=True)
    user_action = models.CharField(max_length=200, blank=True)
    
    # Resolution tracking
    is_resolved = models.BooleanField(default=False)
    auto_fix_attempted = models.BooleanField(default=False)
    auto_fix_successful = models.BooleanField(default=False)
    fix_description = models.TextField(blank=True)
    fix_applied_at = models.DateTimeField(null=True, blank=True)
    
    # AI interaction
    claude_thread_used = models.UUIDField(null=True, blank=True)
    tokens_used_for_fix = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def mark_resolved(self, fix_description: str = '', auto_fixed: bool = False):
        """Mark error as resolved"""
        self.is_resolved = True
        self.fix_description = fix_description
        self.auto_fix_successful = auto_fixed
        self.fix_applied_at = timezone.now()
        self.save()
    
    def __str__(self):
        return f"{self.project.name}: {self.error_type} - {self.error_message[:50]}..."


class UsageAnalytics(models.Model):
    """
    Track detailed usage analytics for improving UX
    """
    ACTION_TYPES = [
        ('project_create', 'Project Created'),
        ('ai_generation', 'AI Generation'),
        ('file_edit', 'File Edited'),
        ('command_run', 'Command Executed'),
        ('container_start', 'Container Started'),
        ('error_occurred', 'Error Occurred'),
        ('error_fixed', 'Error Fixed'),
        ('session_start', 'Session Started'),
        ('session_end', 'Session Ended'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True)
    session = models.ForeignKey(ProjectSession, on_delete=models.SET_NULL, null=True, blank=True)
    
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    action_data = models.JSONField(default=dict)  # Store additional context
    
    # Performance metrics
    response_time_ms = models.IntegerField(null=True, blank=True)
    tokens_used = models.IntegerField(default=0)
    success = models.BooleanField(default=True)
    
    # Context
    user_agent = models.TextField(blank=True)
    page_url = models.URLField(blank=True)
    referrer = models.URLField(blank=True)
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', '-timestamp']),
            models.Index(fields=['action_type', '-timestamp']),
            models.Index(fields=['project', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.action_type} at {self.timestamp}"


class BillingPlan(models.Model):
    """
    Dynamic billing plans that can be created/managed by superusers
    """
    PLAN_TYPES = [
        ('free', 'Free'),
        ('paid', 'Paid'),
        ('enterprise', 'Enterprise'),
    ]
    
    BILLING_INTERVALS = [
        ('monthly', 'Monthly'),
        ('yearly', 'Yearly'),
        ('one_time', 'One Time'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES)
    
    # Token allocation
    token_limit = models.BigIntegerField(help_text="Token limit per billing cycle (0 = unlimited)")
    bonus_tokens = models.BigIntegerField(default=0, help_text="Additional tokens given on signup")
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    billing_interval = models.CharField(max_length=20, choices=BILLING_INTERVALS, default='monthly')
    
    # Features
    max_projects = models.IntegerField(default=10, help_text="Maximum number of projects (0 = unlimited)")
    max_concurrent_containers = models.IntegerField(default=1)
    
    # Advanced Features (Boolean fields for easy selection)
    enable_ai_chat = models.BooleanField(default=True, help_text="Enable AI chat functionality")
    enable_auto_error_fix = models.BooleanField(default=False, help_text="Enable automatic error fixing")
    enable_advanced_templates = models.BooleanField(default=False, help_text="Access to advanced project templates")
    enable_custom_containers = models.BooleanField(default=False, help_text="Use custom Docker configurations")
    enable_code_export = models.BooleanField(default=True, help_text="Export generated code")
    enable_version_control = models.BooleanField(default=False, help_text="Git integration and version control")
    enable_collaboration = models.BooleanField(default=False, help_text="Team collaboration features")
    enable_analytics = models.BooleanField(default=False, help_text="Advanced usage analytics")
    enable_priority_support = models.BooleanField(default=False, help_text="Priority customer support")
    enable_custom_models = models.BooleanField(default=False, help_text="Access to different AI models")
    enable_api_access = models.BooleanField(default=False, help_text="API access for external integrations")
    enable_white_labeling = models.BooleanField(default=False, help_text="White-label customization")
    
    # Plan settings
    is_active = models.BooleanField(default=True)
    is_default_free = models.BooleanField(default=False, help_text="Default plan for new users")
    sort_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_plan_type_display()})"
    
    @property
    def is_free(self):
        return self.plan_type == 'free' or self.price == 0


class UserSubscription(models.Model):
    """
    User's current subscription to a billing plan
    """
    SUBSCRIPTION_STATUS = [
        ('active', 'Active'),
        ('canceled', 'Canceled'),
        ('expired', 'Expired'),
        ('suspended', 'Suspended'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(BillingPlan, on_delete=models.PROTECT)
    
    # Subscription dates
    started_at = models.DateTimeField(auto_now_add=True)
    current_period_start = models.DateTimeField(default=timezone.now)
    current_period_end = models.DateTimeField()
    canceled_at = models.DateTimeField(null=True, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=SUBSCRIPTION_STATUS, default='active')
    auto_renew = models.BooleanField(default=True)
    
    # Token tracking for current period
    tokens_used_this_period = models.BigIntegerField(default=0)
    bonus_tokens_remaining = models.BigIntegerField(default=0)
    
    # Payment tracking
    stripe_subscription_id = models.CharField(max_length=200, blank=True)
    last_payment_date = models.DateTimeField(null=True, blank=True)
    next_payment_date = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.plan.name}"
    
    @property
    def is_active(self):
        return self.status == 'active' and timezone.now() <= self.current_period_end
    
    @property
    def tokens_remaining(self):
        """Calculate remaining tokens including bonus tokens"""
        if self.plan.token_limit == 0:  # Unlimited
            return float('inf')
        
        total_available = self.plan.token_limit + self.bonus_tokens_remaining
        return max(0, total_available - self.tokens_used_this_period)
    
    @property
    def usage_percentage(self):
        """Calculate usage percentage for current period"""
        if self.plan.token_limit == 0:
            return 0
        
        total_limit = self.plan.token_limit + self.bonus_tokens_remaining
        if total_limit == 0:
            return 100
        
        return min(100, (self.tokens_used_this_period / total_limit) * 100)
    
    def can_use_tokens(self, token_count: int) -> tuple[bool, str]:
        """Check if user can use tokens and return reason if not"""
        if not self.is_active:
            return False, "Subscription is not active"
        
        if self.user.is_superuser:
            return True, "Superuser has unlimited access"
        
        if self.plan.token_limit == 0:  # Unlimited plan
            return True, "Unlimited plan"
        
        if self.tokens_remaining >= token_count:
            return True, "Sufficient tokens available"
        
        return False, f"Insufficient tokens. Need {token_count}, have {self.tokens_remaining}"
    
    def use_tokens(self, token_count: int) -> bool:
        """Use tokens and return success status"""
        can_use, reason = self.can_use_tokens(token_count)
        if not can_use:
            return False
        
        if not self.user.is_superuser and self.plan.token_limit > 0:
            self.tokens_used_this_period += token_count
            
            # Use bonus tokens first
            if self.bonus_tokens_remaining > 0:
                bonus_used = min(token_count, self.bonus_tokens_remaining)
                self.bonus_tokens_remaining -= bonus_used
            
            self.save()
        
        return True
    
    def reset_period(self):
        """Reset for new billing period"""
        from dateutil.relativedelta import relativedelta
        
        self.current_period_start = timezone.now()
        
        if self.plan.billing_interval == 'monthly':
            self.current_period_end = self.current_period_start + relativedelta(months=1)
        elif self.plan.billing_interval == 'yearly':
            self.current_period_end = self.current_period_start + relativedelta(years=1)
        else:  # one_time
            self.current_period_end = self.current_period_start + relativedelta(years=100)
        
        self.tokens_used_this_period = 0
        self.save()


class TokenUsage(models.Model):
    """
    Detailed token usage tracking for analytics and billing
    """
    USAGE_TYPES = [
        ('ai_generation', 'AI Code Generation'),
        ('chat_message', 'Chat Message'),
        ('error_fix', 'Auto Error Fix'),
        ('file_analysis', 'File Analysis'),
        ('project_planning', 'Project Planning'),
        ('code_review', 'Code Review'),
        ('other', 'Other'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='token_usage')
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.ForeignKey(UserSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Usage details
    usage_type = models.CharField(max_length=20, choices=USAGE_TYPES)
    tokens_used = models.IntegerField()
    prompt_tokens = models.IntegerField(default=0)
    completion_tokens = models.IntegerField(default=0)
    
    # Context
    operation_description = models.CharField(max_length=200, blank=True)
    request_data = models.JSONField(default=dict, blank=True)
    response_data = models.JSONField(default=dict, blank=True)
    
    # Performance
    response_time_ms = models.IntegerField(null=True, blank=True)
    success = models.BooleanField(default=True)
    error_message = models.TextField(blank=True)
    
    # Billing
    cost_cents = models.IntegerField(default=0, help_text="Cost in cents")
    billing_period = models.DateField(default=timezone.now)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['subscription', '-created_at']),
            models.Index(fields=['billing_period', 'user']),
            models.Index(fields=['usage_type', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username}: {self.tokens_used} tokens ({self.usage_type})"
    
    @property
    def cost_dollars(self):
        return self.cost_cents / 100


class BillingInvoice(models.Model):
    """
    Monthly/periodic billing invoices
    """
    INVOICE_STATUS = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('overdue', 'Overdue'),
        ('canceled', 'Canceled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='invoices')
    subscription = models.ForeignKey(UserSubscription, on_delete=models.PROTECT)
    
    # Invoice details
    invoice_number = models.CharField(max_length=50, unique=True)
    billing_period_start = models.DateField()
    billing_period_end = models.DateField()
    
    # Amounts
    subscription_amount = models.DecimalField(max_digits=10, decimal_places=2)
    token_overage_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Usage summary
    tokens_included = models.BigIntegerField()
    tokens_used = models.BigIntegerField()
    tokens_overage = models.BigIntegerField(default=0)
    
    # Status and dates
    status = models.CharField(max_length=20, choices=INVOICE_STATUS, default='draft')
    issued_date = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField()
    paid_date = models.DateTimeField(null=True, blank=True)
    
    # Payment details
    stripe_invoice_id = models.CharField(max_length=200, blank=True)
    payment_method = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-issued_date']
    
    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number
            import datetime
            prefix = datetime.datetime.now().strftime('%Y%m')
            last_invoice = BillingInvoice.objects.filter(
                invoice_number__startswith=prefix
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                sequence = int(last_invoice.invoice_number[-4:]) + 1
            else:
                sequence = 1
            
            self.invoice_number = f"{prefix}{sequence:04d}"
        
        super().save(*args, **kwargs)
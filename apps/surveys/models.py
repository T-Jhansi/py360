from django.db import models
from django.contrib.auth import get_user_model
from apps.core.models import BaseModel, TimestampedModel
from apps.customers.models import Customer
from apps.policies.models import Policy
from apps.campaigns.models import Campaign
import uuid
import json

User = get_user_model()

class SurveyCategory(BaseModel):
    """Survey categories for organization"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=7, default='#007bff')
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'survey_categories'
        ordering = ['name']
        verbose_name_plural = 'Survey Categories'
    
    def __str__(self):
        return self.name

class Survey(BaseModel):
    """Main survey model"""
    SURVEY_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived'),
    ]
    
    SURVEY_TYPE_CHOICES = [
        ('feedback', 'Customer Feedback'),
        ('satisfaction', 'Satisfaction Survey'),
        ('nps', 'Net Promoter Score'),
        ('renewal', 'Renewal Survey'),
        ('claim', 'Claim Experience'),
        ('onboarding', 'Onboarding Survey'),
        ('exit', 'Exit Survey'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(SurveyCategory, on_delete=models.SET_NULL, null=True, blank=True)
    survey_type = models.CharField(max_length=20, choices=SURVEY_TYPE_CHOICES, default='feedback')
    status = models.CharField(max_length=20, choices=SURVEY_STATUS_CHOICES, default='draft')
    
    # Survey settings
    is_anonymous = models.BooleanField(default=False)
    allow_multiple_responses = models.BooleanField(default=False)
    require_login = models.BooleanField(default=True)
    show_progress_bar = models.BooleanField(default=True)
    randomize_questions = models.BooleanField(default=False)
    
    # Timing
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(default=5, help_text="Estimated duration in minutes")
    
    # Access control
    is_public = models.BooleanField(default=False)
    access_code = models.CharField(max_length=50, blank=True)
    target_audience = models.CharField(max_length=50, choices=[
        ('all_customers', 'All Customers'),
        ('policy_holders', 'Policy Holders'),
        ('specific_policies', 'Specific Policies'),
        ('custom_segment', 'Custom Segment'),
    ], default='all_customers')
    
    # Appearance
    theme_color = models.CharField(max_length=7, default='#007bff')
    logo = models.ImageField(upload_to='survey_logos/', null=True, blank=True)
    custom_css = models.TextField(blank=True)
    
    # Completion settings
    thank_you_message = models.TextField(default="Thank you for your feedback!")
    redirect_url = models.URLField(blank=True)
    send_completion_email = models.BooleanField(default=False)
    
    # Statistics
    total_questions = models.PositiveIntegerField(default=0)
    total_responses = models.PositiveIntegerField(default=0)
    completed_responses = models.PositiveIntegerField(default=0)
    average_completion_time = models.PositiveIntegerField(default=0, help_text="Average completion time in seconds")
    
    # System fields
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_surveys')
    
    class Meta:
        db_table = 'surveys'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'start_date']),
            models.Index(fields=['survey_type', 'status']),
        ]
    
    def __str__(self):
        return self.title
    
    @property
    def response_rate(self):
        """Calculate response completion rate"""
        if self.total_responses == 0:
            return 0
        return round((self.completed_responses / self.total_responses) * 100, 2)

class SurveyQuestion(BaseModel):
    """Survey questions"""
    QUESTION_TYPE_CHOICES = [
        ('text', 'Text Input'),
        ('textarea', 'Long Text'),
        ('number', 'Number Input'),
        ('email', 'Email Input'),
        ('phone', 'Phone Input'),
        ('date', 'Date Input'),
        ('single_choice', 'Single Choice'),
        ('multiple_choice', 'Multiple Choice'),
        ('dropdown', 'Dropdown'),
        ('rating', 'Rating Scale'),
        ('likert', 'Likert Scale'),
        ('nps', 'Net Promoter Score'),
        ('matrix', 'Matrix/Grid'),
        ('file_upload', 'File Upload'),
        ('signature', 'Digital Signature'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    description = models.TextField(blank=True)
    
    # Question settings
    is_required = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    # Display settings
    show_on_same_page = models.BooleanField(default=True)
    page_number = models.PositiveIntegerField(default=1)
    
    # Validation
    validation_rules = models.JSONField(default=dict, blank=True)
    # Example: {"min_length": 10, "max_length": 500, "pattern": "regex"}
    
    # Options for choice questions
    options = models.JSONField(default=list, blank=True)
    # Example: [{"value": "1", "label": "Very Satisfied"}, {"value": "2", "label": "Satisfied"}]
    
    # Rating/Scale settings
    scale_min = models.PositiveIntegerField(default=1)
    scale_max = models.PositiveIntegerField(default=5)
    scale_labels = models.JSONField(default=dict, blank=True)
    # Example: {"1": "Poor", "5": "Excellent"}
    
    # Matrix questions
    matrix_rows = models.JSONField(default=list, blank=True)
    matrix_columns = models.JSONField(default=list, blank=True)
    
    # Logic and branching
    logic_conditions = models.JSONField(default=dict, blank=True)
    # Example: {"show_if": {"question_id": 1, "answer": "yes"}}
    
    class Meta:
        db_table = 'survey_questions'
        ordering = ['survey', 'order']
        unique_together = ['survey', 'order']
    
    def __str__(self):
        return f"{self.survey.title} - Q{self.order}: {self.question_text[:50]}"

class SurveyResponse(BaseModel):
    """Survey responses from customers"""
    RESPONSE_STATUS_CHOICES = [
        ('started', 'Started'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='responses')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, null=True, blank=True, related_name='survey_responses')
    policy = models.ForeignKey(Policy, on_delete=models.SET_NULL, null=True, blank=True, related_name='survey_responses')
    
    # Response details
    status = models.CharField(max_length=20, choices=RESPONSE_STATUS_CHOICES, default='started')
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completion_time = models.PositiveIntegerField(null=True, blank=True, help_text="Completion time in seconds")
    
    # Anonymous responses
    anonymous_id = models.UUIDField(default=uuid.uuid4, unique=True)
    
    # Response metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referrer = models.URLField(blank=True)
    
    # Campaign tracking
    campaign = models.ForeignKey(Campaign, on_delete=models.SET_NULL, null=True, blank=True)
    utm_source = models.CharField(max_length=100, blank=True)
    utm_medium = models.CharField(max_length=100, blank=True)
    utm_campaign = models.CharField(max_length=100, blank=True)
    
    # Overall satisfaction (for quick analysis)
    overall_rating = models.FloatField(null=True, blank=True)
    nps_score = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'survey_responses'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['survey', 'status']),
            models.Index(fields=['customer', 'completed_at']),
        ]
    
    def __str__(self):
        customer_name = self.customer.full_name if self.customer else f"Anonymous ({self.anonymous_id})"
        return f"{self.survey.title} - {customer_name}"

class SurveyAnswer(BaseModel):
    """Individual answers to survey questions"""
    response = models.ForeignKey(SurveyResponse, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name='answers')
    
    # Answer data
    text_answer = models.TextField(blank=True)
    number_answer = models.FloatField(null=True, blank=True)
    date_answer = models.DateField(null=True, blank=True)
    boolean_answer = models.BooleanField(null=True, blank=True)
    
    # For choice questions
    selected_options = models.JSONField(default=list, blank=True)
    
    # For file uploads
    file_answer = models.FileField(upload_to='survey_uploads/', null=True, blank=True)
    
    # For matrix questions
    matrix_answers = models.JSONField(default=dict, blank=True)
    
    # Answer metadata
    answered_at = models.DateTimeField(auto_now_add=True)
    time_spent = models.PositiveIntegerField(default=0, help_text="Time spent on this question in seconds")
    
    class Meta:
        db_table = 'survey_answers'
        unique_together = ['response', 'question']
        ordering = ['response', 'question__order']
    
    def __str__(self):
        return f"{self.response} - {self.question.question_text[:30]}"

class SurveyLogic(BaseModel):
    """Survey logic and branching rules"""
    LOGIC_TYPE_CHOICES = [
        ('show_question', 'Show Question'),
        ('hide_question', 'Hide Question'),
        ('jump_to_question', 'Jump to Question'),
        ('end_survey', 'End Survey'),
        ('show_page', 'Show Page'),
        ('hide_page', 'Hide Page'),
    ]
    
    CONDITION_TYPE_CHOICES = [
        ('equals', 'Equals'),
        ('not_equals', 'Not Equals'),
        ('contains', 'Contains'),
        ('not_contains', 'Does Not Contain'),
        ('greater_than', 'Greater Than'),
        ('less_than', 'Less Than'),
        ('is_empty', 'Is Empty'),
        ('is_not_empty', 'Is Not Empty'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='logic_rules')
    name = models.CharField(max_length=200)
    
    # Trigger conditions
    trigger_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, related_name='logic_triggers')
    condition_type = models.CharField(max_length=20, choices=CONDITION_TYPE_CHOICES)
    condition_value = models.TextField()  # The value to compare against
    
    # Actions
    logic_type = models.CharField(max_length=20, choices=LOGIC_TYPE_CHOICES)
    target_question = models.ForeignKey(SurveyQuestion, on_delete=models.CASCADE, null=True, blank=True, related_name='logic_targets')
    target_page = models.PositiveIntegerField(null=True, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        db_table = 'survey_logic'
        ordering = ['survey', 'order']
    
    def __str__(self):
        return f"{self.survey.title} - {self.name}"

class SurveyInvitation(BaseModel):
    """Survey invitations sent to customers"""
    INVITATION_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('opened', 'Opened'),
        ('responded', 'Responded'),
        ('bounced', 'Bounced'),
        ('failed', 'Failed'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='invitations')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='survey_invitations')
    
    # Invitation details
    invitation_token = models.UUIDField(default=uuid.uuid4, unique=True)
    email_subject = models.CharField(max_length=200)
    email_content = models.TextField()
    
    # Delivery tracking
    status = models.CharField(max_length=20, choices=INVITATION_STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    
    # Response tracking
    survey_response = models.ForeignKey(SurveyResponse, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Reminders
    reminder_count = models.PositiveIntegerField(default=0)
    last_reminder_sent = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'survey_invitations'
        unique_together = ['survey', 'customer']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.survey.title} invitation to {self.customer.full_name}"

class SurveyReport(BaseModel):
    """Generated survey reports"""
    REPORT_TYPE_CHOICES = [
        ('summary', 'Summary Report'),
        ('detailed', 'Detailed Report'),
        ('comparison', 'Comparison Report'),
        ('trend', 'Trend Analysis'),
        ('nps', 'NPS Report'),
        ('custom', 'Custom Report'),
    ]
    
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='reports')
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    
    # Report configuration
    date_range_start = models.DateTimeField(null=True, blank=True)
    date_range_end = models.DateTimeField(null=True, blank=True)
    filters = models.JSONField(default=dict, blank=True)
    
    # Report data
    report_data = models.JSONField(default=dict)
    charts_config = models.JSONField(default=dict, blank=True)
    
    # File exports
    pdf_file = models.FileField(upload_to='survey_reports/', null=True, blank=True)
    excel_file = models.FileField(upload_to='survey_reports/', null=True, blank=True)
    
    # Generation details
    generated_at = models.DateTimeField(null=True, blank=True)
    generated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    generation_time = models.PositiveIntegerField(null=True, blank=True, help_text="Generation time in seconds")
    
    # Sharing
    is_public = models.BooleanField(default=False)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    
    class Meta:
        db_table = 'survey_reports'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.survey.title} - {self.name}"

class SurveyAnalytics(BaseModel):
    """Survey analytics and metrics"""
    survey = models.OneToOneField(Survey, on_delete=models.CASCADE, related_name='analytics')
    
    # Response metrics
    total_invitations = models.PositiveIntegerField(default=0)
    total_responses = models.PositiveIntegerField(default=0)
    completed_responses = models.PositiveIntegerField(default=0)
    abandoned_responses = models.PositiveIntegerField(default=0)
    
    # Timing metrics
    average_completion_time = models.PositiveIntegerField(default=0)
    median_completion_time = models.PositiveIntegerField(default=0)
    fastest_completion = models.PositiveIntegerField(default=0)
    slowest_completion = models.PositiveIntegerField(default=0)
    
    # Satisfaction metrics
    average_rating = models.FloatField(null=True, blank=True)
    nps_score = models.FloatField(null=True, blank=True)
    satisfaction_distribution = models.JSONField(default=dict, blank=True)
    
    # Question analytics
    question_analytics = models.JSONField(default=dict, blank=True)
    # Example: {"question_1": {"skip_rate": 5.2, "avg_time": 30}}
    
    # Demographic breakdown
    demographic_breakdown = models.JSONField(default=dict, blank=True)
    
    # Last updated
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'survey_analytics'
    
    def __str__(self):
        return f"Analytics - {self.survey.title}"

class SurveyFeedback(BaseModel):
    """Feedback about the survey itself"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='survey_feedback')
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Feedback details
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)])
    feedback_text = models.TextField()
    
    # Feedback categories
    categories = models.JSONField(default=list, blank=True)
    # Example: ["too_long", "confusing_questions", "technical_issues"]
    
    # Response
    is_resolved = models.BooleanField(default=False)
    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'survey_feedback'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback on {self.survey.title} - Rating: {self.rating}" 
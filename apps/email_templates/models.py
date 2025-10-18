# from django.db import models, transaction
# from django.contrib.auth import get_user_model
# from django.utils import timezone
# from django.template import Template, Context
# import uuid

# User = get_user_model()


# class EmailTemplateCategory(models.Model):
#     """Categories for organizing email templates"""
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True, null=True)
#     color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
#     is_active = models.BooleanField(default=True)
    
#     # Metadata
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_template_categories')
#     updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_template_categories')
#     is_deleted = models.BooleanField(default=False)
#     deleted_at = models.DateTimeField(blank=True, null=True)
#     deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_template_categories')
    
#     class Meta:
#         db_table = 'email_template_categories'
#         ordering = ['name']
#         verbose_name = 'Email Template Category'
#         verbose_name_plural = 'Email Template Categories'
    
#     def __str__(self):
#         return self.name


# class EmailTemplateTag(models.Model):
#     """Tags for categorizing email templates"""
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=50, unique=True)
#     description = models.TextField(blank=True, null=True)
#     color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
#     is_active = models.BooleanField(default=True)
    
#     # Metadata
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_template_tags')
#     updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_template_tags')
#     is_deleted = models.BooleanField(default=False)
#     deleted_at = models.DateTimeField(blank=True, null=True)
#     deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_template_tags')
    
#     class Meta:
#         db_table = 'email_template_tags'
#         ordering = ['name']
#         verbose_name = 'Email Template Tag'
#         verbose_name_plural = 'Email Template Tags'
    
#     def __str__(self):
#         return self.name


# class EmailTemplate(models.Model):
#     """Email templates for different purposes"""
    
#     TEMPLATE_TYPE_CHOICES = [
#         ('html', 'HTML'),
#         ('text', 'Plain Text'),
#         ('both', 'Both HTML and Text'),
#     ]
    
#     STATUS_CHOICES = [
#         ('draft', 'Draft'),
#         ('active', 'Active'),
#         ('inactive', 'Inactive'),
#         ('archived', 'Archived'),
#     ]
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=200)
#     subject = models.CharField(max_length=500)
#     description = models.TextField(blank=True, null=True)
    
#     # Template content
#     html_content = models.TextField(blank=True, null=True)
#     text_content = models.TextField(blank=True, null=True)
#     template_type = models.CharField(max_length=10, choices=TEMPLATE_TYPE_CHOICES, default='both')
    
#     variables = models.JSONField(default=dict, blank=True, help_text="Available variables for this template")
#     category = models.ForeignKey(EmailTemplateCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='templates')
#     tags = models.ManyToManyField(EmailTemplateTag, blank=True, related_name='templates')
    
#     status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
#     is_public = models.BooleanField(default=True, help_text="Available to all users")
    
#     usage_count = models.PositiveIntegerField(default=0)
#     last_used = models.DateTimeField(blank=True, null=True)
    
#     # Metadata
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_templates')
#     updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_templates')
#     is_deleted = models.BooleanField(default=False)
#     deleted_at = models.DateTimeField(blank=True, null=True)
#     deleted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_templates')
    
#     class Meta:
#         db_table = 'email_templates'
#         ordering = ['-created_at']
#         verbose_name = 'Email Template'
#         verbose_name_plural = 'Email Templates'

#     def __str__(self):
#         return self.name
    
#     def save(self, *args, **kwargs):
#         """
#         Override save to automatically create a new version on content change.
#         """
#         is_new = self._state.adding
#         super().save(*args, **kwargs) # Save first to get an ID for new instances

#         if is_new:
#             # Create the very first version when the template is created
#             EmailTemplateVersion.objects.create(
#                 template=self,
#                 name=self.name,
#                 subject=self.subject,
#                 html_content=self.html_content,
#                 text_content=self.text_content,
#                 change_summary="Initial version created.",
#                 created_by=self.created_by
#             )

#     def increment_usage(self):
#         """Increment usage count and update last used timestamp"""
#         self.usage_count += 1
#         self.last_used = timezone.now()
#         self.save(update_fields=['usage_count', 'last_used'])
    
#     def soft_delete(self, user: User = None):
#         """
#         Soft delete the template.
#         """
#         self.is_deleted = True
#         self.deleted_at = timezone.now()
#         self.status = 'archived'
#         self.deleted_by = user
#         self.save(update_fields=['is_deleted', 'deleted_at', 'status', 'deleted_by'])
    
#     def render_content(self, context: dict = None) -> dict:
#         """
#         Render template content with provided context using Django's template engine.
#         """
#         if context is None:
#             context = {}
            
#         subject_template = Template(self.subject)
#         html_template = Template(self.html_content or "")
#         text_template = Template(self.text_content or "")
#         template_context = Context(context)

#         return {
#             'subject': subject_template.render(template_context),
#             'html_content': html_template.render(template_context),
#             'text_content': text_template.render(template_context),
#         }

#     def duplicate(self, user: User = None):
#         """
#         Create a copy of this template.
#         """
#         with transaction.atomic():
#             new_template = EmailTemplate.objects.create(
#                 name=f"{self.name} (Copy)",
#                 subject=self.subject,
#                 description=self.description,
#                 html_content=self.html_content,
#                 text_content=self.text_content,
#                 template_type=self.template_type,
#                 variables=self.variables,
#                 category=self.category,
#                 status='draft',
#                 is_public=self.is_public,
#                 created_by=user,
#                 updated_by=user
#             )
#             new_template.tags.set(self.tags.all())
#             return new_template


# class EmailTemplateVersion(models.Model):
#     """Version history for email templates"""
    
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='versions')
#     version_number = models.PositiveIntegerField(editable=False)
    
#     name = models.CharField(max_length=200)
#     subject = models.CharField(max_length=500)
#     html_content = models.TextField(blank=True, null=True)
#     text_content = models.TextField(blank=True, null=True)
    
#     change_summary = models.TextField(blank=True, null=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_template_versions')
    
#     class Meta:
#         db_table = 'email_template_versions'
#         ordering = ['template', '-version_number']
#         unique_together = ['template', 'version_number']
#         verbose_name = 'Email Template Version'
#         verbose_name_plural = 'Email Template Versions'
    
#     def __str__(self):
#         return f"{self.template.name} v{self.version_number}"
    
#     def save(self, *args, **kwargs):
#         """Auto-increment version number on creation."""
#         if not self.pk: # Only on creation
#             last_version = EmailTemplateVersion.objects.filter(template=self.template).order_by('-version_number').first()
#             self.version_number = (last_version.version_number + 1) if last_version else 1
#         super().save(*args, **kwargs)
        
#     def restore(self, user: User = None):
#         """
#         Restore the main template to this version's content.
#         """
#         with transaction.atomic():
#             template = self.template
#             template.name = self.name
#             template.subject = self.subject
#             template.html_content = self.html_content
#             template.text_content = self.text_content
#             template.updated_by = user
#             template.save()

#             # Create a new version to record the restoration event
#             EmailTemplateVersion.objects.create(
#                 template=template,
#                 name=template.name,
#                 subject=template.subject,
#                 html_content=template.html_content,
#                 text_content=template.text_content,
#                 change_summary=f"Restored to version {self.version_number}",
#                 created_by=user
#             )
# from django.db import models, transaction
# from django.contrib.auth import get_user_model
# from django.utils import timezone
# from django.template import Template, Context
# from typing import Optional, TYPE_CHECKING
# import uuid

# if TYPE_CHECKING:
#     from django.contrib.auth.models import User


# class EmailTemplateCategory(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     name = models.CharField(max_length=100, unique=True)
#     description = models.TextField(blank=True, null=True)
#     color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_template_categories')
#     updated_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_template_categories')
#     is_deleted = models.BooleanField(default=False)
#     deleted_at = models.DateTimeField(blank=True, null=True)
#     deleted_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_template_categories')

from django.db import models, transaction
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.template import Template, Context
from typing import Optional, TYPE_CHECKING
import uuid

if TYPE_CHECKING:
    from django.contrib.auth.models import User


class EmailTemplateCategory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#007bff', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_template_categories')
    updated_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_template_categories')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_template_categories')
    
    class Meta:
        db_table = 'email_template_categories'
        ordering = ['name']
        verbose_name = 'Email Template Category'
        verbose_name_plural = 'Email Template Categories'
    
    def __str__(self):
        return self.name


class EmailTemplateTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    color = models.CharField(max_length=7, default='#6c757d', help_text="Hex color code")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_template_tags')
    updated_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_template_tags')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_template_tags')
    
    class Meta:
        db_table = 'email_template_tags'
        ordering = ['name']
        verbose_name = 'Email Template Tag'
        verbose_name_plural = 'Email Template Tags'
    
    def __str__(self):
        return self.name


class EmailTemplate(models.Model):
    TEMPLATE_TYPE_CHOICES = [('html', 'HTML'), ('text', 'Plain Text'), ('both', 'Both HTML and Text')]
    STATUS_CHOICES = [('draft', 'Draft'), ('active', 'Active'), ('inactive', 'Inactive'), ('archived', 'Archived')]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=500)
    description = models.TextField(blank=True, null=True)
    html_content = models.TextField(blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    template_type = models.CharField(max_length=10, choices=TEMPLATE_TYPE_CHOICES, default='both')
    variables = models.JSONField(default=dict, blank=True, help_text="Available variables for this template")
    category = models.ForeignKey(EmailTemplateCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='templates')
    tags = models.ManyToManyField(EmailTemplateTag, blank=True, related_name='templates')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_public = models.BooleanField(default=True, help_text="Available to all users")
    usage_count = models.PositiveIntegerField(default=0)
    last_used = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_templates')
    updated_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='updated_email_templates')
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(blank=True, null=True)
    deleted_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='deleted_email_templates')
    
    class Meta:
        db_table = 'email_templates'
        ordering = ['-created_at']
        verbose_name = 'Email Template'
        verbose_name_plural = 'Email Templates'

    def __str__(self):
        return self.name
    
    # --- THIS SECTION CONTAINS THE FIX ---
    def save(self, *args, **kwargs):
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            # Manually create an instance and then save it to ensure
            # the custom save() method on EmailTemplateVersion is called.
            version = EmailTemplateVersion(
                template=self, name=self.name, subject=self.subject,
                html_content=self.html_content, text_content=self.text_content,
                change_summary="Initial version created.", created_by=self.created_by
            )
            version.save()

    def increment_usage(self):
        self.usage_count += 1
        self.last_used = timezone.now()
        self.save(update_fields=['usage_count', 'last_used'])
    
    def soft_delete(self, user: Optional['User'] = None):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.status = 'archived'
        self.deleted_by = user
        self.save(update_fields=['is_deleted', 'deleted_at', 'status', 'deleted_by'])
    
    def render_content(self, context: Optional[dict] = None) -> dict:
        safe_context = context if context is not None else {}
        subject_template = Template(self.subject)
        html_template = Template(self.html_content or "")
        text_template = Template(self.text_content or "")
        template_context = Context(safe_context)
        return {
            'subject': subject_template.render(template_context),
            'html_content': html_template.render(template_context),
            'text_content': text_template.render(template_context),
        }

    def duplicate(self, user: Optional['User'] = None):
        with transaction.atomic():
            new_template = EmailTemplate.objects.create(
                name=f"{self.name} (Copy)", subject=self.subject, description=self.description,
                html_content=self.html_content, text_content=self.text_content,
                template_type=self.template_type, variables=self.variables, category=self.category,
                status='draft', is_public=self.is_public, created_by=user, updated_by=user
            )
            new_template.tags.set(self.tags.all())
            return new_template


class EmailTemplateVersion(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name='versions')
    version_number = models.PositiveIntegerField(editable=False)
    name = models.CharField(max_length=200)
    subject = models.CharField(max_length=500)
    html_content = models.TextField(blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)
    change_summary = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(get_user_model(), on_delete=models.SET_NULL, null=True, blank=True, related_name='created_email_template_versions')
    
    class Meta:
        db_table = 'email_template_versions'
        ordering = ['template', '-version_number']
        unique_together = ['template', 'version_number']
        verbose_name = 'Email Template Version'
        verbose_name_plural = 'Email Template Versions'
    
    def __str__(self):
        return f"{self.template.name} v{self.version_number}"
    
    def save(self, *args, **kwargs):
        if not self.version_number:
            latest_version = EmailTemplateVersion.objects.filter(
                template=self.template
            ).order_by('-version_number').first()
            
            if latest_version:
                self.version_number = latest_version.version_number + 1
            else:
                self.version_number = 1
        super().save(*args, **kwargs)
        
    def restore(self, user: Optional['User'] = None):
        with transaction.atomic():
            template = self.template
            template.name = self.name
            template.subject = self.subject
            template.html_content = self.html_content
            template.text_content = self.text_content
            template.updated_by = user
            template.save()

            version = EmailTemplateVersion(
                template=template, name=template.name, subject=template.subject,
                html_content=template.html_content, text_content=template.text_content,
                change_summary=f"Restored to version {self.version_number}", created_by=user
            )
            version.save()


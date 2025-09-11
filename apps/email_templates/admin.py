"""
Admin configuration for Email Templates
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import EmailTemplate, EmailTemplateVersion, EmailTemplateCategory, EmailTemplateTag


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin interface for EmailTemplate"""
    
    list_display = [
        'name', 'template_type', 'status', 'is_default', 'usage_count', 
        'created_by', 'created_at', 'last_used'
    ]
    list_filter = ['template_type', 'status', 'is_default', 'requires_approval', 'created_at']
    search_fields = ['name', 'subject', 'description', 'tags']
    readonly_fields = ['usage_count', 'last_used', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'subject', 'template_type', 'status', 'description', 'tags')
        }),
        ('Content', {
            'fields': ('html_content', 'text_content', 'variables')
        }),
        ('Settings', {
            'fields': ('is_default', 'requires_approval')
        }),
        ('Usage Tracking', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Filter out deleted templates"""
        return super().get_queryset(request).filter(is_deleted=False)
    
    def save_model(self, request, obj, form, change):
        """Save model with user context"""
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EmailTemplateVersion)
class EmailTemplateVersionAdmin(admin.ModelAdmin):
    """Admin interface for EmailTemplateVersion"""
    
    list_display = [
        'template', 'version_number', 'is_current', 'created_by', 'created_at'
    ]
    list_filter = ['is_current', 'created_at', 'template__template_type']
    search_fields = ['template__name', 'change_notes']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Filter out versions of deleted templates"""
        return super().get_queryset(request).filter(template__is_deleted=False)


@admin.register(EmailTemplateCategory)
class EmailTemplateCategoryAdmin(admin.ModelAdmin):
    """Admin interface for EmailTemplateCategory"""
    
    list_display = ['name', 'color_display', 'sort_order', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def color_display(self, obj):
        """Display color as colored square"""
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    def get_queryset(self, request):
        """Filter out deleted categories"""
        return super().get_queryset(request).filter(is_deleted=False)


@admin.register(EmailTemplateTag)
class EmailTemplateTagAdmin(admin.ModelAdmin):
    """Admin interface for EmailTemplateTag"""
    
    list_display = ['name', 'color_display', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    def color_display(self, obj):
        """Display color as colored square"""
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; '
            'background-color: {}; border: 1px solid #ccc;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'
    
    def get_queryset(self, request):
        """Filter out deleted tags"""
        return super().get_queryset(request).filter(is_deleted=False)

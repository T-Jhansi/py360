from django.contrib import admin
from django.db.models import Count
from django.urls import reverse
from django.utils.html import format_html
from .models import EmailTemplate, EmailTemplateCategory, EmailTemplateTag, EmailTemplateVersion


@admin.register(EmailTemplateCategory)
class EmailTemplateCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'is_active', 'template_count_display', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def color_display(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px; vertical-align: middle;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'

    def template_count_display(self, obj):
        # _# IMPROVED:_ This now uses the annotated value from get_queryset.
        return obj.template_count
    template_count_display.short_description = 'Templates'
    template_count_display.admin_order_field = 'template_count'

    def get_queryset(self, request):
        # _# OPTIMIZED:_ Use annotate to efficiently count templates in one query.
        queryset = super().get_queryset(request).filter(is_deleted=False)
        queryset = queryset.annotate(template_count=Count('templates'))
        return queryset


@admin.register(EmailTemplateTag)
class EmailTemplateTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color_display', 'is_active', 'template_count_display', 'created_at']
    list_filter = ['is_active']
    search_fields = ['name']
    readonly_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

    def color_display(self, obj):
        return format_html(
            '<span style="display: inline-block; width: 20px; height: 20px; background-color: {}; border: 1px solid #ccc; border-radius: 3px; vertical-align: middle;"></span> {}',
            obj.color, obj.color
        )
    color_display.short_description = 'Color'

    def template_count_display(self, obj):
        return obj.template_count
    template_count_display.short_description = 'Templates'
    template_count_display.admin_order_field = 'template_count'

    def get_queryset(self, request):
        # _# OPTIMIZED:_ Use annotate for efficiency.
        queryset = super().get_queryset(request).filter(is_deleted=False)
        queryset = queryset.annotate(template_count=Count('templates'))
        return queryset


class EmailTemplateVersionInline(admin.TabularInline):
    model = EmailTemplateVersion
    extra = 0
    # _# IMPROVED:_ Added a link to the full version object.
    fields = ['version_number', 'view_details_link', 'change_summary', 'created_at', 'created_by']
    readonly_fields = fields

    def view_details_link(self, obj):
        if obj.pk:
            url = reverse('admin:email_templates_emailtemplateversion_change', args=(obj.pk,))
            return format_html('<a href="{}">View Details</a>', url)
        return "N/A"
    view_details_link.short_description = 'Details'


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'category', 'status', 'usage_count', 'created_at']
    list_filter = ['status', 'template_type', 'category', 'is_public']
    search_fields = ['name', 'subject', 'description']
    readonly_fields = ['id', 'usage_count', 'last_used', 'created_at', 'updated_at', 'created_by', 'updated_by']
    filter_horizontal = ['tags']
    inlines = [EmailTemplateVersionInline]
    
    fieldsets = (
        ('Basic Information', {'fields': ('name', 'subject', 'description', 'category', 'tags')}),
        ('Content', {'fields': ('html_content', 'text_content', 'template_type', 'variables')}),
        ('Settings', {'fields': ('status', 'is_public')}),
        ('Metadata', {'fields': ('id', 'created_by', 'created_at', 'updated_by', 'updated_at'), 'classes': ('collapse',)}),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_deleted=False).select_related('category', 'created_by')


@admin.register(EmailTemplateVersion)
class EmailTemplateVersionAdmin(admin.ModelAdmin):
    list_display = ['template', 'version_number', 'change_summary', 'created_at', 'created_by']
    list_filter = ['created_at', 'template']
    search_fields = ['template__name', 'name', 'subject', 'change_summary']
    readonly_fields = [f.name for f in EmailTemplateVersion._meta.fields] # Make all fields read-only
    
    def has_add_permission(self, request):
        # Versions are created automatically, not manually in the admin.
        return False
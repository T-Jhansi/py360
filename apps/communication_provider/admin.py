from django.contrib import admin
from django.utils.html import format_html
from .models import CommunicationProvider


@admin.register(CommunicationProvider)
class CommunicationProviderAdmin(admin.ModelAdmin):    
    list_display = [
        'name', 
        'channel', 
        'is_default', 
        'is_active', 
        'created_by', 
        'created_at',
        'status_display'
    ]
    list_filter = [
        'channel', 
        'is_default', 
        'is_active', 
        'created_at',
        'deleted_at'
    ]
    search_fields = ['name', 'channel']
    readonly_fields = ['created_at', 'updated_at', 'deleted_at']
    ordering = ['channel', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'channel', 'is_default', 'is_active')
        }),
        ('Audit Information', {
            'fields': ('created_by', 'updated_by', 'deleted_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )

    def status_display(self, obj):        
        if obj.is_deleted:
            return format_html('<span style="color: red;">Deleted</span>')
        elif obj.is_active:
            return format_html('<span style="color: green;">Active</span>')
        else:
            return format_html('<span style="color: orange;">Inactive</span>')
    status_display.short_description = 'Status'

    def get_queryset(self, request):
        return super().get_queryset(request).filter(deleted_at__isnull=True)

    def save_model(self, request, obj, form, change):
        if not change: 
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['soft_delete_selected', 'restore_selected', 'activate_selected', 'deactivate_selected']

    def soft_delete_selected(self, request, queryset):
        count = 0
        for provider in queryset:
            if not provider.is_deleted:
                provider.soft_delete(user=request.user)
                count += 1
        self.message_user(request, f'{count} providers were soft deleted.')
    soft_delete_selected.short_description = "Soft delete selected providers"

    def restore_selected(self, request, queryset):
        count = 0
        for provider in queryset:
            if provider.is_deleted:
                provider.restore(user=request.user)
                count += 1
        self.message_user(request, f'{count} providers were restored.')
    restore_selected.short_description = "Restore selected providers"

    def activate_selected(self, request, queryset):
        count = queryset.filter(is_active=False).update(is_active=True, updated_by=request.user)
        self.message_user(request, f'{count} providers were activated.')
    activate_selected.short_description = "Activate selected providers"

    def deactivate_selected(self, request, queryset):
        count = queryset.filter(is_active=True).update(is_active=False, updated_by=request.user)
        self.message_user(request, f'{count} providers were deactivated.')
    deactivate_selected.short_description = "Deactivate selected providers"

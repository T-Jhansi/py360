from django.contrib import admin
from .models import Offer


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin configuration for Offer model"""
    
    list_display = [
        'title', 'offer_type', 'amount', 'discount', 'currency',
        'is_active', 'display_order', 'created_at'
    ]
    list_filter = [
        'offer_type', 'is_active', 'currency', 'created_at'
    ]
    search_fields = [
        'title', 'description', 'features'
    ]
    ordering = ['display_order', 'created_at']
    list_editable = ['is_active', 'display_order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'offer_type', 'is_active')
        }),
        ('Pricing & Discounts', {
            'fields': ('amount', 'discount', 'currency', 'interest_rate')
        }),
        ('Features & Details', {
            'fields': ('features', 'extra_info', 'terms_and_conditions')
        }),
        ('Display Settings', {
            'fields': ('display_order', 'icon', 'color_scheme')
        }),
        ('Validity Period', {
            'fields': ('start_date', 'end_date'),
            'classes': ('collapse',)
        }),
        ('Audit Information', {
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'created_by', 'updated_by']
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by fields"""
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
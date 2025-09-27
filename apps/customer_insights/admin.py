"""
Admin configuration for Customer Insights models.
"""

from django.contrib import admin
from .models import (
    CustomerInsight, PaymentInsight, CommunicationInsight, 
    ClaimsInsight, CustomerProfileInsight
)


@admin.register(CustomerInsight)
class CustomerInsightAdmin(admin.ModelAdmin):
    """Admin for CustomerInsight model"""
    
    list_display = [
        'id', 'customer', 'insight_type', 'calculated_at', 'is_active'
    ]
    list_filter = ['insight_type', 'is_active', 'calculated_at']
    search_fields = ['customer__customer_code', 'customer__first_name', 'customer__last_name']
    readonly_fields = ['calculated_at', 'created_at', 'updated_at']
    ordering = ['-calculated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer', 'insight_type', 'is_active')
        }),
        ('Data', {
            'fields': ('data',)
        }),
        ('Timestamps', {
            'fields': ('calculated_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentInsight)
class PaymentInsightAdmin(admin.ModelAdmin):
    """Admin for PaymentInsight model"""
    
    list_display = [
        'customer', 'total_premiums_paid', 'on_time_payment_rate', 
        'payment_reliability', 'customer_since_years'
    ]
    list_filter = ['payment_reliability', 'most_used_mode', 'created_at']
    search_fields = ['customer__customer_code', 'customer__first_name', 'customer__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
        }),
        ('Payment Statistics', {
            'fields': (
                'total_premiums_paid', 'on_time_payment_rate', 'total_payments_made',
                'average_payment_amount', 'customer_since_years'
            )
        }),
        ('Payment Patterns', {
            'fields': (
                'most_used_mode', 'preferred_payment_method', 'average_payment_timing',
                'payment_frequency', 'payment_reliability'
            )
        }),
        ('Timestamps', {
            'fields': ('last_payment_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CommunicationInsight)
class CommunicationInsightAdmin(admin.ModelAdmin):
    """Admin for CommunicationInsight model"""
    
    list_display = [
        'customer', 'total_communications', 'satisfaction_rating', 
        'preferred_channel', 'response_rate'
    ]
    list_filter = ['preferred_channel', 'communication_frequency', 'created_at']
    search_fields = ['customer__customer_code', 'customer__first_name', 'customer__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
        }),
        ('Communication Statistics', {
            'fields': (
                'total_communications', 'avg_response_time', 'satisfaction_rating',
                'response_rate', 'escalation_count'
            )
        }),
        ('Communication Patterns', {
            'fields': (
                'preferred_channel', 'communication_frequency', 'channel_breakdown'
            )
        }),
        ('Timestamps', {
            'fields': ('last_contact_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ClaimsInsight)
class ClaimsInsightAdmin(admin.ModelAdmin):
    """Admin for ClaimsInsight model"""
    
    list_display = [
        'customer', 'total_claims', 'approval_rate', 'risk_level', 
        'avg_processing_time'
    ]
    list_filter = ['risk_level', 'created_at']
    search_fields = ['customer__customer_code', 'customer__first_name', 'customer__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
        }),
        ('Claims Statistics', {
            'fields': (
                'total_claims', 'approved_amount', 'total_claimed_amount',
                'avg_processing_time', 'approval_rate'
            )
        }),
        ('Claims Analysis', {
            'fields': (
                'claims_by_type', 'claims_by_status', 'risk_level', 'claim_frequency'
            )
        }),
        ('Timestamps', {
            'fields': ('last_claim_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CustomerProfileInsight)
class CustomerProfileInsightAdmin(admin.ModelAdmin):
    """Admin for CustomerProfileInsight model"""
    
    list_display = [
        'customer', 'active_policies', 'customer_segment', 
        'engagement_level', 'overall_risk_score'
    ]
    list_filter = ['customer_segment', 'engagement_level', 'created_at']
    search_fields = ['customer__customer_code', 'customer__first_name', 'customer__last_name']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Customer', {
            'fields': ('customer',)
        }),
        ('Policy Information', {
            'fields': (
                'active_policies', 'family_policies', 'expired_lapsed_policies',
                'policy_portfolio'
            )
        }),
        ('Customer Value', {
            'fields': (
                'customer_lifetime_value', 'total_paid_ytd'
            )
        }),
        ('Customer Analysis', {
            'fields': (
                'customer_segment', 'engagement_level', 'overall_risk_score'
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

from django.contrib import admin
from .models import CustomerInstallment


@admin.register(CustomerInstallment)
class CustomerInstallmentAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'customer', 'renewal_case', 'period', 'amount', 
        'due_date', 'status', 'payment', 'created_at'
    ]
    list_filter = [
        'status', 'due_date', 'created_at', 'updated_at'
    ]
    search_fields = [
        'customer__first_name', 'customer__last_name', 'customer__customer_code',
        'renewal_case__case_number', 'period', 'payment__transaction_id'
    ]
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-due_date', '-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('customer', 'renewal_case', 'period', 'amount', 'due_date', 'status')
        }),
        ('Payment Information', {
            'fields': ('payment',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('payment', 'customer', 'renewal_case')

"""
URL configuration for Customer Family Medical History app.
"""

from django.urls import path
from . import views

app_name = 'customer_family_medical_history'

urlpatterns = [
    # List and create customer family medical history
    path(
        '',
        views.CustomerFamilyMedicalHistoryListCreateView.as_view(),
        name='customer-family-medical-history-list-create'
    ),
    
    # Detail view for customer family medical history (retrieve, update, delete)
    path(
        '<int:pk>/',
        views.CustomerFamilyMedicalHistoryDetailView.as_view(),
        name='customer-family-medical-history-detail'
    ),
    
    # Get medical history by customer ID
    path(
        'customer/<int:customer_id>/',
        views.customer_medical_history_by_customer,
        name='customer-medical-history-by-customer'
    ),
    
    # Get risk assessment by customer ID
    path(
        'risk-assessment/<int:customer_id>/',
        views.customer_medical_history_risk_assessment,
        name='customer-medical-history-risk-assessment'
    ),
    
    # Statistics
    path(
        'statistics/',
        views.medical_history_statistics,
        name='medical-history-statistics'
    ),
    
    # Summary for analytics
    path(
        'summary/',
        views.medical_history_summary,
        name='medical-history-summary'
    ),
]

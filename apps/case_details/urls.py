from django.urls import path
from .views import CombinedPolicyDataAPIView
from .views import CustomerCommunicationPreferencesAPIView
from .views import CustomerPreferencesSummaryAPIView

urlpatterns = [
    path('combined-policy-data/', CombinedPolicyDataAPIView.as_view(), name='combined_policy_data'),
    path('combined-policy-data/<int:case_id>/', CombinedPolicyDataAPIView.as_view(), name='combined_policy_data_with_id'),
    path('combined-policy-data/<str:case_number>/', CombinedPolicyDataAPIView.as_view(), name='combined_policy_data_by_number'),
    path("customer-communication-preferences/<int:case_number>/",CustomerCommunicationPreferencesAPIView.as_view(),name="customer_communication_preferences"),
    path('preferences-summary/<int:case_id>/', CustomerPreferencesSummaryAPIView.as_view(), name='preferences_summary'),
    path('preferences-summary/<str:case_ref>/', CustomerPreferencesSummaryAPIView.as_view(), name='preferences_summary_by_ref'),
    
]
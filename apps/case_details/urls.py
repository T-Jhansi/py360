from django.urls import path
from .views import CombinedPolicyDataAPIView

urlpatterns = [
    path('combined-policy-data/', CombinedPolicyDataAPIView.as_view(), name='combined_policy_data'),
    path('combined-policy-data/<int:case_id>/', CombinedPolicyDataAPIView.as_view(), name='combined_policy_data_with_id'),
]
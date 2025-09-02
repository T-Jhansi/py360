from django.urls import path
from .views import (
    search_case_logs_by_case_number_api, search_case_logs_by_policy_number_api
)
from apps.case_tracking.views import update_case_log_api

app_name = 'case_logs'

urlpatterns = [
    path('search/case-number/', search_case_logs_by_case_number_api, name='search-case-logs-by-case-number'),
    path('search/policy-number/', search_case_logs_by_policy_number_api, name='search-case-logs-by-policy-number'),
    path('update-case-log/<int:case_log_id>/', update_case_log_api, name='update-case-log'),
]

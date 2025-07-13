from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    PolicyTypeViewSet, PolicyViewSet, PolicyRenewalViewSet, PolicyClaimViewSet,
    PolicyDocumentViewSet, PolicyBeneficiaryViewSet, PolicyPaymentViewSet, PolicyNoteViewSet
)

router = DefaultRouter()
router.register(r'types', PolicyTypeViewSet, basename='policytype')
router.register(r'policies', PolicyViewSet, basename='policy')
router.register(r'renewals', PolicyRenewalViewSet, basename='policyrenewal')
router.register(r'claims', PolicyClaimViewSet, basename='policyclaim')
router.register(r'documents', PolicyDocumentViewSet, basename='policydocument')
router.register(r'beneficiaries', PolicyBeneficiaryViewSet, basename='policybeneficiary')
router.register(r'payments', PolicyPaymentViewSet, basename='policypayment')
router.register(r'notes', PolicyNoteViewSet, basename='policynote')



urlpatterns = [
    path('', include(router.urls)),

] 

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    EmailTemplateViewSet,
    EmailTemplateCategoryViewSet,
    EmailTemplateTagViewSet,
    EmailTemplateVersionViewSet
)

router = DefaultRouter()
router.register(r'templates', EmailTemplateViewSet, basename='email-template')
router.register(r'categories', EmailTemplateCategoryViewSet, basename='email-template-category')
router.register(r'tags', EmailTemplateTagViewSet, basename='email-template-tag')
router.register(r'versions', EmailTemplateVersionViewSet, basename='email-template-version')

urlpatterns = [
    path('', include(router.urls)),
]
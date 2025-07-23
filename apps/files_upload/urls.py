from rest_framework.routers import DefaultRouter
from .views import FileUploadViewSet

router = DefaultRouter()
router.register(r'file-uploads', FileUploadViewSet, basename='fileupload')

urlpatterns = router.urls

from rest_framework import viewsets
from .models import FileUpload
from .serializers import FileUploadSerializer
from rest_framework.permissions import IsAuthenticated

class FileUploadViewSet(viewsets.ModelViewSet):
    queryset = FileUpload.objects.all()
    serializer_class = FileUploadSerializer
    permission_classes = [IsAuthenticated]

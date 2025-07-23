from rest_framework import serializers
from .models import FileUpload
import os

class FileUploadSerializer(serializers.ModelSerializer):
    file = serializers.FileField(write_only=True)

    class Meta:
        model = FileUpload
        fields = ['file', 'filename', 'original_filename', 'file_size', 'file_type', 'upload_status']
        read_only_fields = ['file_name', 'original_filename', 'file_size', 'file_type', 'upload_status']

    def create(self, validated_data):
        uploaded_file = validated_data.pop('file')

        upload_path = f"uploads/{uploaded_file.name}"
        with open(upload_path, 'wb+') as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        file_instance = FileUpload.objects.create(
            file_name=uploaded_file.name,
            original_filename=uploaded_file.name,
            file_size=uploaded_file.size,
            file_type=os.path.splitext(uploaded_file.name)[1],
            upload_path=upload_path,
            uploaded_by_id=self.context['request'].user,
            **validated_data
        )

        return file_instance

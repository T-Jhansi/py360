from rest_framework import serializers
from .models import CustomerDocument
from apps.customers.models import Customer
from apps.customers_files.models import CustomerFile


class CustomerDocumentSerializer(serializers.ModelSerializer):
    """Serializer for CustomerDocument model"""

    # Accept both customer_id/file_id and customer/file for flexibility
    customer_id = serializers.IntegerField(write_only=True, required=False)
    file_id = serializers.IntegerField(write_only=True, required=False)

    # Read-only fields for display
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_code = serializers.CharField(source='customer.customer_code', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status = serializers.CharField(read_only=True)
    expiry_status = serializers.CharField(read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)

    # User information
    created_by_name = serializers.CharField(source='created_by.username', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.username', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True)

    # File information
    file_name = serializers.CharField(source='file.file_name', read_only=True)
    file_size = serializers.IntegerField(source='file.file_size', read_only=True)
    file_type = serializers.CharField(source='file.file_type', read_only=True)

    class Meta:
        model = CustomerDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'document_number',
            'is_verified', 'verified_at', 'verification_notes', 'verification_status',
            'issue_date', 'expiry_date', 'expiry_status', 'is_expired', 'is_expiring_soon',
            'issuing_authority', 'notes', 'customer', 'customer_name', 'customer_code',
            'file', 'file_name', 'file_size', 'file_type', 'verified_by', 'verified_by_name',
            'created_at', 'updated_at', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'is_deleted', 'deleted_at',
            'customer_id', 'file_id'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'verified_at', 'is_deleted', 'deleted_at'
        ]
    
    def validate_customer(self, value):
        """Validate that customer exists and is active"""
        if value.is_deleted:
            raise serializers.ValidationError("Cannot create document for deleted customer.")
        return value

    def validate_file(self, value):
        """Validate that file exists and is active"""
        if not value.is_active:
            raise serializers.ValidationError("File must be active before creating document.")
        return value

    def validate_customer_id(self, value):
        """Validate that customer exists and is active"""
        try:
            customer = Customer.objects.get(id=value)
            if customer.is_deleted:
                raise serializers.ValidationError("Cannot create document for deleted customer.")
            return value
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer with this ID does not exist.")

    def validate_file_id(self, value):
        """Validate that file exists and is active"""
        try:
            file_obj = CustomerFile.objects.get(id=value)
            if not file_obj.is_active:
                raise serializers.ValidationError("File must be active before creating document.")
            return value
        except CustomerFile.DoesNotExist:
            raise serializers.ValidationError("File with this ID does not exist.")

    def validate_expiry_date(self, value):
        """Validate expiry date is not in the past"""
        if value and self.instance is None:  
            from django.utils import timezone
            if value < timezone.now().date():
                raise serializers.ValidationError("Expiry date cannot be in the past.")
        return value

    def validate(self, attrs):
        """Cross-field validation"""
        issue_date = attrs.get('issue_date')
        expiry_date = attrs.get('expiry_date')

        if issue_date and expiry_date:
            if issue_date >= expiry_date:
                raise serializers.ValidationError({
                    'expiry_date': 'Expiry date must be after issue date.'
                })

        customer_id = attrs.get('customer_id')
        file_id = attrs.get('file_id')
        customer = attrs.get('customer')
        file_obj = attrs.get('file')

        if customer_id and customer:
            raise serializers.ValidationError("Provide either 'customer_id' or 'customer', not both.")
        if not customer_id and not customer:
            raise serializers.ValidationError("Either 'customer_id' or 'customer' is required.")

        if file_id and file_obj:
            raise serializers.ValidationError("Provide either 'file_id' or 'file', not both.")
        if not file_id and not file_obj:
            raise serializers.ValidationError("Either 'file_id' or 'file' is required.")

        return attrs

    def create(self, validated_data):
        """Create document with customer and file objects"""
        customer_id = validated_data.pop('customer_id', None)
        file_id = validated_data.pop('file_id', None)

        if customer_id:
            customer = Customer.objects.get(id=customer_id)
            validated_data['customer'] = customer

        if file_id:
            file_obj = CustomerFile.objects.get(id=file_id)
            validated_data['file'] = file_obj

        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Update document with customer and file objects"""
        customer_id = validated_data.pop('customer_id', None)
        file_id = validated_data.pop('file_id', None)

        if customer_id:
            customer = Customer.objects.get(id=customer_id)
            validated_data['customer'] = customer

        if file_id:
            file_obj = CustomerFile.objects.get(id=file_id)
            validated_data['file'] = file_obj

        return super().update(instance, validated_data)


class CustomerDocumentListSerializer(serializers.ModelSerializer):
    """Simplified serializer for listing customer documents"""
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_code = serializers.CharField(source='customer.customer_code', read_only=True)
    document_type_display = serializers.CharField(source='get_document_type_display', read_only=True)
    verification_status = serializers.CharField(read_only=True)
    expiry_status = serializers.CharField(read_only=True)
    file_name = serializers.CharField(source='file.file_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.username', read_only=True)
    
    class Meta:
        model = CustomerDocument
        fields = [
            'id', 'document_type', 'document_type_display', 'document_number',
            'is_verified', 'verification_status', 'expiry_date', 'expiry_status',
            'customer', 'customer_name', 'customer_code', 'file_name',
            'verified_by_name', 'created_at', 'updated_at'
        ]


class CustomerDocumentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating customer documents"""

    customer_id = serializers.IntegerField(write_only=True)
    file_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = CustomerDocument
        fields = [
            'document_type', 'document_number', 'issue_date', 'expiry_date',
            'issuing_authority', 'notes', 'customer_id', 'file_id'
        ]

    def validate_customer_id(self, value):
        """Validate that customer exists and is active"""
        try:
            customer = Customer.objects.get(id=value)
            if customer.is_deleted:
                raise serializers.ValidationError("Cannot create document for deleted customer.")
            return value
        except Customer.DoesNotExist:
            raise serializers.ValidationError("Customer with this ID does not exist.")

    def validate_file_id(self, value):
        """Validate that file exists and is active"""
        try:
            file_obj = CustomerFile.objects.get(id=value)
            if not file_obj.is_active:
                raise serializers.ValidationError("File must be active before creating document.")
            return value
        except CustomerFile.DoesNotExist:
            raise serializers.ValidationError("File with this ID does not exist.")

    def create(self, validated_data):
        """Create document with customer and file objects"""
        customer_id = validated_data.pop('customer_id')
        file_id = validated_data.pop('file_id')

        customer = Customer.objects.get(id=customer_id)
        file_obj = CustomerFile.objects.get(id=file_id)

        validated_data['customer'] = customer
        validated_data['file'] = file_obj

        return super().create(validated_data)

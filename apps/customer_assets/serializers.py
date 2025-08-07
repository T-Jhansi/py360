from rest_framework import serializers
from .models import CustomerAssets
from apps.customers.models import Customer


class CustomerAssetsSerializer(serializers.ModelSerializer):
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_code = serializers.CharField(source='customer.customer_code', read_only=True)
    residence_summary = serializers.CharField(read_only=True)
    asset_score = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CustomerAssets
        fields = [
            'id',
            'customer',
            'customer_name',
            'customer_code',
            'residence_type',
            'residence_status',
            'residence_location',
            'residence_rating',
            'residence_summary',
            'asset_score',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class CustomerAssetsCreateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CustomerAssets
        fields = [
            'customer',
            'residence_type',
            'residence_status',
            'residence_location',
            'residence_rating',
        ]


class CustomerAssetsUpdateSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = CustomerAssets
        fields = [
            'residence_type',
            'residence_status',
            'residence_location',
            'residence_rating',
        ]


class CustomerAssetsListSerializer(serializers.ModelSerializer):
    
    customer_name = serializers.CharField(source='customer.full_name', read_only=True)
    customer_code = serializers.CharField(source='customer.customer_code', read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    residence_summary = serializers.CharField(read_only=True)
    asset_score = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = CustomerAssets
        fields = [
            'id',
            'customer',
            'customer_name',
            'customer_code',
            'customer_email',
            'residence_type',
            'residence_status',
            'residence_location',
            'residence_rating',
            'residence_summary',
            'asset_score',
            'created_at',
        ]

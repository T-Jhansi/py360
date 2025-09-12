from rest_framework import serializers
from .models import Offer


class OfferSerializer(serializers.ModelSerializer):
    """Serializer for Offer model - used for listing and retrieving offers"""
    
    offer_type_display = serializers.CharField(source='get_offer_type_display', read_only=True)
    currency_display = serializers.CharField(source='get_currency_display', read_only=True)
    is_currently_active = serializers.ReadOnlyField()
    formatted_amount = serializers.ReadOnlyField()
    formatted_interest_rate = serializers.ReadOnlyField()
    
    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'description', 'offer_type', 'offer_type_display',
            'amount', 'discount', 'currency', 'currency_display', 'interest_rate',
            'features', 'extra_info', 'is_active', 'is_currently_active',
            'display_order', 'icon', 'color_scheme', 'terms_and_conditions',
            'start_date', 'end_date', 'formatted_amount', 'formatted_interest_rate',
            'created_at', 'updated_at', 'created_by', 'updated_by'
        ]
        read_only_fields = [
            'id', 'offer_type_display', 'currency_display', 'is_currently_active',
            'formatted_amount', 'formatted_interest_rate', 'created_at', 'updated_at',
            'created_by', 'updated_by'
        ]


class OfferCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new offers"""
    
    class Meta:
        model = Offer
        fields = [
            'title', 'description', 'offer_type', 'amount', 'discount', 'currency',
            'interest_rate', 'features', 'extra_info', 'is_active', 'display_order',
            'icon', 'color_scheme', 'terms_and_conditions', 'start_date', 'end_date'
        ]
    
    def validate(self, data):
        """Validate offer data"""
        # Validate that amount is provided for payment options
        if data.get('offer_type') == 'payment_option' and not data.get('amount'):
            raise serializers.ValidationError({
                'amount': 'Amount is required for payment option offers'
            })
        
        # Validate that interest_rate is provided for funding options
        if data.get('offer_type') == 'funding' and not data.get('interest_rate'):
            raise serializers.ValidationError({
                'interest_rate': 'Interest rate is required for funding offers'
            })
        
        # Validate date range
        start_date = data.get('start_date')
        end_date = data.get('end_date')
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        return data


class OfferUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating offers"""
    
    class Meta:
        model = Offer
        fields = [
            'title', 'description', 'offer_type', 'amount', 'discount', 'currency',
            'interest_rate', 'features', 'extra_info', 'is_active', 'display_order',
            'icon', 'color_scheme', 'terms_and_conditions', 'start_date', 'end_date'
        ]
    
    def validate(self, data):
        """Validate offer data for updates"""
        # Get the instance being updated
        instance = self.instance
        
        # Validate that amount is provided for payment options
        offer_type = data.get('offer_type', instance.offer_type if instance else None)
        amount = data.get('amount', instance.amount if instance else None)
        
        if offer_type == 'payment_option' and not amount:
            raise serializers.ValidationError({
                'amount': 'Amount is required for payment option offers'
            })
        
        # Validate that interest_rate is provided for funding options
        interest_rate = data.get('interest_rate', instance.interest_rate if instance else None)
        
        if offer_type == 'funding' and not interest_rate:
            raise serializers.ValidationError({
                'interest_rate': 'Interest rate is required for funding offers'
            })
        
        # Validate date range
        start_date = data.get('start_date', instance.start_date if instance else None)
        end_date = data.get('end_date', instance.end_date if instance else None)
        
        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError({
                'end_date': 'End date must be after start date'
            })
        
        return data

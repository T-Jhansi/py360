from rest_framework import serializers


class DashboardSummarySerializer(serializers.Serializer):
    """Serializer for dashboard summary data"""
    total_cases = serializers.IntegerField()
    in_progress = serializers.IntegerField()
    renewed = serializers.IntegerField()
    pending_action = serializers.IntegerField()
    failed = serializers.IntegerField()
    renewal_amount_total = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_collected = serializers.DecimalField(max_digits=12, decimal_places=2)
    payment_pending = serializers.DecimalField(max_digits=12, decimal_places=2)

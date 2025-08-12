from rest_framework import serializers
from apps.customers.models import Customer
from apps.customers_documents.models import CustomerDocument
from apps.policies.models import Policy, PolicyType
from apps.customer_financial_profile.models import CustomerFinancialProfile
from apps.channels.models import Channel
from apps.policy_features.models import PolicyFeature
from apps.policy_coverages.models import PolicyCoverage
from apps.policy_additional_benefits.models import PolicyAdditionalBenefit
from apps.policy_exclusions.models import PolicyExclusion


class CustomerDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerDocument
        fields = '__all__'


class CustomerFinancialProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerFinancialProfile
        fields = '__all__'


class PolicyCoverageSerializer(serializers.ModelSerializer):
    additional_benefits = serializers.SerializerMethodField()

    class Meta:
        model = PolicyCoverage
        fields = '__all__'

    def get_additional_benefits(self, obj):
        # Get additional benefits for this coverage
        benefits = PolicyAdditionalBenefit.objects.filter(policy_coverages=obj)
        return PolicyAdditionalBenefitSerializer(benefits, many=True).data


class PolicyAdditionalBenefitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyAdditionalBenefit
        fields = '__all__'


class PolicyFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyFeature
        fields = '__all__'


class PolicyExclusionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyExclusion
        fields = '__all__'


class PolicyTypeSerializer(serializers.ModelSerializer):
    policy_features = PolicyFeatureSerializer(many=True, read_only=True)
    policy_coverages = PolicyCoverageSerializer(many=True, read_only=True)

    class Meta:
        model = PolicyType
        fields = '__all__'


class ChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Channel
        fields = '__all__'


class PolicySerializer(serializers.ModelSerializer):
    policy_type = PolicyTypeSerializer(read_only=True)
    exclusions = PolicyExclusionSerializer(many=True, read_only=True)

    class Meta:
        model = Policy
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    documents = CustomerDocumentSerializer(many=True, read_only=True, source='documents_new')
    financial_profile = CustomerFinancialProfileSerializer(read_only=True)
    channels = ChannelSerializer(many=True, read_only=True)
    policies = PolicySerializer(many=True, read_only=True)

    class Meta:
        model = Customer
        fields = '__all__'


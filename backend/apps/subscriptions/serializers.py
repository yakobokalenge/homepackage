from rest_framework import serializers
from .models import SubscriptionPlan, Subscription

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = '__all__'

class SubscriptionSerializer(serializers.ModelSerializer):
    plan_detail = PlanSerializer(source='plan', read_only=True)
    class Meta:
        model = Subscription
        fields = '__all__'
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')

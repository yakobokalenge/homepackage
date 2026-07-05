from rest_framework import serializers
from .models import Transaction, WebhookEvent


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = '__all__'
        read_only_fields = ('id', 'user', 'status', 'gateway_transaction_id', 'gateway_reference',
                          'gateway_response', 'initiated_at', 'completed_at', 'refunded_at')


class InitiatePaymentSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField()
    payment_method = serializers.ChoiceField(choices=Transaction.PaymentMethod.choices)
    phone_number = serializers.CharField(max_length=20, required=False, default='')
    gateway = serializers.ChoiceField(choices=Transaction.Gateway.choices, default='flutterwave')


class TransactionListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = ('id', 'amount', 'currency', 'payment_method', 'status', 'description', 'initiated_at', 'completed_at')

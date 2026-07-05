import uuid
from rest_framework import status as http_status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings
from .models import Transaction, WebhookEvent
from .serializers import InitiatePaymentSerializer, TransactionSerializer, TransactionListSerializer
from .gateways.factory import PaymentGatewayFactory
from .gateways.base import PaymentRequest
from apps.subscriptions.models import SubscriptionPlan, Subscription
from decimal import Decimal


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def initiate_payment(request):
    """Initiate a payment for a subscription plan."""
    serializer = InitiatePaymentSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    try:
        plan = SubscriptionPlan.objects.get(id=data['plan_id'], is_active=True)
    except SubscriptionPlan.DoesNotExist:
        return Response({'error': 'Plan not found'}, status=http_status.HTTP_404_NOT_FOUND)

    idempotency_key = f"hp_{uuid.uuid4().hex[:16]}"
    gateway_name = data.get('gateway', 'flutterwave')
    callback_url = f"{settings.PAYMENT_CALLBACK_BASE_URL}/api/v1/webhooks/{gateway_name}/"

    transaction = Transaction.objects.create(
        user=request.user,
        amount=plan.price_tzs,
        currency='TZS',
        payment_method=data['payment_method'],
        payment_gateway=gateway_name,
        phone_number=data.get('phone_number', ''),
        description=f"Subscription: {plan.name} ({plan.get_billing_cycle_display()})",
        idempotency_key=idempotency_key,
        ip_address=request.META.get('REMOTE_ADDR'),
    )

    gateway = PaymentGatewayFactory.get_gateway(gateway_name)
    pay_request = PaymentRequest(
        amount=plan.price_tzs,
        currency='TZS',
        phone_number=data.get('phone_number', ''),
        email=request.user.email or '',
        payment_method=data['payment_method'],
        description=transaction.description,
        callback_url=callback_url,
        redirect_url=f"{settings.CORS_ALLOWED_ORIGINS[0] if settings.CORS_ALLOWED_ORIGINS else ''}/billing?status=success",
        idempotency_key=idempotency_key,
        metadata={'user_id': str(request.user.id), 'plan_id': str(plan.id), 'transaction_id': str(transaction.id)},
    )

    response = gateway.initiate_payment(pay_request)

    if response.success:
        transaction.gateway_transaction_id = response.transaction_id
        transaction.gateway_reference = response.gateway_reference
        transaction.status = Transaction.Status.PROCESSING
        transaction.gateway_response = response.raw_response
        transaction.save()
        return Response({
            'transaction_id': str(transaction.id),
            'status': 'processing',
            'message': response.message,
            'redirect_url': response.redirect_url,
        })
    else:
        transaction.status = Transaction.Status.FAILED
        transaction.failure_reason = response.message
        transaction.gateway_response = response.raw_response
        transaction.save()
        return Response({'error': response.message}, status=http_status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_payment(request, transaction_id):
    """Verify the status of a payment."""
    try:
        transaction = Transaction.objects.get(id=transaction_id, user=request.user)
    except Transaction.DoesNotExist:
        return Response({'error': 'Transaction not found'}, status=http_status.HTTP_404_NOT_FOUND)

    if transaction.status in (Transaction.Status.SUCCESSFUL, Transaction.Status.REFUNDED):
        return Response(TransactionSerializer(transaction).data)

    gateway = PaymentGatewayFactory.get_gateway(transaction.payment_gateway)
    result = gateway.verify_payment(transaction.gateway_transaction_id)

    if result.success:
        transaction.status = Transaction.Status.SUCCESSFUL
        transaction.completed_at = timezone.now()
        transaction.save()
        _activate_subscription(transaction)
    elif result.status == 'failed':
        transaction.status = Transaction.Status.FAILED
        transaction.failure_reason = result.message
        transaction.save()

    return Response(TransactionSerializer(transaction).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_history(request):
    """Get user's payment history."""
    transactions = Transaction.objects.filter(user=request.user)
    return Response(TransactionListSerializer(transactions, many=True).data)


def _activate_subscription(transaction):
    """Activate subscription after successful payment."""
    meta = transaction.gateway_response.get('meta', {}) or {}
    plan_id = meta.get('plan_id')
    if not plan_id:
        return
    try:
        plan = SubscriptionPlan.objects.get(id=plan_id)
    except SubscriptionPlan.DoesNotExist:
        return

    from datetime import timedelta
    duration_map = {'weekly': timedelta(weeks=1), 'monthly': timedelta(days=30), 'yearly': timedelta(days=365)}
    duration = duration_map.get(plan.billing_cycle, timedelta(days=30))
    now = timezone.now()

    sub, _ = Subscription.objects.update_or_create(
        user=transaction.user,
        defaults={
            'plan': plan,
            'status': Subscription.Status.ACTIVE,
            'current_period_start': now,
            'current_period_end': now + duration,
            'payment_gateway': transaction.payment_gateway,
        }
    )
    transaction.subscription = sub
    transaction.save()

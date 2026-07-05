"""Webhook handlers for payment gateways."""
import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone
from .models import Transaction, WebhookEvent
from .gateways.factory import PaymentGatewayFactory


@api_view(['POST'])
@permission_classes([AllowAny])
def flutterwave_webhook(request):
    return _process_webhook(request, 'flutterwave')


@api_view(['POST'])
@permission_classes([AllowAny])
def clickpesa_webhook(request):
    return _process_webhook(request, 'clickpesa')


@api_view(['POST'])
@permission_classes([AllowAny])
def azampay_webhook(request):
    return _process_webhook(request, 'azampay')


def _process_webhook(request, gateway_name):
    """Generic webhook processor."""
    payload = request.data if isinstance(request.data, dict) else json.loads(request.body)
    headers = {k: v for k, v in request.META.items() if k.startswith('HTTP_')}

    event = WebhookEvent.objects.create(
        gateway=gateway_name,
        event_type=payload.get('event', payload.get('event_type', 'unknown')),
        payload=payload,
        headers=headers,
        signature=headers.get('HTTP_VERIF_HASH', headers.get('HTTP_X_AZAMPAY_SIGNATURE', '')),
    )

    try:
        gateway = PaymentGatewayFactory.get_gateway(gateway_name)
        if not gateway.verify_webhook(payload, headers):
            event.processing_error = 'Signature verification failed'
            event.save()
            return Response({'status': 'error'}, status=400)

        event.is_verified = True

        # Extract transaction reference
        tx_ref = (payload.get('data', {}).get('tx_ref') or
                  payload.get('order_reference') or
                  payload.get('externalId', ''))

        if tx_ref:
            try:
                transaction = Transaction.objects.get(idempotency_key=tx_ref)
                tx_status = (payload.get('data', {}).get('status') or
                            payload.get('status', '')).lower()

                if tx_status in ('successful', 'completed', 'success'):
                    transaction.status = Transaction.Status.SUCCESSFUL
                    transaction.completed_at = timezone.now()
                    transaction.gateway_response = payload
                    transaction.save()
                    # Activate subscription
                    from .views import _activate_subscription
                    _activate_subscription(transaction)
                elif tx_status in ('failed', 'error'):
                    transaction.status = Transaction.Status.FAILED
                    transaction.failure_reason = payload.get('message', 'Payment failed')
                    transaction.save()
            except Transaction.DoesNotExist:
                event.processing_error = f'Transaction not found: {tx_ref}'

        event.is_processed = True
        event.processed_at = timezone.now()
        event.save()
        return Response({'status': 'ok'})
    except Exception as e:
        event.processing_error = str(e)
        event.save()
        return Response({'status': 'error'}, status=500)

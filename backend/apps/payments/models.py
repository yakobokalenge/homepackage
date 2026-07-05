"""Payment models: Transaction, WebhookEvent."""
import uuid
from django.db import models
from django.conf import settings


class Transaction(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        SUCCESSFUL = 'successful', 'Successful'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentMethod(models.TextChoices):
        MPESA = 'mpesa', 'M-Pesa (Vodacom)'
        TIGO_PESA = 'tigo_pesa', 'Tigo Pesa'
        AIRTEL_MONEY = 'airtel_money', 'Airtel Money'
        HALO_PESA = 'halo_pesa', 'HaloPesa'
        VISA = 'visa', 'Visa'
        MASTERCARD = 'mastercard', 'Mastercard'
        BANK_TRANSFER = 'bank_transfer', 'Bank Transfer'

    class Gateway(models.TextChoices):
        FLUTTERWAVE = 'flutterwave', 'Flutterwave'
        CLICKPESA = 'clickpesa', 'ClickPesa'
        AZAMPAY = 'azampay', 'AzamPay'
        SELCOM = 'selcom', 'Selcom'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    subscription = models.ForeignKey('subscriptions.Subscription', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, default='TZS')
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    payment_gateway = models.CharField(max_length=20, choices=Gateway.choices, default=Gateway.FLUTTERWAVE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    gateway_transaction_id = models.CharField(max_length=200, blank=True, default='')
    gateway_reference = models.CharField(max_length=200, blank=True, default='')
    gateway_response = models.JSONField(default=dict, blank=True)
    phone_number = models.CharField(max_length=20, blank=True, default='')
    network_provider = models.CharField(max_length=30, blank=True, default='')
    description = models.TextField(blank=True, default='')
    receipt_url = models.URLField(blank=True, default='')
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    refund_reason = models.TextField(blank=True, default='')
    failure_reason = models.TextField(blank=True, default='')
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    refunded_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    idempotency_key = models.CharField(max_length=200, unique=True)

    class Meta:
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['gateway_transaction_id']),
        ]

    def __str__(self):
        return f"TXN {self.id} - {self.amount} {self.currency} ({self.get_status_display()})"


class WebhookEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    gateway = models.CharField(max_length=30)
    event_type = models.CharField(max_length=100)
    payload = models.JSONField()
    headers = models.JSONField(default=dict, blank=True)
    signature = models.CharField(max_length=500, blank=True, default='')
    is_verified = models.BooleanField(default=False)
    is_processed = models.BooleanField(default=False)
    processing_error = models.TextField(blank=True, default='')
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-received_at']

    def __str__(self):
        return f"Webhook {self.gateway}: {self.event_type}"

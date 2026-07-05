from django.contrib import admin
from .models import Transaction, WebhookEvent


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'amount', 'currency', 'payment_method', 'payment_gateway', 'status', 'initiated_at')
    list_filter = ('status', 'payment_method', 'payment_gateway', 'currency')
    search_fields = ('user__email', 'gateway_transaction_id', 'idempotency_key')
    readonly_fields = ('id', 'gateway_response')


@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ('gateway', 'event_type', 'is_verified', 'is_processed', 'received_at')
    list_filter = ('gateway', 'is_verified', 'is_processed')
    readonly_fields = ('payload', 'headers')

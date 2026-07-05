from django.urls import path
from . import views, webhooks

urlpatterns = [
    path('initiate/', views.initiate_payment, name='initiate-payment'),
    path('verify/<uuid:transaction_id>/', views.verify_payment, name='verify-payment'),
    path('history/', views.payment_history, name='payment-history'),
    path('webhooks/flutterwave/', webhooks.flutterwave_webhook, name='webhook-flutterwave'),
    path('webhooks/clickpesa/', webhooks.clickpesa_webhook, name='webhook-clickpesa'),
    path('webhooks/azampay/', webhooks.azampay_webhook, name='webhook-azampay'),
]

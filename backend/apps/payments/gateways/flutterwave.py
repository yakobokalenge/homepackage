"""Flutterwave Payment Gateway — Primary gateway for Tanzania."""
import hashlib
import requests
from decimal import Decimal
from django.conf import settings
from .base import PaymentGateway, PaymentRequest, PaymentResponse


class FlutterwaveGateway(PaymentGateway):
    def __init__(self):
        self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
        self.base_url = settings.FLUTTERWAVE_BASE_URL or 'https://api.flutterwave.com'
        self.webhook_hash = getattr(settings, 'FLUTTERWAVE_WEBHOOK_HASH', '')

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.secret_key}', 'Content-Type': 'application/json'}

    def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        # Determine charge type based on payment method
        mobile_methods = {'mpesa', 'tigo_pesa', 'airtel_money', 'halo_pesa'}
        if request.payment_method in mobile_methods:
            return self._charge_mobile_money(request)
        return self._charge_card(request)

    def _charge_mobile_money(self, request: PaymentRequest) -> PaymentResponse:
        payload = {
            'tx_ref': request.idempotency_key,
            'amount': str(request.amount),
            'currency': request.currency,
            'email': request.email or 'noemail@homepackage.co.tz',
            'phone_number': request.phone_number,
            'meta': request.metadata,
            'redirect_url': request.redirect_url,
        }
        try:
            resp = requests.post(
                f'{self.base_url}/v3/charges?type=mobile_money_tanzania',
                json=payload, headers=self.headers, timeout=30
            )
            data = resp.json()
            if data.get('status') == 'success':
                return PaymentResponse(
                    success=True,
                    transaction_id=str(data.get('data', {}).get('id', '')),
                    gateway_reference=data.get('data', {}).get('flw_ref', ''),
                    status='pending',
                    message=data.get('message', 'STK push sent'),
                    raw_response=data,
                )
            return PaymentResponse(success=False, message=data.get('message', 'Failed'), raw_response=data)
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def _charge_card(self, request: PaymentRequest) -> PaymentResponse:
        payload = {
            'tx_ref': request.idempotency_key,
            'amount': str(request.amount),
            'currency': request.currency,
            'redirect_url': request.redirect_url,
            'customer': {'email': request.email},
            'meta': request.metadata,
        }
        try:
            resp = requests.post(f'{self.base_url}/v3/payments', json=payload, headers=self.headers, timeout=30)
            data = resp.json()
            if data.get('status') == 'success':
                return PaymentResponse(
                    success=True,
                    redirect_url=data.get('data', {}).get('link', ''),
                    status='pending',
                    message='Redirect to payment page',
                    raw_response=data,
                )
            return PaymentResponse(success=False, message=data.get('message', 'Failed'), raw_response=data)
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def verify_payment(self, transaction_id: str) -> PaymentResponse:
        try:
            resp = requests.get(f'{self.base_url}/v3/transactions/{transaction_id}/verify', headers=self.headers, timeout=15)
            data = resp.json()
            tx = data.get('data', {})
            success = tx.get('status') == 'successful' and data.get('status') == 'success'
            return PaymentResponse(
                success=success,
                transaction_id=str(tx.get('id', '')),
                gateway_reference=tx.get('flw_ref', ''),
                status=tx.get('status', 'unknown'),
                message=data.get('message', ''),
                raw_response=data,
            )
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def refund_payment(self, transaction_id: str, amount: Decimal) -> PaymentResponse:
        try:
            resp = requests.post(
                f'{self.base_url}/v3/transactions/{transaction_id}/refund',
                json={'amount': str(amount)}, headers=self.headers, timeout=15
            )
            data = resp.json()
            return PaymentResponse(success=data.get('status') == 'success', message=data.get('message', ''), raw_response=data)
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def verify_webhook(self, payload: dict, headers: dict) -> bool:
        incoming_hash = headers.get('verif-hash', '')
        return incoming_hash == self.webhook_hash

    def create_subscription(self, plan_data: dict, customer_data: dict) -> dict:
        payload = {
            'amount': plan_data['amount'],
            'name': plan_data['name'],
            'interval': plan_data.get('interval', 'monthly'),
            'currency': plan_data.get('currency', 'TZS'),
        }
        resp = requests.post(f'{self.base_url}/v3/payment-plans', json=payload, headers=self.headers, timeout=15)
        return resp.json()

    def cancel_subscription(self, subscription_id: str) -> dict:
        resp = requests.put(
            f'{self.base_url}/v3/subscriptions/{subscription_id}/cancel',
            headers=self.headers, timeout=15
        )
        return resp.json()

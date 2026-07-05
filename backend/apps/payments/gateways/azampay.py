"""AzamPay Payment Gateway — Tanzania-focused gateway."""
import requests
from decimal import Decimal
from django.conf import settings
from .base import PaymentGateway, PaymentRequest, PaymentResponse

PROVIDER_MAP = {'mpesa': 'Mpesa', 'tigo_pesa': 'Tigo', 'airtel_money': 'Airtel', 'halo_pesa': 'Halopesa'}


class AzamPayGateway(PaymentGateway):
    def __init__(self):
        self.app_name = settings.AZAMPAY_APP_NAME
        self.client_id = settings.AZAMPAY_CLIENT_ID
        self.client_secret = settings.AZAMPAY_CLIENT_SECRET
        self.api_key = settings.AZAMPAY_API_KEY
        self.base_url = settings.AZAMPAY_BASE_URL or 'https://checkout.azampay.co.tz'
        self.auth_url = settings.AZAMPAY_AUTH_URL or 'https://authenticator.azampay.co.tz'
        self._token = None

    def _get_token(self):
        if self._token:
            return self._token
        resp = requests.post(
            f'{self.auth_url}/AppRegistration/GenerateToken',
            json={'appName': self.app_name, 'clientId': self.client_id, 'clientSecret': self.client_secret},
            timeout=10
        )
        data = resp.json()
        self._token = data.get('data', {}).get('accessToken', '')
        return self._token

    @property
    def headers(self):
        return {
            'Authorization': f'Bearer {self._get_token()}',
            'X-API-KEY': self.api_key,
            'Content-Type': 'application/json',
        }

    def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        provider = PROVIDER_MAP.get(request.payment_method, 'Mpesa')
        payload = {
            'accountNumber': request.phone_number,
            'amount': str(request.amount),
            'currency': request.currency,
            'externalId': request.idempotency_key,
            'provider': provider,
        }
        try:
            resp = requests.post(f'{self.base_url}/azampay/mno/checkout', json=payload, headers=self.headers, timeout=30)
            data = resp.json()
            return PaymentResponse(
                success=resp.status_code in (200, 201),
                transaction_id=data.get('transactionId', ''),
                gateway_reference=request.idempotency_key,
                status='pending',
                message=data.get('message', 'Payment initiated'),
                raw_response=data,
            )
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def verify_payment(self, transaction_id: str) -> PaymentResponse:
        try:
            resp = requests.get(f'{self.base_url}/azampay/transactions/{transaction_id}', headers=self.headers, timeout=15)
            data = resp.json()
            return PaymentResponse(
                success=data.get('status') == 'completed',
                transaction_id=transaction_id,
                status=data.get('status', 'unknown'),
                raw_response=data,
            )
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def refund_payment(self, transaction_id: str, amount: Decimal) -> PaymentResponse:
        return PaymentResponse(success=False, message='Refunds not directly supported via API')

    def verify_webhook(self, payload: dict, headers: dict) -> bool:
        # AzamPay uses x-azampay-signature header
        return bool(headers.get('x-azampay-signature'))

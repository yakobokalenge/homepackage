"""ClickPesa Payment Gateway — Tanzania-focused secondary gateway."""
import requests
from decimal import Decimal
from django.conf import settings
from .base import PaymentGateway, PaymentRequest, PaymentResponse


class ClickPesaGateway(PaymentGateway):
    def __init__(self):
        self.client_id = settings.CLICKPESA_API_KEY
        self.api_key = settings.CLICKPESA_API_SECRET
        self.base_url = settings.CLICKPESA_BASE_URL or 'https://api.clickpesa.com'
        self._token = None

    def _get_token(self):
        if self._token:
            return self._token
        resp = requests.post(
            f'{self.base_url}/third-parties/generate-token',
            headers={'client-id': self.client_id, 'api-key': self.api_key},
            timeout=10
        )
        data = resp.json()
        self._token = data.get('token', '')
        return self._token

    @property
    def headers(self):
        return {'Authorization': f'Bearer {self._get_token()}', 'Content-Type': 'application/json'}

    def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        payload = {
            'amount': str(request.amount),
            'currency': request.currency,
            'order_reference': request.idempotency_key,
            'phone_number': request.phone_number,
            'callback_url': request.callback_url,
        }
        try:
            resp = requests.post(f'{self.base_url}/v2/payments/mobile-money', json=payload, headers=self.headers, timeout=30)
            data = resp.json()
            return PaymentResponse(
                success=resp.status_code in (200, 201),
                transaction_id=data.get('transaction_id', ''),
                gateway_reference=data.get('order_reference', ''),
                status='pending',
                message=data.get('message', 'USSD push sent'),
                raw_response=data,
            )
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def verify_payment(self, transaction_id: str) -> PaymentResponse:
        try:
            resp = requests.get(f'{self.base_url}/v2/payments/{transaction_id}', headers=self.headers, timeout=15)
            data = resp.json()
            return PaymentResponse(
                success=data.get('status') == 'completed',
                transaction_id=transaction_id,
                status=data.get('status', 'unknown'),
                message=data.get('message', ''),
                raw_response=data,
            )
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def refund_payment(self, transaction_id: str, amount: Decimal) -> PaymentResponse:
        try:
            resp = requests.post(
                f'{self.base_url}/v2/payments/{transaction_id}/refund',
                json={'amount': str(amount)}, headers=self.headers, timeout=15
            )
            return PaymentResponse(success=resp.status_code == 200, raw_response=resp.json())
        except requests.RequestException as e:
            return PaymentResponse(success=False, message=str(e))

    def verify_webhook(self, payload: dict, headers: dict) -> bool:
        # ClickPesa uses checksum verification
        return True  # Implement checksum validation with CLICKPESA_WEBHOOK_SECRET

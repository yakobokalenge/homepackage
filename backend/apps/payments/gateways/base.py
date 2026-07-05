"""Payment Gateway Abstraction Layer — Strategy Pattern."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional


@dataclass
class PaymentRequest:
    amount: Decimal
    currency: str = 'TZS'
    phone_number: str = ''
    email: str = ''
    payment_method: str = ''
    description: str = ''
    callback_url: str = ''
    redirect_url: str = ''
    idempotency_key: str = ''
    metadata: dict = field(default_factory=dict)


@dataclass
class PaymentResponse:
    success: bool
    transaction_id: str = ''
    gateway_reference: str = ''
    status: str = ''
    redirect_url: str = ''
    message: str = ''
    raw_response: dict = field(default_factory=dict)


class PaymentGateway(ABC):
    """Abstract base class for all payment gateways."""

    @abstractmethod
    def initiate_payment(self, request: PaymentRequest) -> PaymentResponse:
        """Initiate a payment (mobile money STK push or card redirect)."""

    @abstractmethod
    def verify_payment(self, transaction_id: str) -> PaymentResponse:
        """Verify the status of a payment."""

    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: Decimal) -> PaymentResponse:
        """Refund a completed payment."""

    @abstractmethod
    def verify_webhook(self, payload: dict, headers: dict) -> bool:
        """Verify that a webhook is authentic."""

    def create_subscription(self, plan_data: dict, customer_data: dict) -> dict:
        """Create a recurring subscription (optional)."""
        raise NotImplementedError("Subscriptions not supported by this gateway")

    def cancel_subscription(self, subscription_id: str) -> dict:
        """Cancel a subscription (optional)."""
        raise NotImplementedError("Subscriptions not supported by this gateway")

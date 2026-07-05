"""Payment Gateway Factory — Registry pattern for easy gateway switching."""
from .base import PaymentGateway
from .flutterwave import FlutterwaveGateway
from .clickpesa import ClickPesaGateway
from .azampay import AzamPayGateway

_REGISTRY: dict[str, type[PaymentGateway]] = {
    'flutterwave': FlutterwaveGateway,
    'clickpesa': ClickPesaGateway,
    'azampay': AzamPayGateway,
}


class PaymentGatewayFactory:
    @staticmethod
    def get_gateway(name: str) -> PaymentGateway:
        cls = _REGISTRY.get(name)
        if not cls:
            raise ValueError(f"Unknown payment gateway: {name}. Available: {list(_REGISTRY.keys())}")
        return cls()

    @staticmethod
    def register(name: str, gateway_class: type[PaymentGateway]):
        _REGISTRY[name] = gateway_class

    @staticmethod
    def available_gateways() -> list[str]:
        return list(_REGISTRY.keys())

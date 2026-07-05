"""Subscription models: SubscriptionPlan, Subscription."""
import uuid
from django.db import models
from django.conf import settings


class SubscriptionPlan(models.Model):
    class Tier(models.TextChoices):
        BASIC = 'basic', 'Basic'
        PREMIUM = 'premium', 'Premium'
        INSTITUTIONAL = 'institutional', 'Institutional'

    class BillingCycle(models.TextChoices):
        WEEKLY = 'weekly', 'Weekly'
        MONTHLY = 'monthly', 'Monthly'
        YEARLY = 'yearly', 'Yearly'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    tier = models.CharField(max_length=20, choices=Tier.choices)
    billing_cycle = models.CharField(max_length=10, choices=BillingCycle.choices)
    price_tzs = models.DecimalField(max_digits=12, decimal_places=2)
    features = models.JSONField(default=list)
    max_assessments = models.IntegerField(default=-1, help_text='-1 = unlimited')
    includes_proctoring = models.BooleanField(default=False)
    includes_analytics = models.BooleanField(default=False)
    includes_sms = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['price_tzs']
        unique_together = ['tier', 'billing_cycle']

    def __str__(self):
        return f"{self.name} ({self.get_billing_cycle_display()}) - TZS {self.price_tzs:,.0f}"


class Subscription(models.Model):
    class Status(models.TextChoices):
        TRIAL = 'trial', 'Trial'
        ACTIVE = 'active', 'Active'
        PAST_DUE = 'past_due', 'Past Due'
        CANCELLED = 'cancelled', 'Cancelled'
        EXPIRED = 'expired', 'Expired'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='subscriptions')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    current_period_start = models.DateTimeField()
    current_period_end = models.DateTimeField()
    cancelled_at = models.DateTimeField(null=True, blank=True)
    payment_gateway = models.CharField(max_length=30, blank=True, default='')
    gateway_subscription_id = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.full_name} - {self.plan.name} ({self.get_status_display()})"

    @property
    def is_active_subscription(self):
        from django.utils import timezone
        return self.status in (self.Status.ACTIVE, self.Status.TRIAL) and self.current_period_end > timezone.now()

from django.contrib import admin
from .models import SubscriptionPlan, Subscription

@admin.register(SubscriptionPlan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'billing_cycle', 'price_tzs', 'is_active')
    list_filter = ('tier', 'billing_cycle', 'is_active')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'status', 'current_period_start', 'current_period_end')
    list_filter = ('status', 'plan__tier')

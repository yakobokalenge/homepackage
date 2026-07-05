from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import SubscriptionPlan, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SubscriptionPlan.objects.filter(is_active=True)
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['tier', 'billing_cycle']


class SubscriptionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SubscriptionSerializer

    def get_queryset(self):
        return Subscription.objects.filter(user=self.request.user).select_related('plan')

    @action(detail=False, methods=['get'])
    def current(self, request):
        try:
            sub = Subscription.objects.select_related('plan').get(user=request.user)
            return Response(SubscriptionSerializer(sub).data)
        except Subscription.DoesNotExist:
            return Response({'status': 'no_subscription'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        sub = self.get_object()
        sub.status = Subscription.Status.CANCELLED
        sub.cancelled_at = timezone.now()
        sub.save()
        return Response({'status': 'cancelled'})

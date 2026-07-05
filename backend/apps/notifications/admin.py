from django.contrib import admin
from .models import Notification

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'notification_type', 'channel', 'is_read', 'sent_at')
    list_filter = ('notification_type', 'channel', 'is_read')
    search_fields = ('title', 'user__email')

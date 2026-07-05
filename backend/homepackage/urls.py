"""
URL configuration for HomePackage project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def api_root(request):
    return JsonResponse({
        "name": "HomePackage API",
        "version": "1.0",
        "status": "healthy",
        "admin": "/admin/",
        "auth": "/api/v1/auth/",
    })

urlpatterns = [
    path('', api_root),
    path('admin/', admin.site.urls),
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/schools/', include('apps.schools.urls')),
    path('api/v1/content/', include('apps.content.urls')),
    path('api/v1/', include('apps.assessments.urls')),
    path('api/v1/proctoring/', include('apps.proctoring.urls')),
    path('api/v1/subscriptions/', include('apps.subscriptions.urls')),
    path('api/v1/payments/', include('apps.payments.urls')),
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    try:
        import debug_toolbar
        urlpatterns += [path('__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass

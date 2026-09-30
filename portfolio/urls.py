# portfolio/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from projects.views import health_check

urlpatterns = [
    # Admin dashboard route
    path('admin/', admin.site.urls),
    
    # Directs all root traffic ('') straight into your projects app
    path('', include('projects.urls')),
    path('health/', health_check, name='health_check'), # For health check
]

# Enables Django to serve media files locally during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

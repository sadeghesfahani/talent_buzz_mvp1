"""
URL configuration for djangoProject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from django.urls import path

def trigger_error(request):
    division_by_zero = 1 / 0

schema_view = get_schema_view(
    openapi.Info(
        title="AI",
        default_version='v1',
        description="AI generative for events",
        terms_of_service="https://www.yourapp.com/terms/",
        contact=openapi.Contact(email="sina@omnitechs.nl"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=([permissions.AllowAny]),
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('user/', include('user.urls')),
    path('honeycomb/', include('honeycomb.urls')),
    path('auth/', include('authentication.urls')),
    path('comunication/', include('communication.urls')),
    path('feedback/', include('feedback.urls')),
    path('task/', include('task.urls')),
    path('ai/', include('ai.urls')),
    # path('helpdesk/', include('helpdesk.urls')),
    path('', include('common.urls')),
    path('profile/', include('user_profile.urls')),
    path('sentry-debug/', trigger_error),
    path('assistant/', include('assistant.urls')),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
]



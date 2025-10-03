"""
URL configuration for sandbox_2 project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import TemplateView


def robots_txt(request):
    return HttpResponse("User-agent: *\nAllow: /\nSitemap: https://www.sustains.co/sitemap.xml", content_type="text/plain")


urlpatterns = [
    # Django admin disabled for security - using custom admin system
    # path("admin/", admin.site.urls),  # DISABLED
    path("robots.txt", robots_txt),
    # Portfolio management routes
    path('', include('portfolio.urls')),
    path('', include('advanced_analytics.urls')),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

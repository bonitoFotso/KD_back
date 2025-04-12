"""
URL configuration for KES_DocGen project.

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
from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('document.urls')),
    path('api/', include('api.routers')),
    path('api/', include('client.urls')),
    path('api/', include('courrier.urls')),
    path('api/', include('offres_app.urls')),
    path('api/', include('affaires_app.urls')),
    path('api/', include('proformas_app.urls')),
    path('api/', include('factures_app.urls')),
    path('api/', include('opportunites_app.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
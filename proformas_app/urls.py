from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProformaViewSet

router = DefaultRouter()
router.register(r'proformas', ProformaViewSet)

app_name = 'proformas_api'

urlpatterns = [
    path('', include(router.urls)),
]
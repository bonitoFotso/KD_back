from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import CourrierViewSet, CourrierHistoryViewSet

router = DefaultRouter()
router.register('courriers', CourrierViewSet)
router.register('historique', CourrierHistoryViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
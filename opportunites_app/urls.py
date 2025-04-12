from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import OpportuniteViewSet, OpportuniteTransitionViewSet

# Création du routeur pour les API REST
router = DefaultRouter()
router.register(r'opportunites', OpportuniteViewSet)
#router.register(r'transitions', OpportuniteTransitionViewSet)

urlpatterns = [
    # Routes API standards
    path('', include(router.urls)),
    
    # Routes supplémentaires au besoin
    # path('api/opportunites/dashboard/', opportunite_dashboard, name='opportunite-dashboard'),
]
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import AffaireViewSet

# Création du routeur pour les vues basées sur ViewSet
router = DefaultRouter()
router.register(r'affaires', AffaireViewSet, basename='affaire')

# Configuration des URLs de l'application
urlpatterns = [
    # Inclusion des routes générées par le routeur
    path('', include(router.urls)),
    
    # Routes spécifiques si nécessaire
    # path('api/dashboard/', dashboard_view, name='dashboard'),
]
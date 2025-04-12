# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    OffreFileUploadView,
    OffreLostView,
    OffreNoteView,
    OffreRelanceProlongationView,
    OffreViewSet,
    OffreInitDataView,
    ClientListView,
    ContactsByClientView,
    EntityListView,
    OffreWonView,
    ProductListView,
    OffreDraftView,
    OffreSubmitView,
    OffreStatusChangeView
)
# Création du routeur pour le viewset
router = DefaultRouter()
router.register(r'offres', OffreViewSet)

# URLs de l'API
urlpatterns = [
    # Endpoints principaux via le routeur
    path('', include(router.urls)),
    
    # Endpoint d'initialisation pour la création d'offre
    path('offress/init_data/', OffreInitDataView.as_view(), name='offre-init-data'),
    
    # Clients et contacts
    path('clients/', ClientListView.as_view(), name='client-list'),
    path('clients/<int:client_id>/contacts/', ContactsByClientView.as_view(), name='client-contacts'),
    
    # Entités
    path('entities/', EntityListView.as_view(), name='entity-list'),
    
    # Produits
    path('products/', ProductListView.as_view(), name='product-list'),
    
    # Actions spécifiques pour les offres
    path('off/offres/draft/', OffreDraftView.as_view(), name='offre-draft'),
    path('off/offres/<int:pk>/envoyer/', OffreSubmitView.as_view(), name='offre-submit'),
    path('off/offres/<int:pk>/change-status/', OffreStatusChangeView.as_view(), name='offre-change-status'),
    path('off/offres/<int:pk>/upload/', OffreFileUploadView.as_view(), name='offre-upload'),
    path('off/offres/<int:pk>/gagner/', OffreWonView.as_view(), name='offre-submit'),
    path('off/offres/<int:pk>/perdre/', OffreLostView.as_view(), name='offre-submit'),
    path('off/offres/<int:pk>/relancer/', OffreLostView.as_view(), name='offre-submit'),
    path('off/offres/<int:pk>/relance/', OffreRelanceProlongationView.as_view(), name='relance-offre'),
    path('off/offres/<int:pk>/notes/', OffreNoteView.as_view(), name='offre-submit'),
    


]
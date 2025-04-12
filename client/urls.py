from rest_framework.routers import DefaultRouter
from django.urls import path, include

from client.v import RegionHierarchyView
from .views import (
    ClientWithContactsViewSet, ContactDetailedViewSet, PaysViewSet, RegionViewSet, VilleViewSet,
    ClientViewSet, SiteViewSet, ContactViewSet
)

router = DefaultRouter()
router.register(r'pays', PaysViewSet)
router.register(r'regions', RegionViewSet)
router.register(r'villes', VilleViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'sites', SiteViewSet)
router.register(r'contacts', ContactViewSet)
router.register('contacts-detailles', ContactDetailedViewSet, basename='contacts-detailles')
router.register(r'clientsContacts', ClientWithContactsViewSet, basename='client-contacts')

urlpatterns = [
    path('', include(router.urls)),
    path('contact2/', RegionHierarchyView.as_view(), name='regions-hierarchy'),
]
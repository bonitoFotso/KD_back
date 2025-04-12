from rest_framework import filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Q
from django.utils.timezone import now
from datetime import timedelta
from factures_app.models import Facture

from .models import Pays, Region, Ville, Client, Site, Contact
from document.models import (
    Rapport, 
    Formation, Participant, AttestationFormation,
)
from rest_framework import viewsets

from .serializers import (
    ClientDetailSerializer, ClientWithContactsDetailSerializer, ClientWithContactsListSerializer, 
    ContactDetailedSerializer, PaysListSerializer, PaysDetailSerializer, PaysEditSerializer,
    RegionListSerializer, RegionDetailSerializer, RegionEditSerializer,
    VilleListSerializer, VilleDetailSerializer, VilleEditSerializer,
    ClientListSerializer, ClientEditSerializer,
    SiteListSerializer, SiteDetailSerializer, SiteEditSerializer,
    ContactListSerializer, ContactDetailSerializer, ContactEditSerializer
)

from document.serializers import (
    OffreListSerializer, ProformaListSerializer, AffaireListSerializer,
    FactureListSerializer, RapportListSerializer, FormationListSerializer,
    ParticipantListSerializer, AttestationFormationListSerializer,
)

from offres_app.models import Offre
from affaires_app.models import Affaire
from opportunites_app.models import Opportunite
from opportunites_app.serializers import OpportuniteSerializer
class PaysViewSet(viewsets.ModelViewSet):
    queryset = Pays.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom', 'code_iso']
    ordering_fields = ['nom', 'code_iso']

    def get_serializer_class(self):
        if self.action == 'list':
            return PaysListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return PaysEditSerializer
        return PaysDetailSerializer

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['pays']
    search_fields = ['nom', 'pays__nom']
    ordering_fields = ['nom', 'pays__nom']

    def get_serializer_class(self):
        if self.action == 'list':
            return RegionListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RegionEditSerializer
        return RegionDetailSerializer

class VilleViewSet(viewsets.ModelViewSet):
    queryset = Ville.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['region', 'region__pays']
    search_fields = ['nom', 'region__nom', 'region__pays__nom']
    ordering_fields = ['nom', 'region__nom']

    def get_serializer_class(self):
        if self.action == 'list':
            return VilleListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return VilleEditSerializer
        return VilleDetailSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.filter()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ville', 'agreer', 'agreement_fournisseur', 'secteur_activite']
    search_fields = ['nom', 'c_num', 'email', 'telephone', 'matricule']
    ordering_fields = ['nom', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClientListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClientEditSerializer
        elif self.action == 'with_contacts':
            return ClientWithContactsListSerializer
        elif self.action == 'with_contacts_detail':
            return ClientWithContactsDetailSerializer
        return ClientDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date_debut = self.request.query_params.get('date_debut', None)
        date_fin = self.request.query_params.get('date_fin', None)
        
        if date_debut:
            queryset = queryset.filter(created_at__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(created_at__lte=date_fin)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def with_contacts(self, request):
        """Retourne la liste des clients avec leurs contacts."""
        queryset = self.filter_queryset(self.get_queryset().prefetch_related('contacts'))
        serializer = ClientWithContactsListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def with_contacts_detail(self, request, pk=None):
        """Retourne les détails d'un client avec ses contacts."""
        client = self.get_object()
        serializer = ClientWithContactsDetailSerializer(client)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def sites(self, request, pk=None):
        """Retourne les sites d'un client."""
        client = self.get_object()
        sites = Site.objects.filter(client=client)
        serializer = SiteListSerializer(sites, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Retourne les contacts d'un client."""
        client = self.get_object()
        contacts = Contact.objects.filter(client=client)
        serializer = ContactListSerializer(contacts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def opportunites(self, request, pk=None):
        """Retourne les opportunités d'un client."""
        client = self.get_object()
        opportunites = Opportunite.objects.filter(client=client)
        serializer = OpportuniteSerializer(opportunites, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def offres(self, request, pk=None):
        """Retourne les offres d'un client."""
        client = self.get_object()
        offres = Offre.objects.filter(client=client)
        serializer = OffreListSerializer(offres, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def affaires(self, request, pk=None):
        """Retourne les affaires d'un client."""
        client = self.get_object()
        offres = Offre.objects.filter(client=client)
        # Use a flat list to collect all affaires
        affaires = Affaire.objects.filter(offre__in=offres)
        serializer = AffaireListSerializer(affaires, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def factures(self, request, pk=None):
        """Retourne les factures d'un client."""
        client = self.get_object()
        # Get all offres for this client
        offres = Offre.objects.filter(client=client)
        # Get all affaires related to these offres
        affaires = Affaire.objects.filter(offre__in=offres)
        # Get all factures related to these affaires
        factures = Facture.objects.filter(affaire__in=affaires)
        serializer = FactureListSerializer(factures, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def formations(self, request, pk=None):
        """Retourne les formations d'un client."""
        client = self.get_object()
        formations = Formation.objects.filter(client=client)
        serializer = FormationListSerializer(formations, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def rapports(self, request, pk=None):
        """Retourne les rapports d'un client."""
        client = self.get_object()
        rapports = Rapport.objects.filter(client=client)
        serializer = RapportListSerializer(rapports, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistiques(self, request, pk=None):
        """Retourne les statistiques d'un client."""
        client = self.get_object()
        
        # Statistiques des opportunités
        opportunites_stats = {
            'total': Opportunite.objects.filter(client=client).count(),
            'gagnees': Opportunite.objects.filter(client=client, statut='GAGNEE').count(),
            'perdues': Opportunite.objects.filter(client=client, statut='PERDUE').count(),
            'en_cours': Opportunite.objects.filter(client=client).exclude(
                statut__in=['GAGNEE', 'PERDUE']).count(),
            'valeur_totale': Opportunite.objects.filter(client=client).aggregate(
                Sum('montant_estime'))['montant_estime__sum'] or 0,
        }
        
        # Statistiques des offres
        offres_stats = {
            'total': Offre.objects.filter(client=client).count(),
            'gagnees': Offre.objects.filter(client=client, statut='GAGNE').count(),
            'perdues': Offre.objects.filter(client=client, statut='PERDU').count(),
            'en_cours': Offre.objects.filter(client=client).exclude(
                statut__in=['GAGNE', 'PERDU']).count(),
            'valeur_totale': Offre.objects.filter(client=client).aggregate(
                Sum('montant'))['montant__sum'] or 0,
        }
        
        # Statistiques des affaires
        affaires_stats = {
            'total': Affaire.objects.filter(client=client).count(),
            'en_cours': Affaire.objects.filter(client=client, statut='EN_COURS').count(),
            'terminees': Affaire.objects.filter(client=client, statut='TERMINEE').count(),
            'annulees': Affaire.objects.filter(client=client, statut='ANNULEE').count(),
        }
        
        # Statistiques des factures
        factures_stats = {
            'total': Facture.objects.filter(client=client).count(),
            'valeur_totale': Offre.objects.filter(client=client, statut='GAGNE').aggregate(
                Sum('montant'))['montant__sum'] or 0,
        }
        
        return Response({
            'opportunites': opportunites_stats,
            'offres': offres_stats,
            'affaires': affaires_stats,
            'factures': factures_stats,
            'contacts': Contact.objects.filter(client=client).count(),
            'sites': Site.objects.filter(client=client).count(),
            'formations': Formation.objects.filter(client=client).count(),
            'rapports': Rapport.objects.filter(client=client).count(),
        })

class SiteViewSet(viewsets.ModelViewSet):
    queryset = Site.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'ville']
    search_fields = ['nom', 's_num', 'client__nom', 'localisation']
    ordering_fields = ['nom', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return SiteListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return SiteEditSerializer
        return SiteDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date_debut = self.request.query_params.get('date_debut', None)
        date_fin = self.request.query_params.get('date_fin', None)
        
        if date_debut:
            queryset = queryset.filter(created_at__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(created_at__lte=date_fin)
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """Retourne les contacts associés à un site."""
        site = self.get_object()
        contacts = Contact.objects.filter(site=site)
        serializer = ContactListSerializer(contacts, many=True)
        return Response(serializer.data)

class ContactViewSet(viewsets.ModelViewSet):
    queryset = Contact.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'service', 'relance', 'ville']
    search_fields = ['nom', 'prenom', 'email', 'telephone', 'mobile', 'client__nom']
    ordering_fields = ['nom', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ContactListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ContactEditSerializer
        elif self.action == 'detailed':
            return ContactDetailedSerializer
        return ContactDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        date_debut = self.request.query_params.get('date_debut', None)
        date_fin = self.request.query_params.get('date_fin', None)
        
        if date_debut:
            queryset = queryset.filter(created_at__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(created_at__lte=date_fin)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def detailed(self, request):
        """Retourne la liste des contacts avec des informations détaillées."""
        queryset = self.filter_queryset(self.get_queryset().select_related('client', 'site', 'ville'))
        serializer = ContactDetailedSerializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def opportunites(self, request, pk=None):
        """Retourne les opportunités associées à un contact."""
        contact = self.get_object()
        opportunites = Opportunite.objects.filter(contact=contact)
        serializer = OpportuniteListSerializer(opportunites, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def offres(self, request, pk=None):
        """Retourne les offres associées à un contact."""
        contact = self.get_object()
        offres = Offre.objects.filter(contact=contact)
        serializer = OffreListSerializer(offres, many=True)
        return Response(serializer.data)
    
class ContactDetailedViewSet(viewsets.ReadOnlyModelViewSet):
   serializer_class = ContactDetailedSerializer
   filter_backends = [DjangoFilterBackend, filters.SearchFilter]
   
   filterset_fields = {
       'ville__region': ['exact'],
       'ville': ['exact'],
       'client__secteur_activite': ['exact'],
       'client__agreer': ['exact'],
       'relance': ['exact']
   }
   search_fields = ['nom', 'prenom', 'client__nom', 'service']

   def get_queryset(self):
       return Contact.objects.all()
   
class ClientWithContactsViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.prefetch_related('contacts').all()
    filterset_fields = ['ville', 'agreer', 'agreement_fournisseur', 'secteur_activite']
    search_fields = ['nom', 'c_num', 'email', 'telephone', 'matricule']
    ordering_fields = ['nom', 'created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return ClientWithContactsListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ClientEditSerializer
        return ClientWithContactsDetailSerializer

    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        client = self.get_object()
        contacts = client.contacts.all()
        serializer = ContactSerializer(contacts, many=True)
        return Response(serializer.data)

    def get_queryset(self):
        queryset = super().get_queryset()
        # Filtres existants
        date_debut = self.request.query_params.get('date_debut')
        date_fin = self.request.query_params.get('date_fin')
        
        if date_debut:
            queryset = queryset.filter(created_at__gte=date_debut)
        if date_fin:
            queryset = queryset.filter(created_at__lte=date_fin)

        # Filtres sur les contacts
        contact_service = self.request.query_params.get('contact_service')
        contact_poste = self.request.query_params.get('contact_poste')

        if contact_service:
            queryset = queryset.filter(contacts__service__icontains=contact_service)
        if contact_poste:
            queryset = queryset.filter(contacts__poste__icontains=contact_poste)

        return queryset.distinct()
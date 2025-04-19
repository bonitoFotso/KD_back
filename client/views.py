from rest_framework import filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Q
from django.utils.timezone import now
from datetime import timedelta
from affaires_app.serializers import AffaireSerializer, FactureSerializer, FormationSerializer, RapportSerializer
from client.filters import AgreementFilter, InteractionFilter, TypeInteractionFilter
from client.permissions import IsOwnerOrReadOnly, IsSuperUserOrReadOnly
from factures_app.models import Facture
from django.utils import timezone

from offres_app.serializers import ContactSerializer, OffreSerializer
from proformas_app.admin import ProformaAdmin
from proformas_app.models import Proforma
from proformas_app.serializers import ProformaSerializer

from .models import Agreement, Categorie, Interaction, Pays, Region, TypeInteraction, Ville, Client, Site, Contact
from document.models import (
    Rapport, 
    Formation, Participant, AttestationFormation,
)
from rest_framework import viewsets

from .serializers import (
    AgreementDetailSerializer, AgreementSerializer, CategoryDetailSerializer, CategoryEditSerializer, CategoryListSerializer, ClientDetailSerializer, ClientWithContactsDetailSerializer, ClientWithContactsListSerializer, 
    ContactDetailedSerializer, InteractionDetailSerializer, InteractionSerializer, PaysListSerializer, PaysDetailSerializer, PaysEditSerializer,
    RegionListSerializer, RegionDetailSerializer, RegionEditSerializer, TypeInteractionSerializer,
    VilleListSerializer, VilleDetailSerializer, VilleEditSerializer,
    ClientListSerializer, ClientEditSerializer,
    SiteListSerializer, SiteDetailSerializer, SiteEditSerializer,
    ContactListSerializer, ContactDetailSerializer, ContactEditSerializer
)

from document.serializers import (
    AttestationFormationDetailSerializer, OffreListSerializer, ParticipantDetailSerializer, ProformaListSerializer, AffaireListSerializer,
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
    
class CategoryViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les catégories de clients.
    """
    queryset = Categorie.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nom']
    ordering_fields = ['nom']

    def get_serializer_class(self):
        if self.action == 'list':
            return CategoryListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CategoryEditSerializer
        return CategoryDetailSerializer

class ClientViewSet(viewsets.ModelViewSet):
    queryset = Client.objects.filter().order_by('nom')
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['ville', 'agree', 'secteur_activite']
    search_fields = ['nom', 'c_num', 'email', 'telephone', 'matricule']
    ordering_fields = ['nom']
    

    def get_serializer_class(self):
        if self.action == 'list':
            queryset = Client.objects.filter(est_client=True)
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
            
        #if self.action == 'list':
        #    return Client.objects.filter(est_client=True)
            
        return queryset
    
    @action(detail=True, methods=['get'])
    def docs(self, request, pk=None):
        """Retourne les documents et données associés à un client."""
        client = self.get_object()

        # Récupération des différentes données liées au client
        opportunites = Opportunite.objects.filter(client=client)
        offres = Offre.objects.filter(client=client)

        # Initialisation des listes pour stocker les objets individuels
        affaires = []
        proformas = []
        factures = []
        rapports = []
        attestations = []
        formations = []
        participants = []  # Ajout de la liste manquante

        # Collection des affaires et proformas liés aux offres
        for offre in offres:
            affaires_offre = Affaire.objects.filter(offre=offre)
            affaires.extend(affaires_offre)
            proformas_offre = Proforma.objects.filter(offre=offre)  # Correction: utilisation de Proforma au lieu d'Opportunite
            proformas.extend(proformas_offre)

        # Collection des documents liés aux affaires
        for affaire in affaires:
            factures.extend(Facture.objects.filter(affaire=affaire))
            rapports.extend(Rapport.objects.filter(affaire=affaire))
            attestations.extend(AttestationFormation.objects.filter(affaire=affaire))
            formations_affaire = Formation.objects.filter(affaire=affaire)
            formations.extend(formations_affaire)

            # Ajout des participants si nécessaire
            participants.extend(Participant.objects.filter(formation__in=formations_affaire))

        contacts = Contact.objects.filter(client=client)
        sites = Site.objects.filter(client=client)

        # Conversion des listes en QuerySets pour la sérialisation
        affaires_qs = Affaire.objects.filter(id__in=[a.id for a in affaires])
        proformas_qs = Proforma.objects.filter(id__in=[p.id for p in proformas])
        factures_qs = Facture.objects.filter(id__in=[f.id for f in factures])
        rapports_qs = Rapport.objects.filter(id__in=[r.id for r in rapports])
        attestations_qs = AttestationFormation.objects.filter(id__in=[a.id for a in attestations])
        formations_qs = Formation.objects.filter(id__in=[f.id for f in formations])
        participants_qs = Participant.objects.filter(id__in=[p.id for p in participants])

        # Sérialisation des données
        data = {
            'opportunites': OpportuniteSerializer(opportunites, many=True).data,
            'offres': OffreSerializer(offres, many=True).data,
            'affaires': AffaireSerializer(affaires_qs, many=True).data,
            'proformas': ProformaSerializer(proformas_qs, many=True).data,
            'factures': FactureSerializer(factures_qs, many=True).data,
            'rapports': RapportSerializer(rapports_qs, many=True).data,
            'formations': FormationSerializer(formations_qs, many=True).data,
            'attestations': AttestationFormationDetailSerializer(attestations_qs, many=True).data,
            'contacts': ContactSerializer(contacts, many=True).data,
            'sites': SiteDetailSerializer(sites, many=True).data,

            # Ajout des compteurs pour faciliter l'affichage
            'counts': {
                'opportunites': opportunites.count(),
                'offres': offres.count(),
                'affaires': len(affaires),
                'proformas': len(proformas),
                'factures': len(factures),
                'rapports': len(rapports),
                'formations': len(formations),
                'participants': len(participants),
                'attestations': len(attestations),
                'contacts': contacts.count(),
                'sites': sites.count(),
            }
        }

        return Response(data)
    
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
        
    @action(detail=True, methods=['get'])
    def sites(self, request, pk=None):
        """
        Retourner tous les sites pour un client.
        """
        client = self.get_object()
        sites = Site.objects.filter(client=client)
        serializer = SiteListSerializer(sites, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def contacts(self, request, pk=None):
        """
        Retourner tous les contacts pour un client.
        """
        client = self.get_object()
        contacts = Contact.objects.filter(client=client)
        serializer = ContactListSerializer(contacts, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def agreements(self, request, pk=None):
        """
        Retourner tous les agreements pour un client.
        """
        client = self.get_object()
        agreements = Agreement.objects.filter(client=client)
        serializer = AgreementSerializer(agreements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def interactions(self, request, pk=None):
        """
        Retourner toutes les interactions pour un client.
        """
        client = self.get_object()
        interactions = Interaction.objects.filter(client=client)
        serializer = InteractionSerializer(interactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def prospects(self, request):
        """
        Retourner tous les prospects (clients potentiels).
        """
        prospects = Client.objects.filter(est_client=False)
        page = self.paginate_queryset(prospects)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(prospects, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Retourner des statistiques sur les clients.
        """
        total_clients = Client.objects.filter(est_client=True).count()
        total_prospects = Client.objects.filter(est_client=False).count()
        clients_par_categorie = Client.objects.filter(est_client=True).values('categorie__nom').annotate(
            count=Count('id')).order_by('categorie__nom')
        prospects_par_categorie = Client.objects.filter(est_client=False).values('categorie__nom').annotate(
            count=Count('id')).order_by('categorie__nom')
        clients_par_mois = Client.objects.filter(
            est_client=True, 
            date_conversion_client__isnull=False
        ).extra(
            select={'month': "EXTRACT(month FROM date_conversion_client)"}
        ).values('month').annotate(count=Count('id')).order_by('month')

        return Response({
            'total_clients': total_clients,
            'total_prospects': total_prospects,
            'clients_par_categorie': clients_par_categorie,
            'prospects_par_categorie': prospects_par_categorie,
            'clients_par_mois': clients_par_mois,
        })

    @action(detail=True, methods=['post'])
    def convertir_en_client(self, request, pk=None):
        """
        Convertir un prospect en client.
        """
        client = self.get_object()
        if client.est_client:
            return Response(
                {"detail": "Ce prospect est déjà un client."},
                status=status.HTTP_400_BAD_REQUEST
            )

        client.est_client = True
        client.date_conversion_client = timezone.now().date()
        client.updated_by = request.user
        client.save()

        serializer = self.get_serializer(client)
        return Response(serializer.data)

class AgreementViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les agreements.
    """
    queryset = Agreement.objects.all()
    #permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = AgreementFilter
    search_fields = ['client__nom', 'entite__nom', 'statut_workflow']
    ordering_fields = ['date_debut', 'date_fin', 'date_statut']
    ordering = ['-date_debut']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return AgreementDetailSerializer
        return AgreementSerializer

    def perform_create(self, serializer):
        serializer.save(cree_par=self.request.user, modifie_par=self.request.user)

    def perform_update(self, serializer):
        serializer.save(modifie_par=self.request.user)

    @action(detail=False, methods=['get'])
    def a_renouveler(self, request):
        """
        Retourner tous les agreements à renouveler dans les 30 prochains jours.
        """
        today = timezone.now().date()
        date_limite = today + timezone.timedelta(days=30)
        
        agreements = Agreement.objects.filter(
            est_actif=True,
            date_fin__isnull=False,
            date_fin__lte=date_limite,
            date_fin__gte=today
        )
        
        page = self.paginate_queryset(agreements)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(agreements, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def expires(self, request):
        """
        Retourner tous les agreements expirés.
        """
        today = timezone.now().date()
        agreements = Agreement.objects.filter(
            est_actif=True,
            date_fin__isnull=False,
            date_fin__lt=today
        )
        
        page = self.paginate_queryset(agreements)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(agreements, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def renouveler(self, request, pk=None):
        """
        Renouveler un agreement en créant une nouvelle instance avec les dates mises à jour.
        """
        old_agreement = self.get_object()
        
        # Vérifier que l'agreement peut être renouvelé
        if not old_agreement.date_fin:
            return Response(
                {"detail": "Impossible de renouveler un agreement sans date de fin."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Récupérer les données du corps de la requête ou utiliser des valeurs par défaut
        nouvelle_date_debut = request.data.get('date_debut', old_agreement.date_fin)
        nouvelle_date_fin = request.data.get('date_fin', None)
        nouveau_statut = request.data.get('statut_workflow', 'VALIDE')
        
        # Créer un nouvel agreement
        nouveau_agreement = Agreement(
            client=old_agreement.client,
            entite=old_agreement.entite,
            date_debut=nouvelle_date_debut,
            date_fin=nouvelle_date_fin,
            est_actif=True,
            statut_workflow=nouveau_statut,
            commentaires=f"Renouvellement de l'agreement #{old_agreement.id}",
            cree_par=request.user,
            modifie_par=request.user
        )
        nouveau_agreement.save()
        
        # Mettre à jour l'ancien agreement
        old_agreement.est_actif = False
        old_agreement.statut_workflow = 'EXPIRE'
        old_agreement.modifie_par = request.user
        old_agreement.save()
        
        serializer = self.get_serializer(nouveau_agreement)
        return Response(serializer.data)


class TypeInteractionViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les types d'interactions.
    """
    queryset = TypeInteraction.objects.all()
    serializer_class = TypeInteractionSerializer
    permission_classes = [IsSuperUserOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = TypeInteractionFilter
    search_fields = ['nom', 'description']
    ordering_fields = ['nom']
    ordering = ['nom']

    @action(detail=True, methods=['get'])
    def interactions(self, request, pk=None):
        """
        Retourner toutes les interactions d'un type.
        """
        type_interaction = self.get_object()
        interactions = Interaction.objects.filter(type_interaction=type_interaction)
        serializer = InteractionSerializer(interactions, many=True)
        return Response(serializer.data)


class InteractionViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les interactions.
    """
    queryset = Interaction.objects.all()
    permission_classes = [IsOwnerOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = InteractionFilter
    search_fields = ['titre', 'notes', 'contact__nom', 'client__nom', 'type_interaction__nom']
    ordering_fields = ['date', 'type_interaction__nom']
    ordering = ['-date']

    def get_serializer_class(self):
        if self.action in ['retrieve', 'create', 'update', 'partial_update']:
            return InteractionDetailSerializer
        return InteractionSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=False, methods=['get'])
    def a_venir(self, request):
        """
        Retourner toutes les interactions à venir.
        """
        now = timezone.now()
        interactions = Interaction.objects.filter(date__gt=now).order_by('date')
        
        page = self.paginate_queryset(interactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(interactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def rendez_vous(self, request):
        """
        Retourner tous les rendez-vous.
        """
        interactions = Interaction.objects.filter(est_rendez_vous=True).order_by('date')
        
        page = self.paginate_queryset(interactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(interactions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def relances_a_faire(self, request):
        """
        Retourner toutes les interactions avec des relances à faire.
        """
        today = timezone.now().date()
        interactions = Interaction.objects.filter(
            date_relance__isnull=False,
            date_relance__lte=today,
            relance_effectuee=False
        ).order_by('date_relance')
        
        page = self.paginate_queryset(interactions)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(interactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def marquer_relance_effectuee(self, request, pk=None):
        """
        Marquer une relance comme effectuée.
        """
        interaction = self.get_object()
        
        if not interaction.date_relance:
            return Response(
                {"detail": "Cette interaction n'a pas de date de relance."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if interaction.relance_effectuee:
            return Response(
                {"detail": "Cette relance a déjà été effectuée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interaction.relance_effectuee = True
        interaction.updated_by = request.user
        interaction.save()
        
        serializer = self.get_serializer(interaction)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def creer_relance(self, request, pk=None):
        """
        Créer une nouvelle interaction de relance pour cette interaction.
        """
        interaction_source = self.get_object()
        
        # Récupérer les données ou utiliser des valeurs par défaut
        date_relance = request.data.get('date', None)
        if not date_relance:
            return Response(
                {"detail": "Une date est requise pour créer une relance."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        type_interaction_id = request.data.get('type_interaction', None)
        if type_interaction_id:
            try:
                type_interaction = TypeInteraction.objects.get(id=type_interaction_id)
            except TypeInteraction.DoesNotExist:
                return Response(
                    {"detail": "Type d'interaction invalide."},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            # Utiliser un type d'interaction par défaut pour les relances
            type_interaction, _ = TypeInteraction.objects.get_or_create(
                nom="Relance",
                defaults={"description": "Relance d'une interaction précédente"}
            )
        
        # Créer la nouvelle interaction
        nouvelle_interaction = Interaction(
            date=date_relance,
            type_interaction=type_interaction,
            titre=f"Relance: {interaction_source.titre}",
            notes=request.data.get('notes', f"Relance de l'interaction #{interaction_source.id}"),
            est_rendez_vous=request.data.get('est_rendez_vous', False),
            duree_minutes=request.data.get('duree_minutes', None),
            contact=interaction_source.contact,
            client=interaction_source.client,
            entite=interaction_source.entite,
            created_by=request.user,
            updated_by=request.user
        )
        nouvelle_interaction.save()
        
        # Marquer la source comme ayant été relancée
        interaction_source.relance_effectuee = True
        interaction_source.updated_by = request.user
        interaction_source.save()
        
        serializer = self.get_serializer(nouvelle_interaction)
        return Response(serializer.data)

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
       'client__agree': ['exact'],
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
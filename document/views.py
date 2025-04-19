from rest_framework import viewsets, status, filters
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import Count, Sum, Q
from django.utils.timezone import now
from datetime import timedelta

from factures_app.models import Facture
from offres_app.models import Offre
from proformas_app.models import Proforma

from .models import (
    Departement, Entity, Product, 
    Rapport, Formation, 
    Participant, AttestationFormation
)

from .serializers import (
    DepartementDetailSerializer, EntityListSerializer, EntityDetailSerializer, EntityEditSerializer,
    CategoryListSerializer,
    ProductListSerializer, ProductDetailSerializer, ProductEditSerializer,
    OffreListSerializer, OffreDetailSerializer, OffreEditSerializer,
    ProformaListSerializer, ProformaDetailSerializer, ProformaEditSerializer,
    AffaireListSerializer, AffaireDetailSerializer, AffaireEditSerializer,
    FactureListSerializer, FactureDetailSerializer, FactureEditSerializer,
    RapportListSerializer, RapportDetailSerializer, RapportEditSerializer,
    FormationListSerializer, FormationDetailSerializer, FormationEditSerializer,
    ParticipantListSerializer, ParticipantDetailSerializer, ParticipantEditSerializer,
    AttestationFormationListSerializer, AttestationFormationDetailSerializer, AttestationFormationEditSerializer,
)

from client.serializers import ClientListSerializer

class EntityViewSet(viewsets.ModelViewSet):
    queryset = Entity.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']

    def get_serializer_class(self):
        print(f"Action: {self.action}")
        if self.action == 'list':
            return EntityListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return EntityEditSerializer
        return EntityDetailSerializer

class DepartementViewSet(viewsets.ModelViewSet):
    queryset = Departement.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['code', 'name']
    ordering_fields = ['code', 'name']

    def get_serializer_class(self):
        if self.action == 'list':
            return DepartementDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return DepartementDetailSerializer
        return DepartementDetailSerializer
    

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['departement', 'departement__entity']
    search_fields = ['code', 'name', 'departement__name']
    ordering_fields = ['code', 'name']

    def get_serializer_class(self):
        print(f"Action: {self.action}")
        if self.action == 'list':
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductEditSerializer
        return ProductDetailSerializer

    @action(detail=True, methods=['get'])
    def offres(self, request, pk=None):
        """Retourne les offres liées à ce produit."""
        product = self.get_object()
        offres = Offre.objects.filter(Q(produit=product) | Q(produits=product)).distinct()
        serializer = OffreListSerializer(offres, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def opportunites(self, request, pk=None):
        """Retourne les opportunités liées à ce produit."""
        product = self.get_object()
        opportunites = Opportunite.objects.filter(
            Q(produit_principal=product) | Q(produits=product)
        ).distinct()
        serializer = OpportuniteListSerializer(opportunites, many=True)
        return Response(serializer.data)


class OffreViewSet(viewsets.ModelViewSet):
    queryset = Offre.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'statut', 'entity', 'produit']
    search_fields = ['reference', 'client__nom']
    ordering_fields = ['reference', 'date_creation', 'montant']

    def get_serializer_class(self):
        if self.action == 'list':
            return OffreListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return OffreEditSerializer
        return OffreDetailSerializer

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide une offre."""
        offre = self.get_object()
        try:
            if offre.statut != 'GAGNE':
                offre.statut = 'GAGNE'
                offre.save()
            serializer = self.get_serializer(offre)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def a_relancer(self, request):
        """Retourne les offres qui nécessitent une relance."""
        offres = Offre.objects.filter(
            relance__lte=now(),
            statut__in=['ENVOYE', 'EN_NEGOCIATION']
        ).order_by('relance')
        serializer = OffreListSerializer(offres, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne des statistiques sur les offres."""
        period = request.query_params.get('period', 'month')
        
        if period == 'year':
            date_debut = now().replace(month=1, day=1)
        elif period == 'quarter':
            current_month = now().month
            quarter_start_month = ((current_month - 1) // 3) * 3 + 1
            date_debut = now().replace(month=quarter_start_month, day=1)
        else:  # month
            date_debut = now().replace(day=1)
        
        # Statistiques par statut
        statut_stats = Offre.objects.filter(
            date_creation__gte=date_debut
        ).values('statut').annotate(
            count=Count('id'),
            montant_total=Sum('montant')
        )
        
        # Statistiques par produit
        produit_stats = Offre.objects.filter(
            date_creation__gte=date_debut
        ).values('produit__name').annotate(
            count=Count('id'),
            montant_total=Sum('montant')
        )
        
        # Statistiques par entité
        entity_stats = Offre.objects.filter(
            date_creation__gte=date_debut
        ).values('entity__name').annotate(
            count=Count('id'),
            montant_total=Sum('montant')
        )
        
        return Response({
            'par_statut': statut_stats,
            'par_produit': produit_stats,
            'par_entity': entity_stats,
            'montant_total': Offre.objects.filter(
                date_creation__gte=date_debut
            ).aggregate(Sum('montant'))['montant__sum'] or 0,
            'taux_conversion': {
                'total': Offre.objects.filter(date_creation__gte=date_debut).count(),
                'gagnees': Offre.objects.filter(
                    date_creation__gte=date_debut, statut='GAGNE'
                ).count(),
                'perdues': Offre.objects.filter(
                    date_creation__gte=date_debut, statut='PERDU'
                ).count(),
            }
        })

class ProformaViewSet(viewsets.ModelViewSet):
    queryset = Proforma.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'statut', 'entity', 'offre']
    search_fields = ['reference', 'client__nom']
    ordering_fields = ['reference', 'date_creation']

    def get_serializer_class(self):
        if self.action == 'list':
            return ProformaListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProformaEditSerializer
        return ProformaDetailSerializer

    @action(detail=True, methods=['post'])
    def valider(self, request, pk=None):
        """Valide un proforma."""
        proforma = self.get_object()
        try:
            proforma.valider(request.user)
            proforma.save()
            serializer = self.get_serializer(proforma)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change le statut d'un proforma."""
        proforma = self.get_object()
        new_status = request.data.get('status', None)
        if not new_status or new_status not in [s[0] for s in Proforma.STATUTS]:
            return Response(
                {"detail": "Statut invalide."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            proforma.statut = new_status
            proforma.save()
            serializer = self.get_serializer(proforma)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'statut', 'entity', 'affaire']
    search_fields = ['reference', 'client__nom']
    ordering_fields = ['reference', 'date_creation']

    def get_serializer_class(self):
        if self.action == 'list':
            return FactureListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FactureEditSerializer
        return FactureDetailSerializer

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change le statut d'une facture."""
        facture = self.get_object()
        new_status = request.data.get('status', None)
        if not new_status or new_status not in [s[0] for s in Facture.STATUTS]:
            return Response(
                {"detail": "Statut invalide."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            facture.statut = new_status
            facture.save()
            serializer = self.get_serializer(facture)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def statistiques(self, request):
        """Retourne des statistiques sur les factures."""
        period = request.query_params.get('period', 'month')
        
        if period == 'year':
            date_debut = now().replace(month=1, day=1)
        elif period == 'quarter':
            current_month = now().month
            quarter_start_month = ((current_month - 1) // 3) * 3 + 1
            date_debut = now().replace(month=quarter_start_month, day=1)
        else:  # month
            date_debut = now().replace(day=1)
        
        # Statistiques par statut
        statut_stats = Facture.objects.filter(
            date_creation__gte=date_debut
        ).values('statut').annotate(
            count=Count('id')
        )
        
        # Statistiques par client
        client_stats = Facture.objects.filter(
            date_creation__gte=date_debut
        ).values('client__nom').annotate(
            count=Count('id')
        )
        
        return Response({
            'par_statut': statut_stats,
            'par_client': client_stats,
            'total': Facture.objects.filter(date_creation__gte=date_debut).count(),
            'brouillon': Facture.objects.filter(
                date_creation__gte=date_debut, statut='BROUILLON'
            ).count(),
            'envoyees': Facture.objects.filter(
                date_creation__gte=date_debut, statut='ENVOYE'
            ).count(),
            'validees': Facture.objects.filter(
                date_creation__gte=date_debut, statut='VALIDE'
            ).count(),
            'refusees': Facture.objects.filter(
                date_creation__gte=date_debut, statut='REFUSE'
            ).count(),
        })

class RapportViewSet(viewsets.ModelViewSet):
    queryset = Rapport.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'statut', 'entity', 'affaire', 'produit']
    search_fields = ['reference', 'client__nom', 'numero']
    ordering_fields = ['reference', 'date_creation']

    def get_serializer_class(self):
        if self.action == 'list':
            return RapportListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return RapportEditSerializer
        return RapportDetailSerializer

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Change le statut d'un rapport."""
        rapport = self.get_object()
        new_status = request.data.get('status', None)
        if not new_status or new_status not in [s[0] for s in Rapport.STATUTS]:
            return Response(
                {"detail": "Statut invalide."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            rapport.statut = new_status
            rapport.save()
            serializer = self.get_serializer(rapport)
            return Response(serializer.data)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'])
    def attestations(self, request, pk=None):
        """Retourne les attestations liées à un rapport."""
        rapport = self.get_object()
        attestations = AttestationFormation.objects.filter(rapport=rapport)
        serializer = AttestationFormationListSerializer(attestations, many=True)
        return Response(serializer.data)

class FormationViewSet(viewsets.ModelViewSet):
    queryset = Formation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'affaire', 'rapport']
    search_fields = ['titre', 'client__nom', 'description']
    ordering_fields = ['titre', 'date_debut', 'date_fin']

    def get_serializer_class(self):
        if self.action == 'list':
            return FormationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return FormationEditSerializer
        return FormationDetailSerializer

    @action(detail=True, methods=['get'])
    def participants(self, request, pk=None):
        """Retourne les participants d'une formation."""
        formation = self.get_object()
        participants = Participant.objects.filter(formation=formation)
        serializer = ParticipantListSerializer(participants, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def attestations(self, request, pk=None):
        """Retourne les attestations de formation."""
        formation = self.get_object()
        attestations = AttestationFormation.objects.filter(formation=formation)
        serializer = AttestationFormationListSerializer(attestations, many=True)
        return Response(serializer.data)

class ParticipantViewSet(viewsets.ModelViewSet):
    queryset = Participant.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['formation']
    search_fields = ['nom', 'prenom', 'email', 'fonction']
    ordering_fields = ['nom', 'prenom']

    def get_serializer_class(self):
        if self.action == 'list':
            return ParticipantListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ParticipantEditSerializer
        return ParticipantDetailSerializer

    @action(detail=True, methods=['get'])
    def attestation(self, request, pk=None):
        """Retourne l'attestation d'un participant."""
        participant = self.get_object()
        try:
            attestation = AttestationFormation.objects.get(participant=participant)
            serializer = AttestationFormationDetailSerializer(attestation)
            return Response(serializer.data)
        except AttestationFormation.DoesNotExist:
            return Response(
                {"detail": "Aucune attestation trouvée pour ce participant."},
                status=status.HTTP_404_NOT_FOUND
            )

class AttestationFormationViewSet(viewsets.ModelViewSet):
    queryset = AttestationFormation.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['client', 'statut', 'entity', 'affaire', 'formation', 'participant', 'rapport']
    search_fields = ['reference', 'client__nom', 'participant__nom', 'participant__prenom']
    ordering_fields = ['reference', 'date_creation']

    def get_serializer_class(self):
        if self.action == 'list':
            return AttestationFormationListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return AttestationFormationEditSerializer
        return AttestationFormationDetailSerializer
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now
from django.db.models import Sum, Count, Q

from .models import Opportunite
from .serializers import (
    OpportuniteSerializer, 
    OpportuniteDetailSerializer,
    OpportuniteCreateSerializer,
    OpportuniteUpdateSerializer,
    OpportuniteTransitionSerializer,
    RaisonPerteSerializer
)
from .filters import OpportuniteFilter
from .permissions import OpportunitePermission


class OpportuniteViewSet(viewsets.ModelViewSet):
    """
    API pour la gestion des opportunités commerciales.
    
    Permet de créer, lister, mettre à jour et supprimer des opportunités,
    ainsi que d'effectuer des transitions d'état (qualifier, proposer, etc.).
    """
    queryset = Opportunite.objects.all()
    permission_classes = [IsAuthenticated, OpportunitePermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = OpportuniteFilter
    search_fields = ['reference', 'client__nom', 'description', 'besoins_client']
    ordering_fields = ['date_creation', 'date_modification', 'montant_estime', 'probabilite', 'statut']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        """
        Retourne le serializer approprié en fonction de l'action.
        """
        if self.action == 'create':
            return OpportuniteCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return OpportuniteUpdateSerializer
        elif self.action == 'retrieve':
            return OpportuniteDetailSerializer
        return OpportuniteDetailSerializer
    
    def get_queryset(self):
        """
        Filtre les opportunités en fonction de l'utilisateur et des paramètres.
        """
        queryset = Opportunite.objects.select_related(
            'client', 'contact', 'entity', 'produit_principal', 'created_by'
        ).prefetch_related('produits')
        
        # Filter by entity if specified
        entity_id = self.request.GET.get('entity_id')
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
            
        ## Filter by user's entities if not superuser
        #if not self.request.user.is_superuser:
        #    user_entities = self.request.user.entities.all()
        #    queryset = queryset.filter(entity__in=user_entities)
            
        # Filter by relance if specified
        relance = self.request.GET.get('relance')
        if relance == 'required':
            queryset = queryset.filter(
                relance__lte=now(),
                statut__in=['PROSPECT', 'QUALIFICATION', 'PROPOSITION', 'NEGOCIATION']
            )
        elif relance == 'upcoming':
            queryset = queryset.filter(
                relance__gt=now(),
                statut__in=['PROSPECT', 'QUALIFICATION', 'PROPOSITION', 'NEGOCIATION']
            )
            
        return queryset
    
    def perform_create(self, serializer):
        """
        Associe l'utilisateur actuel à l'opportunité lors de la création.
        """
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def qualifier(self, request, pk=None):
        """
        Transition: Marque l'opportunité comme qualifiée.
        """
        opportunite = self.get_object()
        
        try:
            opportunite.qualifier(request.user)
            opportunite.save()
            return Response({
                'success': True,
                'message': 'Opportunité qualifiée avec succès',
                'statut': opportunite.statut
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def proposer(self, request, pk=None):
        """
        Transition: Marque l'opportunité comme étant en proposition.
        """
        opportunite = self.get_object()
        
        try:
            opportunite.proposer(request.user)
            opportunite.save()
            return Response({
                'success': True,
                'message': 'Opportunité passée en proposition avec succès',
                'statut': opportunite.statut
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def negocier(self, request, pk=None):
        """
        Transition: Marque l'opportunité comme étant en négociation.
        """
        opportunite = self.get_object()
        
        try:
            opportunite.negocier(request.user)
            opportunite.save()
            return Response({
                'success': True,
                'message': 'Opportunité passée en négociation avec succès',
                'statut': opportunite.statut
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def gagner(self, request, pk=None):
        """
        Transition: Marque l'opportunité comme gagnée.
        """
        opportunite = self.get_object()
        
        try:
            opportunite.gagner(request.user)
            opportunite.save()
            return Response({
                'success': True,
                'message': 'Opportunité marquée comme gagnée avec succès',
                'statut': opportunite.statut
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def perdre(self, request, pk=None):
        """
        Transition: Marque l'opportunité comme perdue.
        """
        opportunite = self.get_object()
        serializer = RaisonPerteSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            raison = serializer.validated_data.get('raison')
            opportunite.perdre(request.user, raison=raison)
            opportunite.save()
            return Response({
                'success': True,
                'message': 'Opportunité marquée comme perdue avec succès',
                'statut': opportunite.statut
            })
        except Exception as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def creer_offre(self, request, pk=None):
        """
        Crée une offre à partir de cette opportunité.
        """
        opportunite = self.get_object()
        
        try:
            offre = opportunite.creer_offre(request.user)
            return Response({
                'success': True,
                'message': 'Offre créée avec succès',
                'offre_id': offre.pk,
                'offre_reference': offre.reference
            })
        except ValueError as e:
            return Response({
                'success': False,
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                'success': False,
                'message': f"Erreur lors de la création de l'offre: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        Retourne des statistiques sur les opportunités.
        """
        # Filtrer les opportunités selon les mêmes règles que le queryset principal
        queryset = self.get_queryset()
        
        # Statistiques par statut
        statut_stats = queryset.values('statut').annotate(
            count=Count('id'),
            montant_total=Sum('montant'),
            montant_estime_total=Sum('montant_estime')
        ).order_by('statut')
        
        # Opportunités nécessitant une relance
        relance_count = queryset.filter(
            relance__lte=now(),
            statut__in=['PROSPECT', 'QUALIFICATION', 'PROPOSITION', 'NEGOCIATION']
        ).count()
        
        # Statistiques globales
        totals = {
            'total_opportunities': queryset.count(),
            'total_montant': queryset.aggregate(Sum('montant'))['montant__sum'] or 0,
            'total_montant_estime': queryset.aggregate(Sum('montant_estime'))['montant_estime__sum'] or 0,
            'opportunites_gagnees': queryset.filter(statut='GAGNEE').count(),
            'opportunites_perdues': queryset.filter(statut='PERDUE').count(),
            'opportunites_en_cours': queryset.filter(~Q(statut__in=['GAGNEE', 'PERDUE'])).count(),
            'relances_necessaires': relance_count
        }
        
        return Response({
            'par_statut': statut_stats,
            'totaux': totals
        })


class OpportuniteTransitionViewSet(viewsets.GenericViewSet):
    """
    API pour effectuer des transitions d'état groupées sur plusieurs opportunités.
    """
    queryset = Opportunite.objects.all()
    permission_classes = [IsAuthenticated, OpportunitePermission]
    serializer_class = OpportuniteTransitionSerializer
    
    @action(detail=False, methods=['post'])
    def gagner_multiple(self, request):
        """
        Marque plusieurs opportunités comme gagnées.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ids = serializer.validated_data.get('ids', [])
        success_count = 0
        error_messages = []
        
        for opp_id in ids:
            try:
                opp = Opportunite.objects.get(pk=opp_id)
                opp.gagner(request.user)
                opp.save()
                success_count += 1
            except Opportunite.DoesNotExist:
                error_messages.append(f"Opportunité {opp_id} introuvable")
            except Exception as e:
                error_messages.append(f"Erreur sur opportunité {opp_id}: {str(e)}")
        
        return Response({
            'success': success_count > 0,
            'success_count': success_count,
            'error_count': len(ids) - success_count,
            'errors': error_messages
        })
    
    @action(detail=False, methods=['post'])
    def perdre_multiple(self, request):
        """
        Marque plusieurs opportunités comme perdues.
        """
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        ids = serializer.validated_data.get('ids', [])
        raison = serializer.validated_data.get('raison')
        success_count = 0
        error_messages = []
        
        for opp_id in ids:
            try:
                opp = Opportunite.objects.get(pk=opp_id)
                opp.perdre(request.user, raison=raison)
                opp.save()
                success_count += 1
            except Opportunite.DoesNotExist:
                error_messages.append(f"Opportunité {opp_id} introuvable")
            except Exception as e:
                error_messages.append(f"Erreur sur opportunité {opp_id}: {str(e)}")
        
        return Response({
            'success': success_count > 0,
            'success_count': success_count,
            'error_count': len(ids) - success_count,
            'errors': error_messages
        })
from rest_framework import viewsets, status, filters, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now
from django.db.models import Sum, Count, Q

from factures_app.filters import FactureFilter
from .models import Facture
from .serializers import FactureSerializer, FactureDetailSerializer, FactureCreateSerializer

class FactureViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les factures.
    """
    queryset = Facture.objects.all()
    
    serializer_class = FactureSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = FactureFilter
    filterset_fields = {
        'statut': ['exact', 'in'],
        'date_creation': ['gte', 'lte'],
        'date_emission': ['gte', 'lte', 'isnull'],
        'date_echeance': ['gte', 'lte', 'isnull'],
        'date_paiement': ['gte', 'lte', 'isnull'],
        'affaire__offre__client': ['exact'],
        'affaire__offre__entity': ['exact'],
        'montant_ttc': ['gte', 'lte'],
    }
    search_fields = ['reference', 'affaire__reference', 'affaire__offre__client__nom', 'notes']
    ordering_fields = ['date_creation', 'date_emission', 'date_echeance', 'montant_ttc', 'reference']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return FactureCreateSerializer
        elif self.action == 'retrieve':
            return FactureDetailSerializer
        return FactureSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_paid(self, request, pk=None):
        """
        Marquer une facture comme payée
        """
        facture = self.get_object()
        amount = request.data.get('amount', None)
        
        if amount is not None:
            try:
                amount = float(amount)
            except (ValueError, TypeError):
                return Response(
                    {'error': 'Le montant doit être un nombre valide'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        facture.mark_as_paid(amount=amount, user=request.user)
        
        return Response({
            'status': 'success',
            'message': 'Facture marquée comme payée',
            'montant_paye': float(facture.montant_paye),
            'statut': facture.statut
        })
    
    @action(detail=True, methods=['post'])
    def mark_as_issued(self, request, pk=None):
        """
        Marquer une facture comme émise
        """
        facture = self.get_object()
        
        if facture.statut != 'BROUILLON':
            return Response(
                {'error': 'Seules les factures en brouillon peuvent être marquées comme émises'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        facture.statut = 'EMISE'
        facture.date_emission = now()
        facture.updated_by = request.user
        facture.save()
        
        return Response({
            'status': 'success',
            'message': 'Facture marquée comme émise',
            'statut': facture.statut,
            'date_emission': facture.date_emission
        })
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Annuler une facture
        """
        facture = self.get_object()
        
        facture.cancel(user=request.user)
        
        return Response({
            'status': 'success',
            'message': 'Facture annulée',
            'statut': facture.statut
        })
    
    @action(detail=True, methods=['post'], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def upload_file(self, request, pk=None):
        """
        Télécharger un fichier pour une facture
        """
        facture = self.get_object()
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'Aucun fichier fourni'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sauvegarder le fichier
        file = request.FILES['file']
        facture.fichier = file
        facture.updated_by = request.user
        facture.save()
        
        return Response({
            'status': 'success',
            'message': 'Fichier téléchargé avec succès',
            'file_name': facture.fichier.name,
            'file_url': request.build_absolute_uri(facture.fichier.url) if facture.fichier else None
        })
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """
        Télécharger le fichier de la facture
        """
        facture = self.get_object()
        
        if not facture.fichier:
            return Response(
                {'error': 'Aucun fichier disponible pour cette facture'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Selon votre configuration, vous pourriez renvoyer l'URL ou le fichier directement
        return Response({
            'fichier_url': request.build_absolute_uri(facture.fichier.url)
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Statistiques sur les factures
        """
        # Statistiques globales
        total_count = self.get_queryset().count()
        montant_total = self.get_queryset().aggregate(total=Sum('montant_ttc'))['total'] or 0
        montant_paye = self.get_queryset().aggregate(total=Sum('montant_paye'))['total'] or 0
        
        # Statistiques par statut
        stats_par_statut = self.get_queryset().values('statut').annotate(
            count=Count('id'),
            montant=Sum('montant_ttc')
        ).order_by('statut')
        
        # Factures en retard
        factures_en_retard = self.get_queryset().filter(
            Q(statut='EMISE') | Q(statut='IMPAYEE'),
            date_echeance__lt=now()
        ).count()
        
        # Statistiques par mois
        current_year = now().year
        stats_par_mois = []
        
        for month in range(1, 13):
            month_data = self.get_queryset().filter(
                date_creation__year=current_year,
                date_creation__month=month
            ).aggregate(
                count=Count('id'),
                montant=Sum('montant_ttc'),
                paye=Sum('montant_paye')
            )
            
            stats_par_mois.append({
                'mois': month,
                'count': month_data['count'] or 0,
                'montant': float(month_data['montant'] or 0),
                'paye': float(month_data['paye'] or 0)
            })
        
        return Response({
            'total_count': total_count,
            'montant_total': float(montant_total),
            'montant_paye': float(montant_paye),
            'taux_recouvrement': float(montant_paye / montant_total) if montant_total > 0 else 0,
            'factures_en_retard': factures_en_retard,
            'stats_par_statut': stats_par_statut,
            'stats_par_mois': stats_par_mois,
        })
from rest_framework import viewsets, status, filters, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils.timezone import now
from .models import Proforma
from .serializers import ProformaSerializer, ProformaDetailSerializer, ProformaCreateSerializer

class ProformaViewSet(viewsets.ModelViewSet):
    """
    API endpoint pour gérer les proformas.
    """
    queryset = Proforma.objects.all().select_related(
        'offre', 'offre__client', 'offre__entity', 'created_by', 'updated_by'
    )
    serializer_class = ProformaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = {
        'statut': ['exact'],
        'date_creation': ['gte', 'lte'],
        'date_validation': ['gte', 'lte', 'isnull'],
        'offre__client': ['exact'],
        'offre__entity': ['exact'],
    }
    search_fields = ['reference', 'offre__reference', 'offre__client__nom', 'notes']
    ordering_fields = ['date_creation', 'date_validation', 'montant_ttc', 'reference']
    ordering = ['-date_creation']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update' or self.action == 'partial_update':
            return ProformaCreateSerializer
        elif self.action == 'retrieve':
            return ProformaDetailSerializer
        return ProformaDetailSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user, updated_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def validate(self, request, pk=None):
        """
        Valider une proforma
        """
        proforma = self.get_object()
        if proforma.statut != 'VALIDE':
            proforma.mark_as_validated(user=request.user)
            return Response({'status': 'Proforma validée'})
        return Response({'error': 'La proforma est déjà validée'}, 
                          status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def expire(self, request, pk=None):
        """
        Marquer une proforma comme expirée
        """
        proforma = self.get_object()
        if proforma.statut not in ['EXPIRE', 'ANNULE']:
            proforma.mark_as_expired(user=request.user)
            return Response({'status': 'Proforma marquée comme expirée'})
        return Response({'error': 'La proforma ne peut pas être marquée comme expirée'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """
        Changer le statut d'une proforma
        """
        proforma = self.get_object()
        new_status = request.data.get('status')
        
        # Vérifier si le statut est valide
        valid_statuses = [status for status, _ in Proforma.STATUS_CHOICES]
        if not new_status or new_status not in valid_statuses:
            return Response(
                {'error': f'Statut invalide. Les options valides sont : {", ".join(valid_statuses)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Appliquer des règles métier pour les changements de statut
        if new_status == 'VALIDE':
            proforma.mark_as_validated(user=request.user)
        elif new_status == 'EXPIRE':
            proforma.mark_as_expired(user=request.user)
        else:
            # Pour les autres statuts, changement simple
            old_status = proforma.statut
            proforma.statut = new_status
            
            # Mettre à jour les dates si nécessaire
            if new_status == 'ANNULE':
                # Vous pourriez ajouter une date d'annulation si vous le souhaitez
                pass
                
            proforma.updated_by = request.user
            proforma.save()
        
        return Response({
            'status': f'Statut changé de {proforma.statut} à {new_status}',
            'proforma': ProformaSerializer(proforma).data
        })
    
    @action(detail=True, methods=['post'], parser_classes=[parsers.MultiPartParser, parsers.FormParser])
    def upload_file(self, request, pk=None):
        """
        Uploader un fichier pour une proforma
        """
        proforma = self.get_object()
        
        if 'file' not in request.FILES:
            return Response(
                {'error': 'Aucun fichier fourni'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sauvegarder le fichier
        file = request.FILES['file']
        proforma.fichier = file
        proforma.updated_by = request.user
        proforma.save()
        
        return Response({
            'status': 'Fichier uploadé avec succès',
            'file_name': proforma.fichier.name,
            'file_url': request.build_absolute_uri(proforma.fichier.url) if proforma.fichier else None
        })
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Statistiques sur les proformas
        """
        total = self.get_queryset().count()
        validated = self.get_queryset().filter(statut='VALIDE').count()
        expired = self.get_queryset().filter(statut='EXPIRE').count()
        
        # Statistiques par mois (pour l'année en cours)
        current_year = now().year
        monthly_stats = []
        
        for month in range(1, 13):
            month_count = self.get_queryset().filter(
                date_creation__year=current_year,
                date_creation__month=month
            ).count()
            month_validated = self.get_queryset().filter(
                statut='VALIDE',
                date_validation__year=current_year,
                date_validation__month=month
            ).count()
            
            monthly_stats.append({
                'month': month,
                'count': month_count,
                'validated': month_validated
            })
        
        return Response({
            'total': total,
            'validated': validated,
            'expired': expired,
            'validation_rate': validated / total if total > 0 else 0,
            'monthly_stats': monthly_stats
        })
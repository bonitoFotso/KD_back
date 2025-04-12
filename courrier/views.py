from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Courrier, CourrierHistory
from .serializers import CourrierSerializer, CourrierListSerializer, CourrierHistorySerializer
from .filters import CourrierFilter


class CourrierViewSet(viewsets.ModelViewSet):
    """
    ViewSet pour les opérations CRUD sur les courriers.
    """
    queryset = Courrier.objects.all()
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = CourrierFilter
    search_fields = ['reference', 'objet', 'notes', 'client__nom', 'entite__nom']
    ordering_fields = ['date_creation', 'date_envoi', 'date_reception', 'reference', 'statut']
    ordering = ['-date_creation']

    def get_serializer_class(self):
        if self.action == 'list':
            return CourrierListSerializer
        return CourrierSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def mark_as_sent(self, request, pk=None):
        """Marquer un courrier comme envoyé"""
        courrier = self.get_object()
        date_str = request.data.get('date_envoi')
        
        try:
            if date_str:
                date_envoi = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date_envoi = timezone.now().date()
                
            courrier.mark_as_sent(date=date_envoi)
            return Response({'status': 'courrier marqué comme envoyé'}, 
                           status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_as_received(self, request, pk=None):
        """Marquer un courrier comme reçu"""
        courrier = self.get_object()
        date_str = request.data.get('date_reception')
        
        try:
            if date_str:
                date_reception = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            else:
                date_reception = timezone.now().date()
                
            courrier.mark_as_received(date=date_reception)
            return Response({'status': 'courrier marqué comme reçu'}, 
                           status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def mark_as_processed(self, request, pk=None):
        """Marquer un courrier comme traité"""
        courrier = self.get_object()
        courrier.mark_as_processed(user=request.user)
        return Response({'status': 'courrier marqué comme traité'})

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archiver un courrier"""
        courrier = self.get_object()
        courrier.archive()
        return Response({'status': 'courrier archivé'})

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Obtenir l'historique d'un courrier"""
        courrier = self.get_object()
        history = courrier.get_history()
        serializer = CourrierHistorySerializer(history, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Obtenir des statistiques sur les courriers"""
        total = Courrier.objects.count()
        entrants = Courrier.objects.filter(direction='IN').count()
        sortants = Courrier.objects.filter(direction='OUT').count()
        
        # Statistiques par statut
        status_stats = {}
        for status_code, status_name in Courrier.STATUS_CHOICES:
            status_stats[status_name] = Courrier.objects.filter(statut=status_code).count()
            
        # Statistiques par type de document
        type_stats = {}
        for type_code, type_name in Courrier.DOC_TYPES:
            type_stats[type_name] = Courrier.objects.filter(doc_type=type_code).count()
            
        # Courriers en retard
        overdue = Courrier.objects.filter(
            statut__in=['DRAFT', 'SENT', 'RECEIVED', 'PENDING']
        ).exclude(
            date_creation__gt=timezone.now().date() - timezone.timedelta(days=7)
        ).count()
            
        return Response({
            'total': total,
            'entrants': entrants,
            'sortants': sortants,
            'par_statut': status_stats,
            'par_type': type_stats,
            'en_retard': overdue,
        })


class CourrierHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet pour l'historique des courriers (lecture seule).
    """
    queryset = CourrierHistory.objects.all()
    serializer_class = CourrierHistorySerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['courrier', 'action', 'user']
    ordering_fields = ['date_action']
    ordering = ['-date_action']
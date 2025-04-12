import django_filters
from django.db.models import Q
from .models import Courrier


class CourrierFilter(django_filters.FilterSet):
    """Filtre pour les courriers"""
    date_min = django_filters.DateFilter(field_name='date_creation', lookup_expr='gte')
    date_max = django_filters.DateFilter(field_name='date_creation', lookup_expr='lte')
    
    envoi_min = django_filters.DateFilter(field_name='date_envoi', lookup_expr='gte')
    envoi_max = django_filters.DateFilter(field_name='date_envoi', lookup_expr='lte')
    
    reception_min = django_filters.DateFilter(field_name='date_reception', lookup_expr='gte')
    reception_max = django_filters.DateFilter(field_name='date_reception', lookup_expr='lte')
    
    est_urgent = django_filters.BooleanFilter(field_name='est_urgent')
    en_retard = django_filters.BooleanFilter(method='filter_en_retard')
    
    class Meta:
        model = Courrier
        fields = [
            'entite', 'client', 'doc_type', 'direction', 'statut', 'created_by', 'handled_by',
            'date_min', 'date_max', 'envoi_min', 'envoi_max', 'reception_min', 'reception_max',
            'est_urgent', 'en_retard'
        ]
    
    def filter_en_retard(self, queryset, name, value):
        # Si value est True, on filtre les courriers en retard
        if value:
            from django.utils import timezone
            seven_days_ago = timezone.now().date() - timezone.timedelta(days=7)
            
            # Courriers entrants reçus il y a plus de 7 jours et non traités
            entrants_en_retard = Q(
                direction='IN',
                date_reception__lt=seven_days_ago,
                statut__in=['RECEIVED', 'PENDING']
            )
            
            # Courriers sortants créés il y a plus de 7 jours et non envoyés
            sortants_en_retard = Q(
                direction='OUT',
                date_creation__lt=seven_days_ago,
                statut='DRAFT'
            )
            
            return queryset.filter(entrants_en_retard | sortants_en_retard)
        
        return queryset
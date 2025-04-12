import datetime
import django_filters
from django.db.models import Q
from django.utils.timezone import now

from .models import Affaire


class AffaireFilter(django_filters.FilterSet):
    """
    Filtre pour les affaires avec recherche avancée.
    """
    # Recherche par statut (multiple)
    statut = django_filters.MultipleChoiceFilter(
        choices=Affaire.STATUT_CHOICES
    )
    
    # Recherche par client
    client = django_filters.CharFilter(
        field_name='offre__client__nom',
        lookup_expr='icontains'
    )
    
    # Recherche par responsable
    responsable = django_filters.NumberFilter(
        field_name='responsable__id'
    )
    
    # Filtres par date
    date_debut_min = django_filters.DateFilter(
        field_name='date_debut',
        lookup_expr='gte'
    )
    date_debut_max = django_filters.DateFilter(
        field_name='date_debut',
        lookup_expr='lte'
    )
    date_fin_min = django_filters.DateFilter(
        field_name='date_fin_prevue',
        lookup_expr='gte'
    )
    date_fin_max = django_filters.DateFilter(
        field_name='date_fin_prevue',
        lookup_expr='lte'
    )
    
    # Filtres de montant
    montant_min = django_filters.NumberFilter(
        field_name='montant_total',
        lookup_expr='gte'
    )
    montant_max = django_filters.NumberFilter(
        field_name='montant_total',
        lookup_expr='lte'
    )
    
    # Filtre pour les affaires en retard
    en_retard = django_filters.BooleanFilter(method='filter_en_retard')
    
    # Filtre pour les affaires créées récemment
    recent = django_filters.BooleanFilter(method='filter_recent')
    
    class Meta:
        model = Affaire
        fields = [
            'statut', 'client', 'responsable',
            'date_debut_min', 'date_debut_max',
            'date_fin_min', 'date_fin_max',
            'montant_min', 'montant_max',
            'en_retard', 'recent'
        ]
    
    def filter_en_retard(self, queryset, name, value):
        """Filtre les affaires en retard."""
        if value:
            return queryset.filter(
                statut='EN_COURS',
                date_fin_prevue__lt=now()
            )
        return queryset
    
    def filter_recent(self, queryset, name, value):
        """Filtre les affaires créées dans les 30 derniers jours."""
        if value:
            date_limite = now() - datetime.timedelta(days=30)
            return queryset.filter(date_creation__gte=date_limite)
        return queryset
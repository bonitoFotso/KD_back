from django_filters import rest_framework as filters
from .models import Facture

class FactureFilter(filters.FilterSet):
    # Field names need to be different from the actual lookups
    # to avoid django-filter confusing them with model fields
    client_id = filters.NumberFilter(field_name='affaire__offre__client__id', lookup_expr='exact')
    entity_id = filters.NumberFilter(field_name='affaire__offre__entity__id', lookup_expr='exact')
    
    
    # Date filters
    date_creation_min = filters.DateTimeFilter(field_name='date_creation', lookup_expr='gte')
    date_creation_max = filters.DateTimeFilter(field_name='date_creation', lookup_expr='lte')
    
    date_emission_min = filters.DateTimeFilter(field_name='date_emission', lookup_expr='gte')
    date_emission_max = filters.DateTimeFilter(field_name='date_emission', lookup_expr='lte')
    date_emission_isnull = filters.BooleanFilter(field_name='date_emission', lookup_expr='isnull')
    
    date_echeance_min = filters.DateTimeFilter(field_name='date_echeance', lookup_expr='gte')
    date_echeance_max = filters.DateTimeFilter(field_name='date_echeance', lookup_expr='lte')
    date_echeance_isnull = filters.BooleanFilter(field_name='date_echeance', lookup_expr='isnull')
    
    date_paiement_min = filters.DateTimeFilter(field_name='date_paiement', lookup_expr='gte')
    date_paiement_max = filters.DateTimeFilter(field_name='date_paiement', lookup_expr='lte')
    date_paiement_isnull = filters.BooleanFilter(field_name='date_paiement', lookup_expr='isnull')
    
    # Amount filters
    montant_ttc_min = filters.NumberFilter(field_name='montant_ttc', lookup_expr='gte')
    montant_ttc_max = filters.NumberFilter(field_name='montant_ttc', lookup_expr='lte')
    
    # Status filters
    statut = filters.CharFilter(field_name='statut', lookup_expr='exact')
    statut_in = filters.CharFilter(field_name='statut', lookup_expr='in')
    
    class Meta:
        model = Facture
        # Don't include any fields that were defined explicitly above
        fields = {
            # Only include fields that are directly on the Facture model
            # and weren't already defined as explicit filter fields above
        }
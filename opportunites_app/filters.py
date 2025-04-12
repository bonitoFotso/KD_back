import django_filters
from django.db.models import Q
from django.utils.timezone import now, timedelta

from .models import Opportunite


class OpportuniteFilter(django_filters.FilterSet):
    """
    Filtres personnalisés pour les opportunités.
    """
    statut = django_filters.MultipleChoiceFilter(
        choices=Opportunite.STATUS_CHOICES,
        help_text="Filtrer par statut"
    )
    
    client_nom = django_filters.CharFilter(
        field_name="client__nom",
        lookup_expr="icontains",
        help_text="Filtrer par nom de client"
    )
    
    entity = django_filters.NumberFilter(
        field_name="entity__id",
        help_text="Filtrer par ID d'entité"
    )
    
    entity_code = django_filters.CharFilter(
        field_name="entity__code",
        lookup_expr="iexact",
        help_text="Filtrer par code d'entité"
    )
    
    montant_min = django_filters.NumberFilter(
        field_name="montant_estime",
        lookup_expr="gte",
        help_text="Montant estimé minimum"
    )
    
    montant_max = django_filters.NumberFilter(
        field_name="montant_estime",
        lookup_expr="lte",
        help_text="Montant estimé maximum"
    )
    
    probabilite_min = django_filters.NumberFilter(
        field_name="probabilite",
        lookup_expr="gte",
        help_text="Probabilité minimum"
    )
    
    probabilite_max = django_filters.NumberFilter(
        field_name="probabilite",
        lookup_expr="lte",
        help_text="Probabilité maximum"
    )
    
    date_creation_after = django_filters.DateTimeFilter(
        field_name="date_creation",
        lookup_expr="gte",
        help_text="Date de création après"
    )
    
    date_creation_before = django_filters.DateTimeFilter(
        field_name="date_creation",
        lookup_expr="lte",
        help_text="Date de création avant"
    )
    
    created_by = django_filters.NumberFilter(
        field_name="created_by__id",
        help_text="Filtrer par ID de créateur"
    )
    
    relance_status = django_filters.ChoiceFilter(
        choices=[
            ('required', 'Relance nécessaire'),
            ('upcoming', 'Relance planifiée'),
            ('none', 'Aucune relance')
        ],
        method='filter_relance_status',
        help_text="Statut de relance"
    )
    
    produit = django_filters.NumberFilter(
        field_name="produits__id",
        help_text="Filtrer par ID de produit"
    )
    
    produit_principal = django_filters.NumberFilter(
        field_name="produit_principal__id",
        help_text="Filtrer par ID de produit principal"
    )
    
    has_offre = django_filters.BooleanFilter(
        method='filter_has_offre',
        help_text="A des offres associées"
    )
    
    is_active = django_filters.BooleanFilter(
        method='filter_is_active',
        help_text="Opportunités actives (non gagnées/perdues)"
    )
    
    periode = django_filters.ChoiceFilter(
        choices=[
            ('today', "Aujourd'hui"),
            ('this_week', "Cette semaine"),
            ('this_month', "Ce mois"),
            ('this_quarter', "Ce trimestre"),
            ('this_year', "Cette année"),
        ],
        method='filter_periode',
        help_text="Période de création"
    )
    
    def filter_relance_status(self, queryset, name, value):
        """
        Filtre les opportunités selon leur statut de relance.
        """
        if value == 'required':
            return queryset.filter(
                relance__lte=now(),
                statut__in=['PROSPECT', 'QUALIFICATION', 'PROPOSITION', 'NEGOCIATION']
            )
        elif value == 'upcoming':
            return queryset.filter(
                relance__gt=now(),
                statut__in=['PROSPECT', 'QUALIFICATION', 'PROPOSITION', 'NEGOCIATION']
            )
        elif value == 'none':
            return queryset.filter(
                Q(relance__isnull=True) | Q(statut__in=['GAGNEE', 'PERDUE'])
            )
        return queryset
    
    def filter_has_offre(self, queryset, name, value):
        """
        Filtre les opportunités selon qu'elles ont des offres associées ou non.
        """
        if value:
            # Utilise une sous-requête pour les opportunités avec offres
            from offres_app.models import Offre
            opps_with_offres = Offre.objects.values_list('opportunite_id', flat=True).distinct()
            return queryset.filter(id__in=opps_with_offres)
        else:
            # Utilise une sous-requête pour les opportunités sans offres
            from offres_app.models import Offre
            opps_with_offres = Offre.objects.values_list('opportunite_id', flat=True).distinct()
            return queryset.exclude(id__in=opps_with_offres)
    
    def filter_is_active(self, queryset, name, value):
        """
        Filtre les opportunités actives (celles qui ne sont ni gagnées ni perdues).
        """
        if value:
            return queryset.exclude(statut__in=['GAGNEE', 'PERDUE'])
        else:
            return queryset.filter(statut__in=['GAGNEE', 'PERDUE'])
    
    def filter_periode(self, queryset, name, value):
        """
        Filtre les opportunités par période de création.
        """
        today = now().date()
        
        if value == 'today':
            return queryset.filter(date_creation__date=today)
        
        elif value == 'this_week':
            start_of_week = today - timedelta(days=today.weekday())  # Lundi
            end_of_week = start_of_week + timedelta(days=6)  # Dimanche
            return queryset.filter(
                date_creation__date__gte=start_of_week,
                date_creation__date__lte=end_of_week
            )
        
        elif value == 'this_month':
            return queryset.filter(
                date_creation__year=today.year,
                date_creation__month=today.month
            )
        
        elif value == 'this_quarter':
            current_quarter = ((today.month - 1) // 3) + 1
            first_month_of_quarter = 3 * current_quarter - 2
            last_month_of_quarter = 3 * current_quarter
            return queryset.filter(
                date_creation__year=today.year,
                date_creation__month__gte=first_month_of_quarter,
                date_creation__month__lte=last_month_of_quarter
            )
        
        elif value == 'this_year':
            return queryset.filter(date_creation__year=today.year)
        
        return queryset
    
    class Meta:
        model = Opportunite
        fields = [
            'statut', 'client', 'entity', 'contact', 'produit_principal',
            'created_by'
        ]
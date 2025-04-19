import django_filters
from django.db.models import Q
from django.utils import timezone

from .models import (
    Pays, Region, Ville, Categorie, Client, Site,
    Contact, Agreement, TypeInteraction, Interaction
)


class PaysFilter(django_filters.FilterSet):
    """Filtre pour le modèle Pays."""
    
    nom = django_filters.CharFilter(lookup_expr='icontains')
    code_iso = django_filters.CharFilter(lookup_expr='iexact')
    
    class Meta:
        model = Pays
        fields = ['nom', 'code_iso']


class RegionFilter(django_filters.FilterSet):
    """Filtre pour le modèle Region."""
    
    nom = django_filters.CharFilter(lookup_expr='icontains')
    pays = django_filters.ModelChoiceFilter(queryset=Pays.objects.all())
    pays_nom = django_filters.CharFilter(field_name='pays__nom', lookup_expr='icontains')
    
    class Meta:
        model = Region
        fields = ['nom', 'pays']


class VilleFilter(django_filters.FilterSet):
    """Filtre pour le modèle Ville."""
    
    nom = django_filters.CharFilter(lookup_expr='icontains')
    region = django_filters.ModelChoiceFilter(queryset=Region.objects.all())
    region_nom = django_filters.CharFilter(field_name='region__nom', lookup_expr='icontains')
    pays = django_filters.ModelChoiceFilter(field_name='region__pays', queryset=Pays.objects.all())
    pays_nom = django_filters.CharFilter(field_name='region__pays__nom', lookup_expr='icontains')
    population_min = django_filters.NumberFilter(field_name='population', lookup_expr='gte')
    population_max = django_filters.NumberFilter(field_name='population', lookup_expr='lte')
    
    class Meta:
        model = Ville
        fields = ['nom', 'region', 'population']


class CategorieFilter(django_filters.FilterSet):
    """Filtre pour le modèle Categorie."""
    
    nom = django_filters.ChoiceFilter(choices=Categorie.CATEGORIE_CHOICES)
    
    class Meta:
        model = Categorie
        fields = ['nom']


class ClientFilter(django_filters.FilterSet):
    """Filtre pour le modèle Client."""
    
    nom = django_filters.CharFilter(lookup_expr='icontains')
    c_num = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    telephone = django_filters.CharFilter(lookup_expr='icontains')
    secteur_activite = django_filters.CharFilter(lookup_expr='icontains')
    categorie = django_filters.ModelChoiceFilter(queryset=Categorie.objects.all())
    ville = django_filters.ModelChoiceFilter(queryset=Ville.objects.all())
    region = django_filters.ModelChoiceFilter(field_name='ville__region', queryset=Region.objects.all())
    pays = django_filters.ModelChoiceFilter(field_name='ville__region__pays', queryset=Pays.objects.all())
    est_client = django_filters.BooleanFilter()
    agree = django_filters.BooleanFilter()
    
    # Statut composite (client/prospect avec/sans agrément)
    statut = django_filters.CharFilter(method='filter_statut')
    
    # Filtres de dates
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    updated_after = django_filters.DateFilter(field_name='updated_at', lookup_expr='gte')
    updated_before = django_filters.DateFilter(field_name='updated_at', lookup_expr='lte')
    converted_after = django_filters.DateFilter(field_name='date_conversion_client', lookup_expr='gte')
    converted_before = django_filters.DateFilter(field_name='date_conversion_client', lookup_expr='lte')
    
    # Filtre par utilisateur
    created_by = django_filters.NumberFilter(field_name='created_by__id')
    updated_by = django_filters.NumberFilter(field_name='updated_by__id')
    
    class Meta:
        model = Client
        fields = [
            'nom', 'c_num', 'email', 'telephone', 'secteur_activite',
            'categorie', 'ville', 'est_client', 'agree'
        ]
    
    def filter_statut(self, queryset, name, value):
        """Filtre par statut (Client, Client Agréé, Prospect, Prospect Agréé)."""
        value = value.lower()
        
        if 'client' in value and 'agréé' in value:
            return queryset.filter(est_client=True).filter(
                Q(agree=True) | Q(entites_agreement__isnull=False)
            ).distinct()
        elif 'client' in value:
            return queryset.filter(est_client=True)
        elif 'prospect' in value and 'agréé' in value:
            return queryset.filter(est_client=False).filter(
                Q(agree=True) | Q(entites_agreement__isnull=False)
            ).distinct()
        elif 'prospect' in value:
            return queryset.filter(est_client=False)
        
        return queryset


class SiteFilter(django_filters.FilterSet):
    """Filtre pour le modèle Site."""
    
    nom = django_filters.CharFilter(lookup_expr='icontains')
    s_num = django_filters.CharFilter(lookup_expr='icontains')
    client = django_filters.ModelChoiceFilter(queryset=Client.objects.all())
    client_nom = django_filters.CharFilter(field_name='client__nom', lookup_expr='icontains')
    localisation = django_filters.CharFilter(lookup_expr='icontains')
    ville = django_filters.ModelChoiceFilter(queryset=Ville.objects.all())
    region = django_filters.ModelChoiceFilter(field_name='ville__region', queryset=Region.objects.all())
    pays = django_filters.ModelChoiceFilter(field_name='ville__region__pays', queryset=Pays.objects.all())
    
    # Filtres de dates
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    
    # Filtre par utilisateur
    created_by = django_filters.NumberFilter(field_name='created_by__id')
    
    class Meta:
        model = Site
        fields = ['nom', 's_num', 'client', 'localisation', 'ville']


class ContactFilter(django_filters.FilterSet):
    """Filtre pour le modèle Contact."""
    
    nom = django_filters.CharFilter(lookup_expr='icontains')
    prenom = django_filters.CharFilter(lookup_expr='icontains')
    email = django_filters.CharFilter(lookup_expr='icontains')
    telephone = django_filters.CharFilter(lookup_expr='icontains')
    mobile = django_filters.CharFilter(lookup_expr='icontains')
    poste = django_filters.CharFilter(lookup_expr='icontains')
    service = django_filters.CharFilter(lookup_expr='icontains')
    
    client = django_filters.ModelChoiceFilter(queryset=Client.objects.all())
    client_nom = django_filters.CharFilter(field_name='client__nom', lookup_expr='icontains')
    site = django_filters.ModelChoiceFilter(queryset=Site.objects.all())
    site_nom = django_filters.CharFilter(field_name='site__nom', lookup_expr='icontains')
    
    ville = django_filters.ModelChoiceFilter(queryset=Ville.objects.all())
    ville_nom = django_filters.CharFilter(field_name='ville__nom', lookup_expr='icontains')
    
    relance = django_filters.BooleanFilter()
    valide = django_filters.BooleanFilter()
    
    # Filtres de dates
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    envoi_after = django_filters.DateFilter(field_name='date_envoi', lookup_expr='gte')
    envoi_before = django_filters.DateFilter(field_name='date_envoi', lookup_expr='lte')
    
    class Meta:
        model = Contact
        fields = [
            'nom', 'prenom', 'email', 'telephone', 'mobile',
            'poste', 'service', 'client', 'site', 'ville',
            'relance', 'valide'
        ]


class AgreementFilter(django_filters.FilterSet):
    """Filtre pour le modèle Agreement."""
    
    client = django_filters.ModelChoiceFilter(queryset=Client.objects.all())
    client_nom = django_filters.CharFilter(field_name='client__nom', lookup_expr='icontains')
    entite = django_filters.NumberFilter(field_name='entite__id')
    entite_nom = django_filters.CharFilter(field_name='entite__nom', lookup_expr='icontains')
    
    est_actif = django_filters.BooleanFilter()
    statut_workflow = django_filters.ChoiceFilter(choices=Agreement.STATUT_CHOICES)
    
    # Filtres de dates
    debut_after = django_filters.DateFilter(field_name='date_debut', lookup_expr='gte')
    debut_before = django_filters.DateFilter(field_name='date_debut', lookup_expr='lte')
    fin_after = django_filters.DateFilter(field_name='date_fin', lookup_expr='gte')
    fin_before = django_filters.DateFilter(field_name='date_fin', lookup_expr='lte')
    statut_after = django_filters.DateFilter(field_name='date_statut', lookup_expr='gte')
    statut_before = django_filters.DateFilter(field_name='date_statut', lookup_expr='lte')
    
    # Filtre pour les agréments à renouveler
    a_renouveler = django_filters.BooleanFilter(method='filter_a_renouveler')
    
    # Filtre pour les agréments expirés
    expire = django_filters.BooleanFilter(method='filter_expire')
    
    class Meta:
        model = Agreement
        fields = [
            'client', 'entite', 'est_actif', 'statut_workflow'
        ]
    
    def filter_a_renouveler(self, queryset, name, value):
        """Filtre les agreements à renouveler dans les 30 prochains jours."""
        if not value:
            return queryset
            
        today = timezone.now().date()
        date_limite = today + timezone.timedelta(days=30)
        
        return queryset.filter(
            est_actif=True,
            date_fin__isnull=False,
            date_fin__lte=date_limite,
            date_fin__gte=today
        )
    
    def filter_expire(self, queryset, name, value):
        """Filtre les agreements expirés."""
        if not value:
            return queryset
            
        today = timezone.now().date()
        
        return queryset.filter(
            date_fin__isnull=False,
            date_fin__lt=today
        )


class TypeInteractionFilter(django_filters.FilterSet):
    """Filtre pour le modèle TypeInteraction."""
    
    nom = django_filters.CharFilter(lookup_expr='icontains')
    description = django_filters.CharFilter(lookup_expr='icontains')
    
    class Meta:
        model = TypeInteraction
        fields = ['nom', 'description']


class InteractionFilter(django_filters.FilterSet):
    """Filtre pour le modèle Interaction."""
    
    titre = django_filters.CharFilter(lookup_expr='icontains')
    notes = django_filters.CharFilter(lookup_expr='icontains')
    
    type_interaction = django_filters.ModelChoiceFilter(queryset=TypeInteraction.objects.all())
    contact = django_filters.ModelChoiceFilter(queryset=Contact.objects.all())
    client = django_filters.ModelChoiceFilter(queryset=Client.objects.all())
    entite = django_filters.NumberFilter(field_name='entite__id')
    
    est_rendez_vous = django_filters.BooleanFilter()
    relance_effectuee = django_filters.BooleanFilter()
    
    # Filtres de dates
    date_after = django_filters.DateTimeFilter(field_name='date', lookup_expr='gte')
    date_before = django_filters.DateTimeFilter(field_name='date', lookup_expr='lte')
    relance_after = django_filters.DateFilter(field_name='date_relance', lookup_expr='gte')
    relance_before = django_filters.DateFilter(field_name='date_relance', lookup_expr='lte')
    
    # Filtre pour les interactions à venir
    a_venir = django_filters.BooleanFilter(method='filter_a_venir')
    
    # Filtre pour les relances à faire
    relance_a_faire = django_filters.BooleanFilter(method='filter_relance_a_faire')
    
    class Meta:
        model = Interaction
        fields = [
            'titre', 'type_interaction', 'contact', 'client',
            'entite', 'est_rendez_vous', 'relance_effectuee'
        ]
    
    def filter_a_venir(self, queryset, name, value):
        """Filtre les interactions à venir."""
        if not value:
            return queryset
            
        now = timezone.now()
        return queryset.filter(date__gt=now)
    
    def filter_relance_a_faire(self, queryset, name, value):
        """Filtre les interactions avec des relances à faire."""
        if not value:
            return queryset
            
        today = timezone.now().date()
        return queryset.filter(
            date_relance__isnull=False,
            date_relance__lte=today,
            relance_effectuee=False
        )
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Offre, OffreProduit


class OffreProduitInline(admin.TabularInline):
    model = OffreProduit
    extra = 1
    fields = ('produit', 'prix_unitaire')
    
    #def get_fields(self, request, obj=None):
    #    """Rend montant readonly seulement quand l'objet existe déjà"""
    #    fields = super().get_fields(request, obj)
    #    if obj is None:  # Si c'est un nouvel objet
    #        return [f for f in fields if f != 'montant']
    #    return fields


@admin.register(Offre)
class OffreAdmin(admin.ModelAdmin):
    list_display = ('reference', 'client_link', 'statut', 'date_creation', 
                     'user', 'relance_status')
    list_filter = ('statut', 'entity', 'date_creation', 'user')
    search_fields = ('reference', 'client__nom', 'notes')
    readonly_fields = ('reference', 'date_creation', 'date_modification',)
    inlines = [OffreProduitInline]
    fieldsets = (
        (None, {
            'fields': ('reference', 'client', 'contact', 'entity', 'user')
        }),
        ('Informations', {
            'fields': ('statut', 'notes')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_modification', 'relance')
        }),
    )
    
    def client_link(self, obj):
        """Lien vers la fiche client"""
        url = reverse("admin:client_client_change", args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, obj.client.nom)
    client_link.short_description = 'Client'
    
    def relance_status(self, obj):
        """Affiche un indicateur visuel pour les relances"""
        if obj.statut in ['GAGNE', 'PERDU']:
            return format_html('<span style="color:gray;">—</span>')
        
        if obj.necessite_relance:
            return format_html('<span style="color:red;">⚠️ Relance due</span>')
        
        if obj.relance:
            days_left = (obj.relance - timezone.now()).days
            if days_left <= 2:
                return format_html('<span style="color:orange;">Relance dans {} jour(s)</span>', days_left)
            return format_html('<span style="color:green;">Relance dans {} jour(s)</span>', days_left)
        
        return format_html('<span style="color:gray;">Pas de relance</span>')
    relance_status.short_description = 'Relance'
    
    
    
    def get_queryset(self, request):
        """Optimise les requêtes en préchargeant les relations"""
        queryset = super().get_queryset(request)
        return queryset.select_related('client', 'contact', 'entity', 'user')
    
    def save_model(self, request, obj, form, change):
        """Affecte l'utilisateur actuel si non défini"""
        if not obj.user:
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(OffreProduit)
class OffreProduitAdmin(admin.ModelAdmin):
    list_display = ('offre', 'produit')
    list_filter = ('offre__statut',)
    search_fields = ('offre__reference', 'produit__nom')
    
    #def afficher_montant(self, obj):
    #    """Afficher le montant de façon sécurisée"""
    #    try:
    #        return obj.montant
    #    except (TypeError, ValueError):
    #        return "—"
    #afficher_montant.short_description = "Montant"
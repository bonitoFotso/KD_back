from django.contrib import admin
from django.db.models import Sum
from django.utils.html import format_html
from .models import Affaire, Facture


class FactureInline(admin.TabularInline):
    """Inline pour afficher les factures liées à une affaire."""
    model = Facture
    extra = 0
    fields = ['reference', 'date_emission', 'date_echeance', 'statut']
    readonly_fields = ['reference']
    can_delete = False
    show_change_link = True


@admin.register(Affaire)
class AffaireAdmin(admin.ModelAdmin):
    list_display = [
        'reference','id', 'get_titre', 'client_nom', 'montant_total', 'responsable',
        'statut_display',
    ]
    list_filter = ['statut', 'date_creation']
    search_fields = ['reference', 'offre__reference', 'offre__client__nom']
    readonly_fields = ['reference']
    fieldsets = [
        (None, {
            'fields': [
                'reference', 'offre', 'statut', 'montant_total', 'createur', 'modificateur', 'responsable'
            ]
        }),
        
        ('Dates', {
            'fields': [
                'date_debut'
            ],
            'classes': ['collapse']
        }),
    ]
    inlines = [FactureInline]
    date_hierarchy = 'date_debut'
    
    def get_queryset(self, request):
        """Optimise les requêtes en préchargeant les relations."""
        return super().get_queryset(request).select_related('offre', 'offre__client')
    
    def client_nom(self, obj):
        """Affiche le nom du client lié à l'offre."""
        return obj.offre.client.nom
    client_nom.short_description = 'Client'
    client_nom.admin_order_field = 'offre__client__nom'
    
    def get_titre(self, obj):
        """Retourne le titre de l'offre comme titre de l'affaire."""
        return obj.offre.reference
    get_titre.short_description = 'Titre'
    get_titre.admin_order_field = 'offre__titre'
    
    def statut_display(self, obj):
        """Affiche le statut avec un code couleur."""
        statut_colors = {
            'EN_COURS': 'blue',
            'TERMINEE': 'green',
            'ANNULEE': 'red',
            # Ajoutez d'autres statuts ici si nécessaire
        }
        color = statut_colors.get(obj.statut, 'black')
        return format_html('<span style="color:{};">{}</span>', color, obj.get_statut_display())
    statut_display.short_description = 'Statut'
    statut_display.admin_order_field = 'statut'
    
    def save_model(self, request, obj, form, change):
        """Génère une référence automatique si non définie."""
        if not obj.reference:
            # Génération d'une référence automatique basée sur l'année et un compteur
            import datetime
            year = datetime.date.today().year
            count = Affaire.objects.filter(
                date_creation__year=year
            ).count() + 1
            obj.reference = f'AFF-{year}-{count:04d}'
        super().save_model(request, obj, form, change)
    
    #def has_delete_permission(self, request, obj=None):
    #    """Désactive la suppression pour les affaires avec des factures."""
    #    if obj and obj.facture_set.exists():
    #        return False
    #    return super().has_delete_permission(request, obj)
from django.contrib import admin
from django.utils.html import format_html
from .models import Proforma

class ProformaAdmin(admin.ModelAdmin):
    list_display = ('reference', 'offre', 'get_client', 'get_entity', 'statut', 'montant_ttc', 'date_creation', 'date_validation')
    list_filter = ('statut', 'date_creation', 'date_validation', 'offre__entity', 'offre__client')
    search_fields = ('reference', 'offre__reference', 'offre__client__nom', 'notes')
    readonly_fields = ('reference', 'created_at', 'updated_at', 'sequence_number')
    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'offre', 'statut', 'sequence_number')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_validation', 'date_expiration')
        }),
        ('Montants', {
            'fields': ('montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc')
        }),
        ('Documents', {
            'fields': ('fichier',)
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_client(self, obj):
        return obj.offre.client.nom
    get_client.short_description = 'Client'
    get_client.admin_order_field = 'offre__client__nom'
    
    def get_entity(self, obj):
        return obj.offre.entity.code
    get_entity.short_description = 'Entité'
    get_entity.admin_order_field = 'offre__entity__code'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création (pas une modification)
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        # Empêcher la suppression des proformas validées
        if obj and obj.statut == 'VALIDE':
            return False
        return super().has_delete_permission(request, obj)
    
    def get_queryset(self, request):
        # Optimiser les requêtes en préchargeant les relations
        return super().get_queryset(request).select_related(
            'offre', 'offre__client', 'offre__entity', 'created_by', 'updated_by'
        )

admin.site.register(Proforma, ProformaAdmin)
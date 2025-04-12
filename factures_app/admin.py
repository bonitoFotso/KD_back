from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Facture

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('reference', 'affaire_link', 'client_display', 'montant_ttc_display', 
                    'statut_display', 'date_creation', 'date_echeance', 'est_en_retard_display')
    list_filter = ('statut', 'date_creation', 'date_emission', 'date_echeance', 'date_paiement')
    search_fields = ('reference', 'affaire__reference', 'affaire__offre__client__nom', 'notes')
    readonly_fields = ('reference', 'montant_tva', 'montant_ttc', 'created_at', 'updated_at', 'sequence_number',
                       'created_by', 'updated_by')
    fieldsets = (
        ('Informations générales', {
            'fields': ('reference', 'affaire', 'statut', 'sequence_number')
        }),
        ('Dates', {
            'fields': ('date_creation', 'date_emission', 'date_echeance', 'date_paiement')
        }),
        ('Montants', {
            'fields': ('montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc', 'montant_paye')
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
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'affaire', 'affaire__offre', 'affaire__offre__client', 'affaire__offre__entity',
            'created_by', 'updated_by'
        )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def affaire_link(self, obj):
        url = reverse('admin:affaires_app_affaire_change', args=[obj.affaire.id])
        return format_html('<a href="{}">{}</a>', url, obj.affaire.reference)
    affaire_link.short_description = 'Affaire'
    affaire_link.admin_order_field = 'affaire__reference'
    
    def client_display(self, obj):
        client = obj.affaire.offre.client
        url = reverse('admin:clients_app_client_change', args=[client.id])
        return format_html('<a href="{}">{}</a>', url, client.nom)
    client_display.short_description = 'Client'
    client_display.admin_order_field = 'affaire__offre__client__nom'
    
    def montant_ttc_display(self, obj):
        return f"{obj.montant_ttc:,.2f} XAF"
    montant_ttc_display.short_description = 'Montant TTC'
    montant_ttc_display.admin_order_field = 'montant_ttc'
    
    def statut_display(self, obj):
        statut_classes = {
            'BROUILLON': 'secondary',
            'EMISE': 'primary',
            'PAYEE': 'success',
            'ANNULEE': 'danger',
            'IMPAYEE': 'warning',
            'PARTIELLEMENT_PAYEE': 'info'
        }
        css_class = statut_classes.get(obj.statut, 'secondary')
        return format_html('<span class="badge badge-{}">{}</span>', css_class, obj.get_status_display())
    statut_display.short_description = 'Statut'
    statut_display.admin_order_field = 'statut'
    
    def est_en_retard_display(self, obj):
        if obj.est_en_retard():
            return format_html('<span class="badge badge-danger">En retard</span>')
        else:
            return ''
    est_en_retard_display.short_description = 'Retard'
    
    actions = ['mark_as_paid', 'mark_as_issued', 'mark_as_canceled']
    
    def mark_as_paid(self, request, queryset):
        count = 0
        for facture in queryset:
            if facture.statut not in ['PAYEE', 'ANNULEE']:
                facture.mark_as_paid(user=request.user)
                count += 1
        self.message_user(request, f"{count} facture(s) marquée(s) comme payée(s).")
    mark_as_paid.short_description = "Marquer les factures sélectionnées comme payées"
    
    def mark_as_issued(self, request, queryset):
        count = 0
        for facture in queryset:
            if facture.statut == 'BROUILLON':
                facture.date_emission = timezone.now()
                facture.updated_by = request.user
                facture.save()
                count += 1
        self.message_user(request, f"{count} facture(s) marquée(s) comme émise(s).")
    mark_as_issued.short_description = "Marquer les factures sélectionnées comme émises"
    
    def mark_as_canceled(self, request, queryset):
        count = 0
        for facture in queryset:
            if facture.statut not in ['ANNULEE']:
                facture.cancel(user=request.user)
                count += 1
        self.message_user(request, f"{count} facture(s) marquée(s) comme annulée(s).")
    mark_as_canceled.short_description = "Marquer les factures sélectionnées comme annulées"
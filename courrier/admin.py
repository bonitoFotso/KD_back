from django.contrib import admin
from django.utils.html import format_html
from .models import Courrier, CourrierHistory

class CourrierHistoryInline(admin.TabularInline):
    model = CourrierHistory
    readonly_fields = ('date_action', 'action', 'user', 'details')
    extra = 0
    can_delete = False
    
    def has_add_permission(self, request, obj=None):
        return False

@admin.register(Courrier)
class CourrierAdmin(admin.ModelAdmin):
    list_display = ('reference', 'doc_type', 'client', 'direction', 'statut', 
                   'date_creation', 'est_urgent', 'created_by', 'get_status_color')
    list_filter = ('direction', 'statut', 'doc_type', 'est_urgent', 'date_creation')
    search_fields = ('reference', 'objet', 'client__nom', 'notes')
    readonly_fields = ('reference', 'date_creation')
    inlines = [CourrierHistoryInline]
    date_hierarchy = 'date_creation'
    
    fieldsets = (
        ('Informations principales', {
            'fields': (('reference', 'entite'), ('doc_type', 'direction'), 
                      'client', 'objet', 'statut')
        }),
        ('Dates', {
            'fields': (('date_creation', 'date_envoi', 'date_reception'),)
        }),
        ('Traitement', {
            'fields': (('created_by', 'handled_by'), 'est_urgent', 'notes')
        }),
        ('Document', {
            'fields': ('fichier',)
        }),
    )

    def get_status_color(self, obj):
        colors = {
            'DRAFT': '#gray',
            'SENT': '#28a745',
            'RECEIVED': '#17a2b8',
            'ARCHIVED': '#6c757d',
            'PENDING': '#ffc107',
            'PROCESSED': '#007bff',
        }
        return format_html(
            '<span style="color: {};">{}</span>',
            colors.get(obj.statut, 'black'),
            obj.get_statut_display()
        )
    get_status_color.short_description = 'Statut'

    actions = ['mark_as_sent', 'mark_as_received', 'mark_as_processed', 'mark_as_archived']

    def mark_as_sent(self, request, queryset):
        for obj in queryset:
            obj.mark_as_sent()
    mark_as_sent.short_description = "Marquer comme envoyé"

    def mark_as_received(self, request, queryset):
        for obj in queryset:
            obj.mark_as_received()
    mark_as_received.short_description = "Marquer comme reçu"

    def mark_as_processed(self, request, queryset):
        for obj in queryset:
            obj.mark_as_processed(request.user)
    mark_as_processed.short_description = "Marquer comme traité"

    def mark_as_archived(self, request, queryset):
        for obj in queryset:
            obj.archive()
    mark_as_archived.short_description = "Archiver"

@admin.register(CourrierHistory)
class CourrierHistoryAdmin(admin.ModelAdmin):
    list_display = ('courrier', 'action', 'date_action', 'user')
    list_filter = ('action', 'date_action', 'user')
    search_fields = ('courrier__reference', 'details')
    readonly_fields = ('courrier', 'action', 'date_action', 'user', 'details')

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
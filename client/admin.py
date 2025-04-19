from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count
from django.utils import timezone

# Import des modèles
from .models import (
    Pays, Region, Ville, Categorie, Client, Site, 
    Contact, Agreement, TypeInteraction, Interaction
)


@admin.register(Pays)
class PaysAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_iso', 'nombre_de_regions')
    search_fields = ('nom', 'code_iso')
    ordering = ('nom',)


class RegionInline(admin.TabularInline):
    model = Region
    extra = 0


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pays', 'nombre_de_villes')
    list_filter = ('pays',)
    search_fields = ('nom', 'pays__nom')
    ordering = ('pays', 'nom')


class VilleInline(admin.TabularInline):
    model = Ville
    extra = 0


@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'region', 'pays_display', 'population')
    list_filter = ('region__pays', 'region')
    search_fields = ('nom', 'region__nom', 'region__pays__nom')
    ordering = ('region__pays__nom', 'region__nom', 'nom')
    
    def pays_display(self, obj):
        return obj.region.pays.nom
    pays_display.short_description = 'Pays'
    pays_display.admin_order_field = 'region__pays__nom'


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom', 'get_display_name')
    
    def get_display_name(self, obj):
        return obj.get_nom_display()
    get_display_name.short_description = 'Description'


class SiteInline(admin.TabularInline):
    model = Site
    extra = 0
    fields = ('nom', 'localisation', 'ville', 's_num')


class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0
    fields = ('nom', 'prenom', 'email', 'telephone', 'poste')


class AgreementInline(admin.TabularInline):
    model = Agreement
    extra = 0
    fields = ('entite', 'date_debut', 'date_fin', 'statut_workflow', 'est_actif')


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'c_num', 'adresse', 'email', 'telephone', 'ville', 'quartier', 'bp')
        }),
        ('Informations commerciales', {
            'fields': ('secteur_activite', 'categorie', 'matricule', 'entite')
        }),
        ('Statut', {
            'fields': ('est_client', 'date_conversion_client', 'agree')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )
    
    list_display = ('nom', 'c_num', 'statut_display', 'secteur_activite', 
                    'ville_complete', 'created_at',)
    list_filter = ('est_client', 'agree', 'categorie', 'ville__region__pays', 
                   'ville__region', 'created_at')
    search_fields = ('nom', 'c_num', 'email', 'telephone', 'matricule',
                     'ville__nom', 'ville__region__nom', 'ville__region__pays__nom')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [SiteInline, ContactInline, AgreementInline]
    date_hierarchy = 'created_at'
    
    def statut_display(self, obj):
        statut = obj.statut
        if 'Agréé' in statut:
            color = 'green'
        elif 'Client' in statut:
            color = 'blue'
        else:
            color = 'orange'
        return format_html('<span style="color: {};">{}</span>', color, statut)
    statut_display.short_description = 'Statut'
    
    def ville_complete(self, obj):
        if obj.ville:
            return f"{obj.ville.nom}, {obj.ville.region.nom}, {obj.ville.region.pays.nom}"
        return "-"
    ville_complete.short_description = 'Localisation'
    
    #def nombre_sites(self, obj):
    #    count = obj.sites.count()
    #    url = reverse('admin:app_site_changelist') + f'?client__id__exact={obj.id}'
    #    return format_html('<a href="{}">{}</a>', url, count)
    #nombre_sites.short_description = 'Sites'
    
    #def nombre_contacts(self, obj):
    #    count = obj.contacts.count()
    #    url = reverse('admin:app_contact_changelist') + f'?client__id__exact={obj.id}'
    #    return format_html('<a href="{}">{}</a>', url, count)
    #nombre_contacts.short_description = 'Contacts'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 'client_link', 's_num', 'ville', 'created_at')
    list_filter = ('ville__region__pays', 'ville__region', 'ville', 'created_at')
    search_fields = ('nom', 's_num', 'client__nom', 'localisation', 'ville__nom')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    inlines = [ContactInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('nom', 'client', 's_num')
        }),
        ('Localisation', {
            'fields': ('localisation', 'ville', 'description')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )
    
    def client_link(self, obj):
        url = reverse('admin:app_client_change', args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, obj.client.nom)
    client_link.short_description = 'Client'
    client_link.admin_order_field = 'client__nom'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('nom_complet', 'email', 'telephone', 'client_link', 'site_link', 
                    'poste', 'service', 'created_at')
    list_filter = ('valide', 'relance', 'service', 'client__est_client', 
                   'ville__region__pays', 'created_at')
    search_fields = ('nom', 'prenom', 'email', 'telephone', 'mobile', 
                     'client__nom', 'site__nom', 'poste')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'mobile')
        }),
        ('Informations professionnelles', {
            'fields': ('poste', 'service', 'role_achat')
        }),
        ('Rattachements', {
            'fields': ('client', 'site')
        }),
        ('Adresse', {
            'fields': ('adresse', 'ville', 'quartier', 'bp')
        }),
        ('Suivi commercial', {
            'fields': ('date_envoi', 'relance', 'source', 'valide', 'notes')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )
    
    def nom_complet(self, obj):
        if obj.prenom:
            return f"{obj.nom} {obj.prenom}"
        return obj.nom
    nom_complet.short_description = 'Nom'
    
    def client_link(self, obj):
        if obj.client:
            url = reverse('admin:app_client_change', args=[obj.client.id])
            return format_html('<a href="{}">{}</a>', url, obj.client.nom)
        return "-"
    client_link.short_description = 'Client'
    
    def site_link(self, obj):
        if obj.site:
            url = reverse('admin:app_site_change', args=[obj.site.id])
            return format_html('<a href="{}">{}</a>', url, obj.site.nom)
        return "-"
    site_link.short_description = 'Site'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Agreement)
class AgreementAdmin(admin.ModelAdmin):
    list_display = ('client_link', 'entite_display', 'date_debut', 'date_fin', 
                    'est_actif', 'statut_workflow_display', 'date_statut')
    list_filter = ('est_actif', 'statut_workflow', 'date_debut', 'date_fin')
    search_fields = ('client__nom', 'entite__nom', 'commentaires')
    date_hierarchy = 'date_statut'
    
    fieldsets = (
        ('Parties concernées', {
            'fields': ('client', 'entite')
        }),
        ('Période de validité', {
            'fields': ('date_debut', 'date_fin', 'est_actif')
        }),
        ('Statut', {
            'fields': ('statut_workflow', 'date_statut', 'commentaires')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('cree_par', 'modifie_par')
        }),
    )
    
    def client_link(self, obj):
        url = reverse('admin:app_client_change', args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, obj.client.nom)
    client_link.short_description = 'Client'
    client_link.admin_order_field = 'client__nom'
    
    def entite_display(self, obj):
        return obj.entite.nom
    entite_display.short_description = 'Entité'
    entite_display.admin_order_field = 'entite__nom'
    
    def statut_workflow_display(self, obj):
        colors = {
            "DEMANDE": "orange",
            "EN_REVUE": "blue",
            "VALIDE": "green",
            "REJETE": "red",
            "EXPIRE": "grey",
            "RENOUVELLEMENT": "purple",
        }
        color = colors.get(obj.statut_workflow, "black")
        return format_html('<span style="color: {};">{}</span>', 
                          color, obj.get_statut_workflow_display())
    statut_workflow_display.short_description = 'Statut'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.cree_par = request.user
        obj.modifie_par = request.user
        super().save_model(request, obj, form, change)


@admin.register(TypeInteraction)
class TypeInteractionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'description', 'couleur_display', 'nombre_interactions')
    search_fields = ('nom', 'description')
    
    def couleur_display(self, obj):
        if obj.couleur:
            return format_html('<span style="color: {}; font-size: 20px;">■</span> {}', 
                              obj.couleur, obj.couleur)
        return "-"
    couleur_display.short_description = 'Couleur'
    
    def nombre_interactions(self, obj):
        count = Interaction.objects.filter(type_interaction=obj).count()
        return count
    nombre_interactions.short_description = 'Nb interactions'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        queryset = queryset.annotate(interactions_count=Count('interaction'))
        return queryset


@admin.register(Interaction)
class InteractionAdmin(admin.ModelAdmin):
    list_display = ('date_format', 'type_interaction_display', 'titre', 
                   'contact_link', 'client_link', 'est_rendez_vous', 
                   'relance_status')
    list_filter = ('type_interaction', 'est_rendez_vous', 'relance_effectuee', 
                  'date', 'client')
    search_fields = ('titre', 'notes', 'contact__nom', 'contact__prenom', 
                    'client__nom', 'entite__nom')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
    date_hierarchy = 'date'
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('date', 'type_interaction', 'titre', 'notes')
        }),
        ('Participants', {
            'fields': ('contact', 'client', 'entite')
        }),
        ('Rendez-vous', {
            'fields': ('est_rendez_vous', 'duree_minutes')
        }),
        ('Relance', {
            'fields': ('date_relance', 'relance_effectuee')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        }),
    )
    
    def date_format(self, obj):
        return obj.date.strftime('%d/%m/%Y %H:%M')
    date_format.short_description = 'Date'
    date_format.admin_order_field = 'date'
    
    def type_interaction_display(self, obj):
        if obj.type_interaction.couleur:
            return format_html('<span style="color: {};">{}</span>', 
                              obj.type_interaction.couleur, obj.type_interaction.nom)
        return obj.type_interaction.nom
    type_interaction_display.short_description = 'Type'
    type_interaction_display.admin_order_field = 'type_interaction__nom'
    
    def contact_link(self, obj):
        url = reverse('admin:app_contact_change', args=[obj.contact.id])
        return format_html('<a href="{}">{}</a>', url, str(obj.contact))
    contact_link.short_description = 'Contact'
    contact_link.admin_order_field = 'contact__nom'
    
    def client_link(self, obj):
        url = reverse('admin:app_client_change', args=[obj.client.id])
        return format_html('<a href="{}">{}</a>', url, obj.client.nom)
    client_link.short_description = 'Client'
    client_link.admin_order_field = 'client__nom'
    
    def relance_status(self, obj):
        if not obj.date_relance:
            return "-"
        elif obj.relance_effectuee:
            return format_html('<span style="color: green;">Effectuée</span>')
        else:
            today = timezone.now().date()
            if obj.date_relance < today:
                return format_html('<span style="color: red;">En retard ({})</span>', 
                                  obj.date_relance.strftime('%d/%m/%Y'))
            elif (obj.date_relance - today).days <= 3:
                return format_html('<span style="color: orange;">À faire ({})</span>', 
                                  obj.date_relance.strftime('%d/%m/%Y'))
            else:
                return format_html('<span style="color: blue;">Planifiée ({})</span>', 
                                  obj.date_relance.strftime('%d/%m/%Y'))
    relance_status.short_description = 'Relance'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


# Personnalisation de l'interface d'administration
# admin.site.site_header = "Administration du CRM"
# admin.site.site_title = "Portail d'administration CRM"
# admin.site.index_title = "Bienvenue dans l'interface d'administration du CRM"

# admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Categorie, Pays, Region, Ville, Client, Site, Contact

@admin.register(Pays)
class PaysAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_iso', 'nombre_de_regions')
    search_fields = ('nom', 'code_iso')
    ordering = ('nom',)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('nom', 'pays', 'nombre_de_villes')
    list_filter = ('pays',)
    search_fields = ('nom', 'pays__nom')
    ordering = ('pays', 'nom')

@admin.register(Ville)
class VilleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'get_region', 'get_pays')
    list_filter = ('region__pays', 'region')
    search_fields = ('nom', 'region__nom', 'region__pays__nom')
    ordering = ('nom',)

    def get_region(self, obj):
        return obj.region.nom
    get_region.short_description = 'Région'
    get_region.admin_order_field = 'region__nom'

    def get_pays(self, obj):
        return obj.region.pays.nom
    get_pays.short_description = 'Pays'
    get_pays.admin_order_field = 'region__pays__nom'

class ContactInline(admin.TabularInline):
    model = Contact
    extra = 0
    fields = ('nom', 'prenom', 'email', 'telephone', 'mobile', 'poste')

class SiteInline(admin.TabularInline):
    model = Site
    extra = 0
    fields = ('nom', 's_num', 'localisation', 'ville')
    
@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('nom',)
    search_fields = ('nom',)
    ordering = ('nom',)
    

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ('nom', 'c_num', 'email','is_client' , 'telephone', 'ville', 'secteur_activite', 'categorie', 
                   'agreer', 'agreement_fournisseur', 'get_contacts_count', 'get_created_at')
    list_filter = ('ville__region__pays', 'ville__region', 'ville', 'agreer', 
                  'agreement_fournisseur', 'created_at')
    search_fields = ('nom', 'c_num', 'email', 'telephone', 'matricule')
    readonly_fields = ('c_num', 'created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 'c_num', 'email', 'telephone')
        }),
        ('Localisation', {
            'fields': ('address', 'bp', 'quartier', 'ville')
        }),
        ('Informations commerciales', {
            'fields': ('secteur_activite', 'matricule', 'agreer', 'agreement_fournisseur', 'entite', 'is_client', 'categorie')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    inlines = [ContactInline, SiteInline]

    def get_contacts_count(self, obj):
        return obj.contacts.count()
    get_contacts_count.short_description = 'Contacts'

    def get_created_at(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M")
    get_created_at.short_description = 'Créé le'
    get_created_at.admin_order_field = 'created_at'

    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ('nom', 's_num', 'client', 'ville', 'get_created_at')
    list_filter = ('ville__region__pays', 'ville__region', 'ville', 'created_at')
    search_fields = ('nom', 's_num', 'client__nom', 'localisation')
    readonly_fields = ('s_num', 'created_at', 'updated_at', 'created_by', 'updated_by')
    fieldsets = (
        ('Informations principales', {
            'fields': ('nom', 's_num', 'client', 'description')
        }),
        ('Localisation', {
            'fields': ('localisation', 'ville')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )

    def get_created_at(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M")
    get_created_at.short_description = 'Créé le'
    get_created_at.admin_order_field = 'created_at'

    def save_model(self, request, obj, form, change):
        if not change:  # Si c'est une création
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'telephone', 'mobile', 'client', 
                   'poste', 'service', 'relance', 'get_created_at')
    list_filter = ('client', 'service', 'relance', 'ville', 'created_at')
    search_fields = ('nom', 'prenom', 'email', 'telephone', 'mobile', 'client__nom')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('nom', 'prenom', 'email', 'telephone', 'mobile')
        }),
        ('Informations professionnelles', {
            'fields': ('client', 'poste', 'service', 'role_achat')
        }),
        ('Localisation', {
            'fields': ('adresse', 'ville', 'quartier', 'bp')
        }),
        ('Suivi', {
            'fields': ('date_envoi', 'relance', 'notes')
        }),
        ('Audit', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_created_at(self, obj):
        return obj.created_at.strftime("%d/%m/%Y %H:%M")
    get_created_at.short_description = 'Créé le'
    get_created_at.admin_order_field = 'created_at'
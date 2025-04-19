# Description: Fichier de configuration de l'interface d'administration de l'application document
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from api.user.models import User
from .models import (
    ContentType, Entity, Departement, Product, 
    Rapport, Formation, Participant, AttestationFormation,
     AuditLog, UserActionLog
)

@admin.register(UserActionLog)
class UserActionLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'user', 'action_type', 'content_type', 'object_id', 'field_name']
    list_filter = ['action_type', 'content_type', 'user']
    search_fields = ['user__username', 'field_name', 'description']
    readonly_fields = ['timestamp', 'user', 'action_type', 'content_type', 'object_id', 
                      'field_name', 'old_value', 'new_value', 'description', 'ip_address']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
        
    def has_change_permission(self, request, obj=None):
        return False
        
    def has_delete_permission(self, request, obj=None):
        return False

from django.contrib import admin

@admin.register(ContentType)
class ContentTypeAdmin(admin.ModelAdmin):
   list_display = ['app_label', 'model']
   list_filter = ['app_label']
   search_fields = ['app_label', 'model']
   ordering = ['app_label', 'model']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
   list_display = ['timestamp', 'user', 'action', 'content_type', 'object_repr']
   list_filter = ['action', 'content_type', 'user']
   search_fields = ['user__username', 'object_repr']
   readonly_fields = ['timestamp', 'user', 'action', 'content_type', 'object_id', 'object_repr', 'changes']
   date_hierarchy = 'timestamp'

   def has_add_permission(self, request):
       return False
       
   def has_change_permission(self, request, obj=None):
       return False
       
   def has_delete_permission(self, request, obj=None):
       return False

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'departement', 'is_staff', 'is_active')
    list_filter = ('departement', 'is_active', 'is_staff')
    search_fields = ('username', 'email')
    ordering = ('username',)



class BaseModelAdmin(admin.ModelAdmin):
    readonly_fields = ('created_by', 'updated_by', 'created_at', 'updated_at')

@admin.register(Entity)
class EntityAdmin(BaseModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')


@admin.register(Departement)
class DepartementAdmin(BaseModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')

@admin.register(Product)
class ProductAdmin(BaseModelAdmin):
    list_display = ('code', 'name', 'departement')
    list_filter = ('departement',)
    search_fields = ('code', 'name')




@admin.register(Rapport)
class RapportAdmin(BaseModelAdmin):
    list_display = ('reference', 'affaire', 'produit', 'statut')
    list_filter = ('statut', 'entity', )
    search_fields = ('reference', 'affaire__reference')
    readonly_fields = ('reference',)

@admin.register(Formation)
class FormationAdmin(BaseModelAdmin):
    list_display = ('titre', 'client', 'affaire', 'date_debut', 'date_fin')
    list_filter = ('client',)
    search_fields = ('titre', 'client__nom')

@admin.register(Participant)
class ParticipantAdmin(BaseModelAdmin):
    list_display = ('nom', 'prenom', 'email', 'formation')
    list_filter = ('formation',)
    search_fields = ('nom', 'prenom', 'email')


@admin.register(AttestationFormation)
class AttestationFormationAdmin(admin.ModelAdmin):
   list_display = ('reference', 'affaire', 'formation', 'participant', 'date_creation')
   list_filter = ('formation', 'participant', 'affaire')
   search_fields = ('reference', 'participant__nom', 'formation__titre')
   readonly_fields = ('reference',)
   
   fieldsets = (
       ('Informations générales', {
           'fields': ('affaire', 'formation', 'participant')
       }),
       ('Détails', {
           'fields': ('details_formation', 'reference')
       })
   )


# Personnalisation de l'interface d'administration
admin.site.site_header = "Gestion des Documents"
admin.site.site_title = "Administration des Documents"
admin.site.index_title = "Tableau de bord"
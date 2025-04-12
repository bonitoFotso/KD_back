from rest_framework import permissions, status
from rest_framework.response import Response
from django.utils.translation import gettext_lazy as _
from rest_framework.exceptions import PermissionDenied
import logging

logger = logging.getLogger(__name__)

from enum import Enum
from typing import List, Dict, Any


class Action(Enum):
    LIST = 'list'
    RETRIEVE = 'retrieve'
    CREATE = 'create'
    UPDATE = 'update'
    DELETE = 'delete'

class PermissionBuilder:
    MODELS = [
        'Rapport', 'Offre', 'Proforma', 'Formation', 
        'Participant', 'AttestationFormation', 'Site', 
        'Client', 'Facture', 'Affaire', 
        'Category', 'Product', 'Entity'
    ]

    @staticmethod
    def base_permissions() -> Dict[str, List[str]]:
        return {
            'global': [Action.LIST.value, Action.RETRIEVE.value],
            'department': [Action.CREATE.value, Action.UPDATE.value],
            'admin': [Action.DELETE.value]
        }

    @classmethod
    def generate_permissions(cls) -> Dict[str, Any]:
        base_actions = cls.base_permissions()
        
        departments = {
            'Inspection': {
                'allowed_models': cls.MODELS,
                'actions': {
                    model: base_actions['global'] + 
                           (base_actions['department'] if model in ['Rapport', 'Offre', 'Proforma'] else [])
                    for model in cls.MODELS
                }
            },
            'Formation': {
                'allowed_models': cls.MODELS,
                'actions': {
                    model: base_actions['global'] + 
                           (base_actions['department'] if model in ['Formation', 'Participant', 'AttestationFormation'] else [])
                    for model in cls.MODELS
                }
            },
            'IT': {
                'allowed_models': cls.MODELS,
                'actions': {
                    model: base_actions['global'] + 
                           (base_actions['department'] if model in ['Client', 'Site'] else [])
                    for model in cls.MODELS
                }
            },
            'HR': {
                'allowed_models': cls.MODELS,
                'actions': {
                    model: base_actions['global'] + 
                           (base_actions['department'] if model in ['Client', 'Site'] else [])
                    for model in cls.MODELS
                }
            },
            'Admin': {
                'allowed_models': cls.MODELS,
                'actions': {
                    model: base_actions['global'] + 
                           base_actions['department'] + 
                           base_actions['admin']
                    for model in cls.MODELS
                }
            }
        }

        return departments

# Generate the permissions
department_permissions = PermissionBuilder.generate_permissions()
class DepartmentPermission(permissions.BasePermission):
   def get_error_response(self, user, action, model_name):
    error_messages = {
        'not_found': {
            'message': _("Accès refusé - Département {dept} non autorisé"),
            'detail': _("Votre département n'a pas les permissions nécessaires. Contactez votre administrateur."),
            'code': 'DEPT_DENIED',
            'status': status.HTTP_403_FORBIDDEN
        },
        'model_denied': {
            'message': _("Accès refusé - Module {model}"), 
            'detail': _("Vous n'avez pas accès à ce module. Contactez votre administrateur."),
            'code': 'MODEL_DENIED',
            'status': status.HTTP_403_FORBIDDEN
        },
        'action_denied': {
            'message': _("Action non autorisée - {action} sur {model}"),
            'detail': _("Vous n'avez pas les droits pour effectuer cette action. Contactez votre administrateur."),
            'code': 'ACTION_DENIED', 
            'status': status.HTTP_403_FORBIDDEN
        }
    }

    
    
    dept_perms = department_permissions.get(user.departement)
    
    if not user.departement or not dept_perms:
        error = error_messages['not_found']
        raise PermissionDenied(detail={
            'message': error['message'].format(dept=user.departement),
            'detail': error['detail'],
            'code': error['code']
        })
    
    allowed_models = dept_perms['allowed_models']
    if model_name not in allowed_models:
        error = error_messages['model_denied']
        raise PermissionDenied(detail={
            'message': error['message'].format(model=model_name),
            'detail': error['detail'], 
            'code': error['code']
        })
    
    error = error_messages['action_denied']
    raise PermissionDenied(detail={
        'message': error['message'].format(action=action, model=model_name),
        'detail': error['detail'],
        'code': error['code']
    })

   def has_permission(self, request, view):
       user = request.user
       action = view.action
       model_name = view.__class__.__name__.replace('ViewSet', '')

       if user.is_superuser:
           return True

       

       dept_perms = department_permissions.get(user.departement)

       if not dept_perms:
           self.get_error_response(user, action, model_name)

       allowed_models = dept_perms['allowed_models']
       if model_name not in allowed_models:
           self.get_error_response(user, action, model_name)

       allowed_actions = dept_perms['actions'].get(model_name, [])
       if action not in allowed_actions:
           self.get_error_response(user, action, model_name)

       return True

   def has_object_permission(self, request, view, obj):
       return self.has_permission(request, view)
   
   
from rest_framework import permissions


class OpportunitePermission(permissions.BasePermission):
    """
    Permissions pour les opportunités:
    - Tous les utilisateurs authentifiés peuvent voir les opportunités
    - Seuls les créateurs et les administrateurs peuvent modifier/supprimer
    - Seuls les administrateurs et commerciaux peuvent créer
    """
    
    def has_permission(self, request, view):
        # Vérifier si l'utilisateur est authentifié
        if not request.user.is_authenticated:
            return False
            
        # Pour la création, vérifier si l'utilisateur est admin ou commercial
        if view.action == 'create':
            return (
                request.user.is_staff or 
                request.user.groups.filter(name='Commerciaux').exists()
            )
            
        # Pour les autres actions (list, retrieve), autoriser tout utilisateur authentifié
        return True
    
    def has_object_permission(self, request, view, obj):
        # Lecture autorisée pour tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True
            
        # Vérifier si l'utilisateur est le créateur ou un admin
        if request.user.is_staff:
            return True
            
        # Vérifier si l'utilisateur est le créateur
        if obj.created_by == request.user:
            return True
            
        # Vérifier si l'utilisateur est un manager
        if request.user.groups.filter(name='Managers').exists():
            return True
            
        # Si la méthode est une transition d'état et que l'utilisateur est un commercial
        if view.action in ['qualifier', 'proposer', 'negocier', 'gagner', 'perdre', 'creer_offre']:
            return request.user.groups.filter(name='Commerciaux').exists()
            
        return False
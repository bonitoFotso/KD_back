from rest_framework import permissions


class OpportunitePermission(permissions.BasePermission):
    """
    Permissions personnalisées pour les opportunités:
    
    - Les superutilisateurs ont tous les droits
    - Un utilisateur peut voir les opportunités des entités auxquelles il est associé
    - Un utilisateur peut modifier/supprimer uniquement les opportunités qu'il a créées
      ou s'il a les permissions appropriées
    """
    
    def has_permission(self, request, view):
        # Vérifier si l'utilisateur est authentifié
        if not request.user or not request.user.is_authenticated:
            return False
        
        # Les superutilisateurs ont tous les droits
        if request.user.is_superuser:
            return True
        
        # Pour la méthode POST, l'utilisateur doit avoir la permission 'add_opportunite'
        if request.method == 'POST' and not request.user.has_perm('opportunites_app.add_opportunite'):
            return False
        
        # Pour les méthodes de liste et de lecture, pas de restrictions supplémentaires
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Pour les autres méthodes, nous vérifions au niveau de l'objet
        return True
    
    def has_object_permission(self, request, view, obj):
        # Les superutilisateurs ont tous les droits
        if request.user.is_superuser:
            return True
        
        # Les méthodes de lecture sont autorisées si l'utilisateur appartient à l'entité
        if request.method in permissions.SAFE_METHODS:
            # Vérifier si l'utilisateur est associé à l'entité de l'opportunité
            user_entities = request.user.entities.all()
            return obj.entity in user_entities
        
        # Pour la mise à jour, l'utilisateur doit être le créateur
        # ou avoir la permission 'change_opportunite'
        if request.method in ['PUT', 'PATCH']:
            if obj.created_by == request.user:
                return True
            return request.user.has_perm('opportunites_app.change_opportunite')
        
        # Pour la suppression, l'utilisateur doit être le créateur
        # ou avoir la permission 'delete_opportunite'
        if request.method == 'DELETE':
            if obj.created_by == request.user:
                return True
            return request.user.has_perm('opportunites_app.delete_opportunite')
        
        # Pour les actions personnalisées (transitions d'état)
        if view.action in ['qualifier', 'proposer', 'negocier', 'gagner', 'perdre', 'creer_offre']:
            # Vérifier les permissions spécifiques
            action_permissions = {
                'qualifier': 'opportunites_app.can_qualify',
                'proposer': 'opportunites_app.can_propose',
                'negocier': 'opportunites_app.can_negotiate',
                'gagner': 'opportunites_app.can_win',
                'perdre': 'opportunites_app.can_lose',
                'creer_offre': 'opportunites_app.can_create_offre'
            }
            
            # Le créateur a toujours le droit d'effectuer ces actions
            if obj.created_by == request.user:
                return True
            
            # Sinon, vérifier les permissions spécifiques
            permission = action_permissions.get(view.action)
            if permission:
                return request.user.has_perm(permission)
        
        return False
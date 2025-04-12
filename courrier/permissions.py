from rest_framework import permissions

class IsCourrierManager(permissions.BasePermission):
    """
    Permission pour les gestionnaires de courriers.
    """
    def has_permission(self, request, view):
        # Tous les utilisateurs authentifiés peuvent lister et voir
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Vérifier si l'utilisateur a le rôle approprié pour les opérations d'écriture
        return request.user.groups.filter(name='Gestionnaire_Courrier').exists() or request.user.is_staff
    
    def has_object_permission(self, request, view, obj):
        # Permettre l'accès en lecture à tous les utilisateurs authentifiés
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Seuls les gestionnaires et admins peuvent modifier/supprimer
        if request.user.groups.filter(name='Gestionnaire_Courrier').exists() or request.user.is_staff:
            return True
            
        # L'utilisateur qui a créé le courrier peut le modifier s'il est encore en brouillon
        if obj.created_by == request.user and obj.statut == 'DRAFT':
            return True
            
        return False
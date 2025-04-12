from rest_framework import permissions


class AffairePermission(permissions.BasePermission):
    """
    Permissions pour les opérations sur les affaires.
    
    Règles appliquées:
    - Tous les utilisateurs authentifiés peuvent lister et visualiser les affaires
    - Seuls les utilisateurs ayant la permission 'add_affaire' peuvent créer des affaires
    - Seuls le créateur, le responsable ou un utilisateur avec la permission 'change_affaire'
      peuvent modifier une affaire
    - Seuls les utilisateurs avec la permission 'delete_affaire' peuvent supprimer une affaire
    """
    
    def has_permission(self, request, view):
        """Vérifie les permissions au niveau de la vue."""
        # Les utilisateurs non authentifiés n'ont aucun accès
        if not request.user.is_authenticated:
            return False
        
        # Pour les actions lecture seule, tous les utilisateurs authentifiés ont accès
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Pour créer une affaire, l'utilisateur doit avoir la permission
        if view.action == 'create':
            return request.user.has_perm('affaires_app.add_affaire')
        
        # Pour modifier un statut, l'utilisateur doit avoir la permission
        if view.action == 'change_statut':
            return request.user.has_perm('affaires_app.change_statut_affaire')
        
        # Pour générer une facture
        if view.action == 'generer_facture':
            return request.user.has_perm('document.add_facture')
        
        # Pour marquer un rapport comme terminé
        if view.action == 'marquer_rapport_termine':
            return request.user.has_perm('document.change_rapport')
        
        # Pour les autres actions, on vérifie au niveau de l'objet
        return True
    
    def has_object_permission(self, request, view, obj):
        """Vérifie les permissions au niveau de l'objet."""
        # Les méthodes sécurisées (GET, HEAD, OPTIONS) sont autorisées pour tous
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Le créateur de l'affaire a tous les droits dessus
        if obj.createur == request.user:
            return True
        
        # Le responsable de l'affaire peut la modifier
        if obj.responsable == request.user:
            return True
        
        # Pour la modification, il faut la permission adéquate
        if view.action in ['update', 'partial_update', 'change_statut']:
            return request.user.has_perm('affaires_app.change_affaire')
        
        # Pour la suppression, il faut la permission adéquate
        if view.action == 'destroy':
            return request.user.has_perm('affaires_app.delete_affaire')
        
        # Pour les actions spécifiques
        if view.action == 'generer_facture':
            return request.user.has_perm('document.add_facture')
        
        if view.action == 'marquer_rapport_termine':
            return request.user.has_perm('document.change_rapport')
        
        # Par défaut, on refuse l'accès
        return False
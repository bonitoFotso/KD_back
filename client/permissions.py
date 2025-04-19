from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les propriétaires d'un objet à l'éditer.
    Les utilisateurs authentifiés peuvent lire tous les objets, mais seuls les
    créateurs peuvent les modifier/supprimer.
    """

    def has_object_permission(self, request, view, obj):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True

        # Les permissions d'écriture ne sont accordées qu'au créateur de l'objet
        # On vérifie si l'objet a un attribut 'created_by' ou 'cree_par'
        if hasattr(obj, 'created_by'):
            return obj.created_by == request.user
        elif hasattr(obj, 'cree_par'):
            return obj.cree_par == request.user
        
        # Si l'objet n'a pas d'attribut de propriété, on n'autorise pas
        return False


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les super-utilisateurs à modifier.
    Les utilisateurs authentifiés peuvent lire tous les objets, mais seuls les
    administrateurs peuvent les modifier/créer/supprimer.
    """

    def has_permission(self, request, view):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True

        # Les permissions d'écriture ne sont accordées qu'aux administrateurs
        return request.user and request.user.is_superuser


class IsAdminUserOrReadOnly(permissions.BasePermission):
    """
    Permission personnalisée pour autoriser seulement les utilisateurs du staff à modifier.
    Les utilisateurs authentifiés peuvent lire tous les objets, mais seuls les
    membres du staff peuvent les modifier/créer/supprimer.
    """

    def has_permission(self, request, view):
        # Les permissions de lecture sont autorisées pour toute requête
        if request.method in permissions.SAFE_METHODS:
            return True

        # Les permissions d'écriture ne sont accordées qu'aux membres du staff
        return request.user and request.user.is_staff
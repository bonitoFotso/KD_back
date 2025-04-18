from api.user.serializers import UserSerializer
from api.user.models import User
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from rest_framework import mixins


class UserViewSet(
    viewsets.GenericViewSet,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.ListModelMixin,  # Ajout du mixin pour la fonctionnalité de liste
):
    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    error_message = {"success": False, "msg": "Error updating user"}

    def get_queryset(self):
        """
        Définit le queryset pour la liste des utilisateurs.
        Les superutilisateurs peuvent voir tous les utilisateurs.
        Les utilisateurs normaux ne peuvent voir que leur propre profil.
        """
        user = self.request.user
        if user.is_superuser:
            return User.objects.all()
        return User.objects.filter(id=user.id)

    def list(self, request, *args, **kwargs):
        """
        Liste tous les utilisateurs (pour les superusers) ou seulement
        l'utilisateur connecté (pour les utilisateurs normaux)
        """
        queryset = self.get_queryset()

        # Possibilité de filtrer par département si le paramètre est fourni
        department = request.query_params.get("department", None)
        if department:
            queryset = queryset.filter(departement=department)

        serializer = self.get_serializer(queryset, many=True)
        return Response(
            {"success": True, "users": serializer.data}, status=status.HTTP_200_OK
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", True)
        instance = User.objects.get(id=request.data.get("userID"))
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        if getattr(instance, "_prefetched_objects_cache", None):
            instance._prefetched_objects_cache = {}
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        user_id = request.data.get("userID")
        if not user_id:
            raise ValidationError(self.error_message)
        if self.request.user.pk != int(user_id) and not self.request.user.is_superuser:
            raise ValidationError(self.error_message)
        self.update(request)
        return Response({"success": True}, status.HTTP_200_OK)

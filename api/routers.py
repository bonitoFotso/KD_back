from api.authentication.viewsets import (
    RegisterViewSet,
    LoginViewSet,
    ActiveSessionViewSet,
    LogoutViewSet,
)
from rest_framework import routers
from api.user.viewsets import UserViewSet

router = routers.SimpleRouter(trailing_slash=False)

# Route pour l'édition d'utilisateur
router.register(r"edit", UserViewSet, basename="user-edit")

# Nouvelle route pour la liste des utilisateurs
router.register(r"users", UserViewSet, basename="user-list")

# Routes d'authentification
router.register(r"register", RegisterViewSet, basename="register")
router.register(r"login", LoginViewSet, basename="login")
router.register(r"checkSession", ActiveSessionViewSet, basename="check-session")
router.register(r"logout", LogoutViewSet, basename="logout")

urlpatterns = [
    *router.urls,
]
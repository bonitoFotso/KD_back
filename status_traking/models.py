from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
import json
from datetime import datetime
from django.conf import settings

User = settings.AUTH_USER_MODEL

class StatusChange(models.Model):
    """Modèle pour enregistrer l'historique des changements de statut"""
    content_type = models.ForeignKey('contenttypes.ContentType', on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    
    ancien_statut = models.CharField(max_length=30)
    nouveau_statut = models.CharField(max_length=30)
    date_changement = models.DateTimeField(auto_now_add=True)
    utilisateur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    commentaire = models.TextField(blank=True)
    
    # Métadonnées additionnelles (stockées en JSON)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        ordering = ['-date_changement']
        verbose_name = "Historique de changement de statut"
        verbose_name_plural = "Historique des changements de statut"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['date_changement']),
            models.Index(fields=['nouveau_statut']),
            models.Index(fields=['utilisateur']),
        ]
    
    def __str__(self):
        return f"{self.ancien_statut} → {self.nouveau_statut} par {self.utilisateur} le {self.date_changement}"

    def get_metadata_value(self, key, default=None):
        """Récupère une valeur des métadonnées de façon sécurisée"""
        return self.metadata.get(key, default)
    
    def get_date_specifique(self):
        """Récupère la date spécifique des métadonnées si elle existe"""
        date_str = self.get_metadata_value('date_specifique')
        if not date_str:
            return None
        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None


class StatusTrackingModel(models.Model):
    """
    Classe abstraite pour la gestion des statuts et le suivi des modifications.
    Cette classe peut être étendue par tout modèle nécessitant un suivi des statuts.
    """
    # Statut actuel
    statut = models.CharField(
        max_length=30,
        verbose_name="Statut"
    )
    
    # Dates importantes
    date_creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    date_modification = models.DateTimeField(auto_now=True, verbose_name="Dernière modification")
    
    # Utilisateurs
    createur = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="%(class)s_crees",
        verbose_name="Créé par"
    )
    modificateur = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name="%(class)s_modifies",
        verbose_name="Modifié par"
    )
    
    # Dates spécifiques pour les changements de statut importants
    dates_statuts = models.JSONField(default=dict, blank=True, verbose_name="Dates des statuts")
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['date_creation']),
            models.Index(fields=['createur']),
            models.Index(fields=['modificateur']),
        ]
    
    def get_status_choices(self):
        """
        Cette méthode doit être implémentée par les classes enfants
        pour retourner les choix de statut valides.
        """
        raise NotImplementedError("Les classes enfants doivent implémenter get_status_choices()")
    
    def get_date_for_status(self, statut):
        """
        Récupère la date enregistrée pour un statut donné et la convertit en objet datetime
        
        Args:
            statut (str): Le statut dont on veut récupérer la date
            
        Returns:
            datetime or None: La date du changement de statut ou None si non trouvée
        """
        if not self.dates_statuts:
            return None
            
        date_str = self.dates_statuts.get(statut)
        if not date_str:
            return None
            
        try:
            return datetime.fromisoformat(date_str)
        except (ValueError, TypeError):
            return None
    
    def validate_date_specifique(self, date_specifique):
        """
        Valide que la date spécifique est cohérente
        
        Args:
            date_specifique (datetime): La date à valider
            
        Raises:
            ValidationError: Si la date est incohérente
        """
        if not date_specifique:
            return
            
        # Vérifier que la date n'est pas dans le futur
        if date_specifique > timezone.now():
            raise ValidationError("La date spécifique ne peut pas être dans le futur")
            
        # Vérifier que la date n'est pas antérieure à la date de création
        if hasattr(self, 'date_creation') and self.date_creation and date_specifique < self.date_creation:
            raise ValidationError("La date spécifique ne peut pas être antérieure à la date de création")
    
    @transaction.atomic
    def set_status(self, nouveau_statut, user=None, date_specifique=None, commentaire="", metadata=None):
        """
        Change le statut de l'objet avec traçabilité
        
        Args:
            nouveau_statut (str): Le nouveau statut
            user (User): L'utilisateur effectuant le changement
            date_specifique (datetime): Date spécifique pour le changement de statut
            commentaire (str): Commentaire sur le changement
            metadata (dict): Métadonnées additionnelles pour le changement
            
        Returns:
            bool: True si le statut a été changé, False sinon
            
        Raises:
            ValidationError: Si le statut ou la date spécifique est invalide
        """
        # Valider le statut
        status_choices = [choice[0] for choice in self.get_status_choices()]
        if nouveau_statut not in status_choices:
            raise ValidationError(f"Statut invalide. Choix possibles: {', '.join(status_choices)}")
        
        # Valider la date spécifique
        if date_specifique:
            self.validate_date_specifique(date_specifique)
        
        # Enregistrer l'ancien statut
        ancien_statut = self.statut
        
        # Si le statut n'a pas changé, ne rien faire
        if ancien_statut == nouveau_statut:
            return False
        
        # Mettre à jour le statut
        self.statut = nouveau_statut
        
        # Mettre à jour l'utilisateur modificateur
        if user:
            self.modificateur = user
        
        # Enregistrer la date du changement de statut dans le dictionnaire dates_statuts
        if self.dates_statuts is None:
            self.dates_statuts = {}
        
        # Utiliser la date spécifique si fournie, sinon la date actuelle
        date_statut = date_specifique or timezone.now()
        
        # Convertir en chaîne pour le stockage JSON
        date_str = date_statut.isoformat()
        self.dates_statuts[nouveau_statut] = date_str
        
        # Préparer les champs à mettre à jour
        update_fields = ['statut', 'dates_statuts', 'modificateur']
        
        # Sauvegarder les modifications
        try:
            self.save(update_fields=update_fields)
        except Exception as e:
            # Journaliser l'erreur et relever l'exception
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la mise à jour du statut: {str(e)}")
            raise
        
        # Créer une entrée dans l'historique (dans la même transaction)
        content_type = ContentType.objects.get_for_model(self)
        
        if metadata is None:
            metadata = {}
        
        # Ajouter la date spécifique dans les métadonnées si elle est fournie
        if date_specifique:
            metadata['date_specifique'] = date_specifique.isoformat()
        
        # Ajouter d'autres métadonnées utiles
        metadata['ip_address'] = getattr(user, 'last_login_ip', None)
        metadata['timestamp'] = timezone.now().isoformat()
        
        try:
            StatusChange.objects.create(
                content_type=content_type,
                object_id=self.pk,
                ancien_statut=ancien_statut,
                nouveau_statut=nouveau_statut,
                utilisateur=user,
                commentaire=commentaire,
                metadata=metadata
            )
        except Exception as e:
            # Journaliser l'erreur et relever l'exception pour annuler la transaction
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Erreur lors de la création de l'historique de statut: {str(e)}")
            raise
        
        return True
    
    def get_status_history(self):
        """
        Récupère l'historique complet des changements de statut pour cet objet
        
        Returns:
            QuerySet: Liste des changements de statut ordonnés du plus récent au plus ancien
        """
        content_type = ContentType.objects.get_for_model(self)
        return StatusChange.objects.filter(
            content_type=content_type,
            object_id=self.pk
        ).select_related('utilisateur').order_by('-date_changement')
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour gérer la création initiale du statut
        et éviter les problèmes de récursion
        """
        # Si c'est une nouvelle instance (sans ID), enregistrer le statut initial
        is_new = self.pk is None
        
        # Vérifier si c'est un appel récursif pour update_fields=['dates_statuts']
        is_dates_statuts_update = (
            kwargs.get('update_fields') is not None and 
            set(kwargs.get('update_fields')) == {'dates_statuts'}
        )
        
        # Appeler la méthode save parent
        super().save(*args, **kwargs)
        
        # Pour une nouvelle instance, créer la première entrée dans l'historique
        if is_new and hasattr(self, 'createur') and self.createur and not is_dates_statuts_update:
            with transaction.atomic():
                content_type = ContentType.objects.get_for_model(self)
                StatusChange.objects.create(
                    content_type=content_type,
                    object_id=self.pk,
                    ancien_statut="",
                    nouveau_statut=self.statut,
                    utilisateur=self.createur,
                    commentaire="Création"
                )
                
                # Initialiser dates_statuts avec la date de création pour le statut initial
                if self.dates_statuts is None or not self.dates_statuts:
                    self.dates_statuts = {
                        self.statut: self.date_creation.isoformat()
                    }
                    # Mise à jour sécurisée pour éviter la récursion
                    type(self).objects.filter(pk=self.pk).update(dates_statuts=self.dates_statuts)

from django.db import models, transaction
from django.core.validators import RegexValidator
from django.db.models import Max
from django.utils.timezone import now
from django_fsm import FSMField, transition
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from client.models import AuditableMixin, Client, Contact



from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

User = settings.AUTH_USER_MODEL

class UserActionLog(models.Model):
    """
    Model for tracking user actions on any model in the system.
    Records the user, action type, affected model, field changed, and old/new values.
    """
    ACTION_TYPES = (
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('STATUS_CHANGE', 'Changement de statut'),
    )
    
    # Who performed the action
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='action_logs')
    
    # When the action occurred
    timestamp = models.DateTimeField(default=timezone.now)
    
    # Type of action performed
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    
    # Generic relation to the affected model
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # The specific field that was changed (if applicable)
    field_name = models.CharField(max_length=100, blank=True, null=True)
    
    # Old and new values
    old_value = models.TextField(blank=True, null=True)
    new_value = models.TextField(blank=True, null=True)
    
    # Additional information or context
    description = models.TextField(blank=True, null=True)
    
    # IP address of the user (optional)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Journal d'action utilisateur"
        verbose_name_plural = "Journal des actions utilisateurs"
        indexes = [
            models.Index(fields=['content_type', 'object_id']),
            models.Index(fields=['user']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.user} a {self.action_type} {self.content_type} (ID: {self.object_id}) le {self.timestamp}"
class Entity(AuditableMixin, models.Model):
    code = models.CharField(
        max_length=3,
        unique=True,
        validators=[RegexValidator(regex='^[A-Z]{3}$')]
    )
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name




class Category(AuditableMixin, models.Model):
    code = models.CharField(
        max_length=3,
        validators=[RegexValidator(regex='^[A-Z]{3}$')]
    )  # INS, FOR, QHS, etc.
    name = models.CharField(max_length=50)
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name="categoris")

    def __str__(self):
        return self.name


class Product(AuditableMixin, models.Model):
    code = models.CharField(
        max_length=4,
        validators=[RegexValidator(regex=r'^(VTE|EC)\d+$')]
    )
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="produits")

    def __str__(self):
        return self.name


from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
import json
from django.conf import settings



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
    
    def __str__(self):
        return f"{self.ancien_statut} → {self.nouveau_statut} par {self.utilisateur} le {self.date_changement}"


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
    
    def get_status_choices(self):
        """
        Cette méthode doit être implémentée par les classes enfants
        pour retourner les choix de statut valides.
        """
        raise NotImplementedError("Les classes enfants doivent implémenter get_status_choices()")
    
    def get_date_for_status(self, statut):
        """Récupère la date enregistrée pour un statut donné"""
        if not self.dates_statuts:
            return None
        return self.dates_statuts.get(statut)
    
    def set_status(self, nouveau_statut, user=None, date_specifique=None, commentaire="", metadata=None):
        """
        Change le statut de l'objet avec traçabilité
        
        Args:
            nouveau_statut (str): Le nouveau statut
            user (User): L'utilisateur effectuant le changement
            date_specifique (datetime): Date spécifique pour le changement de statut
            commentaire (str): Commentaire sur le changement
            metadata (dict): Métadonnées additionnelles pour le changement
        """
        from django.contrib.contenttypes.models import ContentType
        
        # Valider le statut
        status_choices = [choice[0] for choice in self.get_status_choices()]
        if nouveau_statut not in status_choices:
            raise ValidationError(f"Statut invalide. Choix possibles: {', '.join(status_choices)}")
        
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
        
        # Sauvegarder les modifications
        self.save(update_fields=['statut', 'modificateur', 'dates_statuts'])
        
        # Créer une entrée dans l'historique
        content_type = ContentType.objects.get_for_model(self)
        
        if metadata is None:
            metadata = {}
        
        # Ajouter la date spécifique dans les métadonnées si elle est fournie
        if date_specifique:
            metadata['date_specifique'] = date_specifique.isoformat()
        
        StatusChange.objects.create(
            content_type=content_type,
            object_id=self.pk,
            ancien_statut=ancien_statut,
            nouveau_statut=nouveau_statut,
            utilisateur=user,
            commentaire=commentaire,
            metadata=metadata
        )
        
        return True
    
    def get_status_history(self):
        """Récupère l'historique complet des changements de statut pour cet objet"""
        from django.contrib.contenttypes.models import ContentType
        
        content_type = ContentType.objects.get_for_model(self)
        return StatusChange.objects.filter(
            content_type=content_type,
            object_id=self.pk
        ).order_by('-date_changement')
    
    def save(self, *args, **kwargs):
        """Surcharge de la méthode save pour gérer la création initiale du statut"""
        # Si c'est une nouvelle instance (sans ID), enregistrer le statut initial
        is_new = self.pk is None
        
        # Appeler la méthode save parent
        super().save(*args, **kwargs)
        
        # Pour une nouvelle instance, créer la première entrée dans l'historique
        if is_new and hasattr(self, 'createur') and self.createur:
            from django.contrib.contenttypes.models import ContentType
            
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
            if self.dates_statuts is None:
                self.dates_statuts = {}
                
            self.dates_statuts[self.statut] = self.date_creation.isoformat()
            self.save(update_fields=['dates_statuts'])


# Exemple d'utilisation avec le modèle Offre
class AuditLog(models.Model):
    ACTION_TYPES = [
        ('CREATE', 'Création'),
        ('UPDATE', 'Modification'),
        ('DELETE', 'Suppression'),
        ('VALIDATE', 'Validation'),
        ('REFUSE', 'Refus'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_TYPES)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=100)
    object_repr = models.CharField(max_length=200)
    changes = models.JSONField(null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']



class Document(models.Model):
    STATUTS = [
        ('BROUILLON', 'Brouillon'),
        ('ENVOYE', 'Envoyé'),
        ('VALIDE', 'Validé'),
        ('REFUSE', 'Refusé'),
    ]
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name='%(class)ss')
    reference = models.CharField(max_length=50, unique=True, editable=False)
    client = models.ForeignKey(
        Client, 
        on_delete=models.CASCADE,
        related_name='%(class)ss'   # Cela créera automatiquement des related_names uniques
    )
    date_creation = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(choices=STATUTS, default='BROUILLON', max_length=20)
    doc_type = models.CharField(
        max_length=3,
        validators=[RegexValidator(regex='^[A-Z]{3}$')]
    )  # PRF, FAC, etc.
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True, blank=True, related_name='%(class)ss'
    )
    sequence_number = models.IntegerField()
    fichier = models.FileField(upload_to='documents/', blank=True, null=True)

    def log_action(self, action, user, changes=None):
        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=ContentType.objects.get_for_model(self),
            object_id=str(self.pk),
            object_repr=str(self),
            changes=changes
        )

    class Meta:
        abstract = True




class Rapport(Document):
    affaire = models.ForeignKey('affaires_app.Affaire', on_delete=models.CASCADE, related_name="rapports")
    #site = models.ForeignKey(Site, on_delete=models.CASCADE)
    produit = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="rapports")
    numero = models.CharField(max_length=10, blank=True, null=True)


    def save(self, *args, **kwargs):
        if not self.numero:
            self.numero = f"RAP{self.affaire.offre.client.c_num}/{self.produit.code}/{self.pk}"
        if not self.reference:
            if not self.sequence_number:
                last_sequence = Rapport.objects.filter(
                    entity=self.entity,
                    doc_type='RAP',
                    date_creation__year=now().year,
                    date_creation__month=now().month
                ).aggregate(Max('sequence_number'))['sequence_number__max']
                self.sequence_number = (last_sequence or 0) + 1
            total_rapports_client = Rapport.objects.filter(client=self.affaire.offre.client).count() + 1
            total_category_rapports = Rapport.objects.filter(client=self.affaire.offre.client,produit__category=self.produit.category).count() + 1
            date = self.date_creation or now()
            self.reference = f"{self.entity.code}/RAP/{self.client.c_num}/{self.affaire.reference}/{total_category_rapports}/{self.produit.code}/{total_rapports_client}/{self.sequence_number:04d}"
        super().save(*args, **kwargs)


class Formation(AuditableMixin, models.Model):
    titre = models.CharField(max_length=255)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="formations")
    affaire = models.ForeignKey('affaires_app.Affaire', on_delete=models.CASCADE, related_name="formations")
    rapport = models.ForeignKey(Rapport, on_delete=models.CASCADE, related_name="formation")
    date_debut = models.DateTimeField(blank=True, null=True)
    date_fin = models.DateTimeField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.titre} - {self.client.nom}"


class Participant(AuditableMixin, models.Model):
    nom = models.CharField(max_length=255)
    prenom = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=15, blank=True, null=True)
    fonction = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='participants/', blank=True, null=True)
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="participants")

    def __str__(self):
        return f"{self.nom} {self.prenom}"


class AttestationFormation(Document):
    affaire = models.ForeignKey('affaires_app.Affaire', on_delete=models.CASCADE, related_name="attestations")
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="attestations")
    participant = models.ForeignKey(Participant, on_delete=models.CASCADE, related_name= "attestation")
    details_formation = models.TextField()
    rapport = models.ForeignKey(Rapport, on_delete=models.CASCADE, related_name="attestations")

    def save(self, *args, **kwargs):
        if not self.reference:
            if not self.sequence_number:
                last_sequence = AttestationFormation.objects.filter(
                    entity=self.entity,
                    client=self.affaire.client,
                    formation=self.formation,
                    doc_type='ATT',
                    date_creation__year=now().year,
                    date_creation__month=now().month
                ).aggregate(Max('sequence_number'))['sequence_number__max']
                self.sequence_number = (last_sequence or 0) + 1
            total_attestations_client = AttestationFormation.objects.filter(client=self.client).count() + 1
            date = self.date_creation or now()
            self.reference = f"{self.entity.code}/ATT/{self.client.c_num}/{str(date.year)[-2:]}{date.month:02d}{date.day:02d}/{self.affaire.reference}/{total_attestations_client}/{self.formation.pk}/{self.participant.pk}/{self.sequence_number:04d}"
        super().save(*args, **kwargs)


class DocumentPermission:
    pass



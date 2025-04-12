from django.db import models
from django.utils import timezone
from django.conf import settings


def generate_reference(prefix, doc_type, client_ref, direction='OUT'):
    """
    Génère une référence unique pour un document.
    Format : [PREFIX]-[DIRECTION]-[TYPE]-[DATE]-[CLIENT_REF]-[SEQUENCE]
    """
    # Date au format YYMMDD
    date_str = timezone.now().strftime("%y%m%d")
    
    # Direction (IN/OUT)
    dir_code = direction[:3].upper()
    
    # Générer la référence de base
    base_ref = f"{prefix}-{dir_code}-{doc_type}-{date_str}-{client_ref}"
    
    # Obtenir l'année et le mois actuels pour les filtres
    current_year = timezone.now().year
    current_month = timezone.now().month
    
    # Filtrer par type de document, entité, et période (mois en cours)
    # Cela permet une numérotation par mois et par type
    last_ref = Courrier.objects.filter(
        reference__startswith=f"{prefix}-{dir_code}-{doc_type}",
        date_creation__year=current_year,
        date_creation__month=current_month
    ).order_by('-reference').first()
    
    sequence = 1  # Commence à 1
    if last_ref:
        # Extraire le numéro de séquence et l'incrémenter
        try:
            last_sequence = int(last_ref.reference.split('-')[-1])
            sequence = last_sequence + 1
        except (ValueError, IndexError):
            # En cas d'erreur dans le parsing, garder sequence = 1
            pass
    
    # Formater le numéro de séquence avec des zéros à gauche
    sequence_str = f"{sequence:03d}"
    
    # Retourner la référence complète
    return f"{base_ref}-{sequence_str}"
class Courrier(models.Model):
    DIRECTION_CHOICES = [
        ('IN', 'Entrant'),
        ('OUT', 'Sortant'),
    ]
    
    STATUS_CHOICES = [
        ('DRAFT', 'Brouillon'),
        ('SENT', 'Envoyé'),
        ('RECEIVED', 'Reçu'),
        ('ARCHIVED', 'Archivé'),
        ('PENDING', 'En attente'),
        ('PROCESSED', 'Traité'),
    ]
    
    DOC_TYPES = [
        ('LTR', 'Lettre'),
        ('DCE', 'Demande de Certificat'),
        ('ODV', 'Ordre de Virement'),
        ('CDV', 'Courrier de Virement'),
        ('BCM', 'Bon de Commande'),
        ('DAO', 'Demande d\'Approvisionnement'),
        ('ADV', 'Avis de Mission'),
        ('RPT', 'Rapport'),
        ('FCT', 'Facture'),
        ('DVS', 'Devis'),
        ('BDC', 'Bon de Commande'),
        ('CND', 'Conduite à Tenir'),
        ('RCL', 'Recouvrement'),
        ('RCV', 'Reçu'),
        ('RGL', 'Règlement'),
    ]
    
    reference = models.CharField(max_length=50, unique=True, verbose_name="Référence")
    entite = models.ForeignKey('document.Entity', on_delete=models.CASCADE, verbose_name="Entité")
    doc_type = models.CharField(max_length=3, choices=DOC_TYPES, verbose_name="Type de document")
    client = models.ForeignKey('client.Client', on_delete=models.CASCADE, verbose_name="Client", related_name='courriers')
    direction = models.CharField(max_length=3, choices=DIRECTION_CHOICES, default='OUT', verbose_name="Direction")
    statut = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT', verbose_name="Statut")
    date_creation = models.DateField(auto_now_add=True, verbose_name="Date de création")
    date_envoi = models.DateField(null=True, blank=True, verbose_name="Date d'envoi")
    date_reception = models.DateField(null=True, blank=True, verbose_name="Date de réception")
    objet = models.CharField(max_length=255, blank=True, null=True, verbose_name="Objet")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='courriers_crees', on_delete=models.SET_NULL, null=True, verbose_name="Créé par")
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='courriers_traites', on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Traité par")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    fichier = models.FileField(upload_to='courriers/%Y/%m/', blank=True, null=True, verbose_name="Fichier")
    est_urgent = models.BooleanField(default=False, verbose_name="Urgent")
    
    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = generate_reference(
                self.entite.code, 
                self.doc_type, 
                self.client.c_num if hasattr(self.client, 'c_num') else str(self.client.id),
                self.direction
            )
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.reference
    
    class Meta:
        verbose_name = "Courrier"
        verbose_name_plural = "Courriers"
        ordering = ['-date_creation', 'reference']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['client']),
            models.Index(fields=['date_creation']),
            models.Index(fields=['statut']),
            models.Index(fields=['direction']),
        ]
        
    # Ajout de ces méthodes à la classe Courrier

    def mark_as_sent(self, date=None):
        """Marquer comme envoyé avec date optionnelle"""
        self.statut = 'SENT'
        self.date_envoi = date or timezone.now().date()
        self.save(update_fields=['statut', 'date_envoi'])

    def mark_as_received(self, date=None):
        """Marquer comme reçu avec date optionnelle"""
        self.statut = 'RECEIVED'
        self.date_reception = date or timezone.now().date()
        self.save(update_fields=['statut', 'date_reception'])

    def mark_as_processed(self, user=None):
        """Marquer comme traité par un utilisateur"""
        self.statut = 'PROCESSED'
        if user:
            self.handled_by = user
        self.save(update_fields=['statut', 'handled_by'])

    def archive(self):
        """Archiver le courrier"""
        self.statut = 'ARCHIVED'
        self.save(update_fields=['statut'])

    def get_history(self):
        """Récupérer l'historique des actions sur ce courrier"""
        return CourrierHistory.objects.filter(courrier=self).order_by('date_action')

    @property
    def is_overdue(self):
        """Vérifier si le courrier est en retard de traitement (plus de 7 jours)"""
        if self.statut not in ['PROCESSED', 'ARCHIVED']:
            if self.direction == 'IN' and self.date_reception:
                return (timezone.now().date() - self.date_reception).days > 7
            elif self.direction == 'OUT' and self.date_creation:
                return (timezone.now().date() - self.date_creation).days > 7
        return False

# Classe pour l'historique des actions sur un courrier
class CourrierHistory(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'Création'),
        ('EDIT', 'Modification'),
        ('SEND', 'Envoi'),
        ('RECEIVE', 'Réception'),
        ('PROCESS', 'Traitement'),
        ('ARCHIVE', 'Archivage'),
        ('NOTE', 'Annotation'),
    ]
    
    courrier = models.ForeignKey(Courrier, on_delete=models.CASCADE, related_name='historique')
    action = models.CharField(max_length=10, choices=ACTION_CHOICES)
    date_action = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    details = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name = "Historique de courrier"
        verbose_name_plural = "Historiques de courriers"
        ordering = ['-date_action']
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.courrier.reference}"
    
    
from django.db.models.signals import post_save, post_init
from django.dispatch import receiver

@receiver(post_save, sender=Courrier)
def create_courrier_history(sender, instance, created, **kwargs):
    """Crée une entrée d'historique à chaque création ou modification de courrier"""
    if created:
        CourrierHistory.objects.create(
            courrier=instance,
            action='CREATE',
            user=instance.created_by,
            details=f"Création du courrier {instance.reference}"
        )
    else:
        # Détecte si le statut a changé pour créer l'historique approprié
        if hasattr(instance, '_original_statut') and instance._original_statut != instance.statut:
            action_map = {
                'SENT': 'SEND',
                'RECEIVED': 'RECEIVE',
                'PROCESSED': 'PROCESS',
                'ARCHIVED': 'ARCHIVE',
            }
            
            if instance.statut in action_map:
                CourrierHistory.objects.create(
                    courrier=instance,
                    action=action_map[instance.statut],
                    user=instance.handled_by or instance.created_by,
                    details=f"Statut changé de {instance._original_statut} à {instance.statut}"
                )
        else:
            CourrierHistory.objects.create(
                courrier=instance,
                action='EDIT',
                user=instance.handled_by or instance.created_by,
                details="Modification du courrier"
            )

@receiver(post_init, sender=Courrier)
def store_original_status(sender, instance, **kwargs):
    """Stocke le statut original pour détecter les changements"""
    instance._original_statut = instance.statut if instance.pk else None
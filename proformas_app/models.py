from django.utils import timezone
from django.db import models
from django.utils.timezone import now
from django.db.models import Max
from decimal import Decimal
from datetime import timedelta

from django.conf import settings

class Proforma(models.Model):
    STATUS_CHOICES = (
        ('BROUILLON', 'Brouillon'),
        ('EN_COURS', 'En cours'),
        ('VALIDE', 'Validé'),
        ('REFUSE', 'Refusé'),
        ('EXPIRE', 'Expiré'),
        ('ANNULE', 'Annulé'),
    )
    
    reference = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Référence")
    offre = models.OneToOneField('offres_app.Offre', on_delete=models.CASCADE, related_name="proforma", verbose_name="Offre commerciale")
    
    # Informations de base
    sequence_number = models.PositiveIntegerField(blank=True, null=True, verbose_name="Numéro de séquence")
    date_creation = models.DateTimeField(default=now, verbose_name="Date de création")
    date_validation = models.DateTimeField(blank=True, null=True, verbose_name="Date de validation")
    date_expiration = models.DateTimeField(blank=True, null=True, verbose_name="Date d'expiration")
    
    # Statut et suivi
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BROUILLON', verbose_name="Statut")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    # Informations financières
    montant_ht = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Montant HT")
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.25'), verbose_name="Taux TVA (%)")
    montant_tva = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Montant TVA")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Montant TTC")
    
    # Informations des fichiers
    fichier = models.FileField(upload_to='proformas/', blank=True, null=True, verbose_name="Fichier")
    relance = models.DateTimeField(blank=True, null=True, verbose_name="Date de relance")
    
    DELAIS_RELANCE = {
        'ENVOYE': 7,  # Première relance après 7 jours
        'EN_NEGOCIATION': 5,  # Relance tous les 5 jours pendant la négociation
    }
    # Métadonnées
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='proformas_created', verbose_name="Créé par")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='proformas_updated', verbose_name="Modifié par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création dans le système")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de dernière modification")
    
    class Meta:
        verbose_name = "Proforma"
        verbose_name_plural = "Proformas"
        ordering = ['-date_creation']
    
    def __str__(self):
        return self.reference or f"Proforma #{self.pk}"
    
    
    def set_relance(self):
        """
        Configure la prochaine date de relance si l'offre n'est pas gagnée/perdue
        """
        if self.statut in ['GAGNE', 'PERDU']:
            self.relance = None
            return

        if self.statut in self.DELAIS_RELANCE:
            # Si une relance existe déjà, on ajoute le délai à la date actuelle
            # Sinon on l'ajoute à la dernière modification
            base_date = timezone.now() if not self.relance else self.relance
            self.relance = base_date + timedelta(days=self.DELAIS_RELANCE[self.statut])

    @property
    def necessite_relance(self):
        """
        Indique si l'offre nécessite une relance maintenant
        """
        return (
            self.relance 
            and self.relance <= timezone.now() 
            and self.statut not in ['GAGNE', 'PERDU']
        )
    
    def save(self, *args, **kwargs):
        if not self.reference:
            if not self.sequence_number:
                last_sequence = Proforma.objects.filter(
                    offre__entity=self.offre.entity,
                    date_creation__year=now().year,
                    date_creation__month=now().month
                ).aggregate(Max('sequence_number'))['sequence_number__max']
                
                self.sequence_number = (last_sequence or 0) + 1
            
            # Correction ici: utiliser offre__client au lieu de client
            total_proformas_client = Proforma.objects.filter(offre__client=self.offre.client).count() + 1
            
            date = self.date_creation or now()
            
            self.reference = f"{self.offre.entity.code}/PRO/{self.offre.client.c_num}/{str(date.year)[-2:]}{date.month:02d}/{self.offre.pk}/{total_proformas_client}/{self.sequence_number:02d}"
        
        if self.statut == 'VALIDE' and not self.date_validation:
            self.date_validation = now()
            
        if self.montant_ht and (self.montant_tva == 0 or self.montant_ttc == 0):
            self.montant_tva = self.montant_ht * (self.taux_tva / Decimal('100'))
            self.montant_ttc = self.montant_ht + self.montant_tva
            
        super().save(*args, **kwargs)
    
    def calculate_amounts(self):
        """Recalcule les montants TVA et TTC à partir du montant HT"""
        self.montant_tva = self.montant_ht * (self.taux_tva / Decimal('100'))
        self.montant_ttc = self.montant_ht + self.montant_tva
        return self.montant_ttc
        
    def mark_as_validated(self, user=None):
        """Marque la proforma comme validée"""
        self.statut = 'VALIDE'
        self.date_validation = now()
        if user:
            self.updated_by = user
        self.save()
        
    def mark_as_expired(self, user=None):
        """Marque la proforma comme expirée"""
        self.statut = 'EXPIRE'
        if user:
            self.updated_by = user
        self.save()
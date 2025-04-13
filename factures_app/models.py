from django.db import models
from django.utils.timezone import now
from django.db.models import Max
from decimal import Decimal
from django.conf import settings

class Facture(models.Model):
    STATUS_CHOICES = (
        ('BROUILLON', 'Brouillon'),
        ('EMISE', 'Émise'),
        ('PAYEE', 'Payée'),
        ('ANNULEE', 'Annulée'),
        ('IMPAYEE', 'Impayée'),
        ('PARTIELLEMENT_PAYEE', 'Partiellement payée'),
    )
    
    reference = models.CharField(max_length=150, unique=True, blank=True, null=True, verbose_name="Référence")
    affaire = models.OneToOneField('affaires_app.Affaire', on_delete=models.CASCADE, related_name="facture", verbose_name="Affaire")
    
    # Informations de base
    sequence_number = models.PositiveIntegerField(blank=True, null=True, verbose_name="Numéro de séquence")
    date_creation = models.DateTimeField(default=now, verbose_name="Date de création")
    date_emission = models.DateTimeField(blank=True, null=True, verbose_name="Date d'émission")
    date_echeance = models.DateTimeField(blank=True, null=True, verbose_name="Date d'échéance")
    date_paiement = models.DateTimeField(blank=True, null=True, verbose_name="Date de paiement")
    
    # Informations de statut
    statut = models.CharField(max_length=20, choices=STATUS_CHOICES, default='BROUILLON', verbose_name="Statut")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    
    # Informations financières
    montant_ht = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Montant HT")
    taux_tva = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('19.25'), verbose_name="Taux TVA (%)")
    montant_tva = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Montant TVA")
    montant_ttc = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Montant TTC")
    montant_paye = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Montant payé")
    
    # Documents associés
    fichier = models.FileField(upload_to='factures/', blank=True, null=True, verbose_name="Fichier")
    
    # Métadonnées
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='factures_created', verbose_name="Créé par")
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='factures_updated', verbose_name="Modifié par")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création dans le système")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de dernière modification")
    
    class Meta:
        verbose_name = "Facture"
        verbose_name_plural = "Factures"
        ordering = ['-date_creation']
    
    def __str__(self):
        return self.reference or f"Facture #{self.pk}"
    
    def save(self, *args, **kwargs):
        # Génération automatique de la référence
        if not self.reference:
            if not self.sequence_number:
                # Obtenir le dernier numéro de séquence pour l'entité dans le mois courant
                last_sequence = Facture.objects.filter(
                    affaire__offre__entity=self.affaire.offre.entity,  # Utiliser une recherche à travers les relations
                    date_creation__year=now().year,
                    date_creation__month=now().month
                ).aggregate(Max('sequence_number'))['sequence_number__max']
                
                self.sequence_number = (last_sequence or 0) + 1
            
            # Compter le nombre total de factures pour ce client
            total_factures_client = Facture.objects.filter(
                affaire__offre__client=self.affaire.offre.client  # Utiliser une recherche à travers les relations
            ).count() + 1
            
            # Définir la date (utiliser la date de création ou maintenant)
            date = self.date_creation or now()
            
            # Générer la référence avec le format spécifié
            self.reference = f"{self.affaire.offre.entity.code}/FAC/{self.affaire.offre.client.c_num}/{self.affaire.reference}/{self.affaire.offre.produit_principal.code}/{total_factures_client}/{self.sequence_number:04d}"
        
        # Mettre à jour les dates en fonction du statut
        if self.statut == 'EMISE' and not self.date_emission:
            self.date_emission = now()
        
        if self.statut == 'PAYEE' and not self.date_paiement:
            self.date_paiement = now()
        
        # Calculer les montants
        if self.montant_ht and (self.montant_tva == 0 or self.montant_ttc == 0):
            self.montant_tva = self.montant_ht * (self.taux_tva / Decimal('100'))
            self.montant_ttc = self.montant_ht + self.montant_tva
        
        # Mettre à jour le statut basé sur le montant payé
        if self.montant_paye > 0 and self.montant_paye < self.montant_ttc and self.statut not in ['ANNULEE']:
            self.statut = 'PARTIELLEMENT_PAYEE'
        elif self.montant_paye >= self.montant_ttc and self.statut not in ['ANNULEE']:
            self.statut = 'PAYEE'
            if not self.date_paiement:
                self.date_paiement = now()
            
        super().save(*args, **kwargs)
    
    def calculate_amounts(self):
        """Recalcule les montants TVA et TTC à partir du montant HT"""
        self.montant_tva = self.montant_ht * (self.taux_tva / Decimal('100'))
        self.montant_ttc = self.montant_ht + self.montant_tva
        return self.montant_ttc
    
    def mark_as_paid(self, amount=None, user=None):
        """Marque la facture comme payée, entièrement ou partiellement"""
        if amount is None:
            self.montant_paye = self.montant_ttc
            self.statut = 'PAYEE'
        else:
            self.montant_paye = amount
            if amount >= self.montant_ttc:
                self.statut = 'PAYEE'
            elif amount > 0:
                self.statut = 'PARTIELLEMENT_PAYEE'
            else:
                self.statut = 'IMPAYEE'
        
        if self.statut == 'PAYEE' and not self.date_paiement:
            self.date_paiement = now()
        
        if user:
            self.updated_by = user
        
        self.save()
    
    def cancel(self, user=None):
        """Annule la facture"""
        self.statut = 'ANNULEE'
        if user:
            self.updated_by = user
        self.save()
    
    def get_status_display(self):
        """Retourne la représentation lisible du statut"""
        return dict(self.STATUS_CHOICES).get(self.statut, self.statut)
    
    def get_solde(self):
        """Calcule le solde restant à payer"""
        return self.montant_ttc - self.montant_paye
    
    def est_en_retard(self):
        """Vérifie si la facture est en retard de paiement"""
        if not self.date_echeance or self.statut in ['PAYEE', 'ANNULEE']:
            return False
        return now() > self.date_echeance and self.statut not in ['PAYEE', 'ANNULEE']
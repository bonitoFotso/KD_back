from decimal import Decimal
from django.db import models
from django.utils import timezone
from django.db.models import Max
from django.contrib.auth import get_user_model
from datetime import timedelta

from affaires_app.models import Affaire
from proformas_app.models import Proforma
from status_traking.models import StatusTrackingModel


User = get_user_model()


class OffreProduit(models.Model):
    """Modèle de relation Many-to-Many entre Offre et Product avec attributs supplémentaires"""
    offre = models.ForeignKey('Offre', on_delete=models.CASCADE, related_name='offre_produits')
    produit = models.ForeignKey('document.Product', on_delete=models.CASCADE)
    quantite = models.PositiveIntegerField(default=1)
    prix_unitaire = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('0'))
    
    class Meta:
        unique_together = ('offre', 'produit')
        verbose_name = "Produit de l'offre"
        verbose_name_plural = "Produits de l'offre"
    
    @property
    def sous_total(self):
        """Calcule le sous-total pour ce produit"""
        return self.quantite * self.prix_unitaire
    
    def __str__(self):
        return f"{self.produit.code} - {self.quantite}x"

class Offre(StatusTrackingModel):
    """Modèle pour les offres commerciales"""
    STATUS_CHOICES = [
        ('BROUILLON', 'Brouillon'),
        ('ENVOYE', 'Envoyé'),
        ('EN_NEGOCIATION', 'En négociation'),
        ('GAGNE', 'Gagné'),
        ('PERDU', 'Perdu'),
    ]
    
    reference = models.CharField(max_length=100, blank=True, unique=True)
    
    # Redéfinir statut pour être cohérent avec le modèle parent
    statut = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='BROUILLON'
    )
    montant = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'), verbose_name="Montant")
    fichier = models.FileField(upload_to='offres/', blank=True, null=True)
    
    # Relations
    client = models.ForeignKey('client.Client', on_delete=models.CASCADE, related_name="offres")
    contact = models.ForeignKey('client.Contact', on_delete=models.CASCADE, related_name="offres", blank=True, null=True)
    entity = models.ForeignKey('document.Entity', on_delete=models.CASCADE, related_name="offres")
    produits = models.ManyToManyField('document.Product', through='OffreProduit', related_name="offres")
    produit_principal = models.ForeignKey('document.Product', on_delete=models.CASCADE, related_name="offres_principal")
    
    # Redéfinir le champ user pour être cohérent avec createur dans le modèle parent
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name="offres",
        help_text="Utilisateur qui a créé l'offre initialement"
    )
    
    # date 
    date_envoi = models.DateTimeField(blank=True, null=True, verbose_name="Date d'envoi")
    date_validation = models.DateTimeField(blank=True, null=True, verbose_name="Date de validation")
    date_cloture = models.DateTimeField(blank=True, null=True, verbose_name="Date de validation")

    
    # Champs supplémentaires
    notes = models.TextField(blank=True)
    sequence_number = models.PositiveIntegerField(default=1)
    
    # Champ pour la gestion des relances
    relance = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Date de la prochaine relance si l'offre n'est pas encore gagnée"
    )
    
    DELAIS_RELANCE = {
        'ENVOYE': 1,  # Première relance après 7 jours
        'EN_NEGOCIATION': 5,  # Relance tous les 5 jours pendant la négociation
    }

    class Meta:
        verbose_name = "Offre commerciale"
        verbose_name_plural = "Offres commerciales"
        ordering = ['date_creation']
        
    def generer_reference(self):
        """
        Génère une référence unique pour l'offre selon le format défini
        """
        if not self.sequence_number:
            last_sequence = Offre.objects.filter(
                entity=self.entity,
                client=self.client,
                date_creation__year=timezone.now().year,
                date_creation__month=timezone.now().month
            ).aggregate(Max('sequence_number'))['sequence_number__max']
            self.sequence_number = (last_sequence or 0) + 1
        
        produit_code = self.produit_principal.code
        total_offres_client = Offre.objects.filter(client=self.client).count() + 1
        date = self.date_creation or timezone.now()
        
        return f"{self.entity.code}/OFF/{self.client.c_num}/{str(date.year)[-2:]}{date.month:02d}{date.day:02d}/{produit_code}/{total_offres_client}/{self.sequence_number:04d}"

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
            if self.date_envoi:
                base_date = self.date_envoi
            else:
                base_date = self.date_creation
            if self.relance:
                base_date = self.relance
            else:
                # Si aucune relance n'existe, on prend la date de création
                base_date = self.date_creation
            # On ajoute le délai de relance
            self.relance = base_date + timedelta(days=self.DELAIS_RELANCE[self.statut])
        else:
            # Si le statut n'est pas dans les délais de relance, on remet à zéro
            self.relance = None
        # Si la relance est déjà passée, on la remet à aujourd'hui
        if self.relance and self.relance <= timezone.now():
            
            
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
    
    @property
    def calculer_montant_total(self):
        """
        Calcule le montant total de l'offre à partir des produits et quantités
        """
        total = Decimal('0')
        for offre_produit in self.produits.all():
            total += offre_produit.sous_total
        return total
    
    def save(self, *args, **kwargs):
        # Pour la première sauvegarde, lier le user au createur
        is_new = self.pk is None
        if is_new and self.user and not hasattr(self, 'createur'):
            self.createur = self.user
            
        # Génération de la référence si elle n'existe pas
        if not self.reference:
            self.reference = self.generer_reference()

        # Gestion des statuts et relances
        statut_precedent = None
        
        # Vérifier si l'objet existe déjà pour comparer l'ancien statut
        if self.pk:
            try:
                statut_precedent = Offre.objects.get(pk=self.pk).statut
            except Offre.DoesNotExist:
                pass
        
        # Mettre à jour les relances selon le statut
        if self.statut in ['GAGNE', 'PERDU']:
            self.relance = None
        else:
            self.set_relance()

        # Note: nous ne appelons pas directement set_status ici pour éviter 
        # des problèmes de récursion avec save()
        
        # Appel à la méthode save du parent (StatusTrackingModel)
        super().save(*args, **kwargs)
        
        ## Mettre à jour le montant total si nécessaire
        #montant_calcule = self.calculer_montant_total
        #if self.montant != montant_calcule:
        #    self.montant = montant_calcule
        #    # Éviter une récursion infinie en ne rappelant save que si le montant a changé
        #    if 'update_fields' not in kwargs:
        #        models.Model.save(self, update_fields=['montant'])  # Appel direct à Model.save pour éviter la récursion
        
        # Créer une proforma et une affaire si l'offre est gagnée
        if self.statut == 'GAGNE' and (not statut_precedent or statut_precedent != 'GAGNE'):
            # Créer une proforma
            proforma, proforma_created = Proforma.objects.get_or_create(
                offre=self,
                defaults={
                    'created_by': self.user or self.createur,
                    'montant_ht': self.montant
                }
            )
            
            # Créer une affaire
            affaire, affaire_created = Affaire.objects.get_or_create(
                offre=self,
                defaults={
                    'createur': self.user or self.createur,
                    'modificateur' :self.user or self.createur,
                    'montant_total': self.montant
                }
            )
    
    def changer_statut(self, nouveau_statut, user=None, date_specifique=None, commentaire="", metadata=None):
        """
        Méthode pour changer le statut de l'offre qui gère également les effets secondaires
        comme la création de proforma et d'affaire.
        
        Args:
            nouveau_statut (str): Le nouveau statut
            user (User): L'utilisateur effectuant le changement
            date_specifique (datetime): Date spécifique pour le changement de statut
            commentaire (str): Commentaire sur le changement
            metadata (dict): Métadonnées additionnelles
            
        Returns:
            bool: True si le statut a été changé, False sinon
        """
        # Vérifier si le statut change réellement
        if self.statut == nouveau_statut:
            return False
            
        # Sauvegarder l'ancien statut
        ancien_statut = self.statut
        
        # Appliquer le changement via set_status de StatusTrackingModel
        changed = self.set_status(
            nouveau_statut, 
            user=user, 
            date_specifique=date_specifique,
            commentaire=commentaire,
            metadata=metadata
        )
        
        if changed:
            # Mettre à jour la relance selon le nouveau statut
            if nouveau_statut in ['GAGNE', 'PERDU']:
                self.relance = None
            else:
                self.set_relance()
            
            # Sauvegarder les changements d'attributs sans repasser par toute la logique de save()
            models.Model.save(self, update_fields=['relance'])
            
            # Si on passe à GAGNE, créer proforma et affaire
            if nouveau_statut == 'GAGNE' and ancien_statut != 'GAGNE':
                # Créer une proforma
                proforma, proforma_created = Proforma.objects.get_or_create(
                    offre=self,
                    defaults={
                        'created_by': user or self.user or self.createur,
                        'montant': self.montant
                    }
                )
                
                # Créer une affaire
                affaire, affaire_created = Affaire.objects.get_or_create(
                    offre=self,
                    defaults={
                        'created_by': user or self.user or self.createur,
                        'montant_total': self.montant
                    }
                )
        
        return changed
    
    def clean(self):
        """
        Validation personnalisée pour le modèle
        """
        from django.core.exceptions import ValidationError
        
        # Vérifier que le contact appartient bien au client
        if self.contact and self.contact.client != self.client:
            raise ValidationError({
                'contact': f"Le contact sélectionné n'appartient pas au client {self.client.nom}"
            })
        
        # Autres validations métier...
        
    def get_status_choices(self):
        """Implémentation de la méthode abstraite"""
        return self.STATUS_CHOICES
    
    def __str__(self):
        return f"{self.reference} - {self.client.nom}"
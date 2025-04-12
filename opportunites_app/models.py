from django.db import models, transaction
from django.utils.timezone import now
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from django_fsm import FSMField, transition
from django.contrib.contenttypes.models import ContentType
from django.db.models import Max
from django.conf import settings

from document.models import AuditLog
from offres_app.models import Offre


class Opportunite(models.Model):
    """
    Modèle représentant une opportunité commerciale dans le pipeline de vente.
    Une opportunité passe par différents stades (de prospect à gagnée/perdue)
    et peut être convertie en offre commerciale.
    """
    STATUS_CHOICES = [
        ('PROSPECT', 'Prospect'),
        ('QUALIFICATION', 'Qualification'),
        ('PROPOSITION', 'Proposition'),
        ('NEGOCIATION', 'Négociation'),
        ('GAGNEE', 'Gagnée'),
        ('PERDUE', 'Perdue'),
    ]
    
    # Relations
    entity = models.ForeignKey(
        'document.Entity', 
        on_delete=models.CASCADE, 
        related_name='opportunites',
        verbose_name="Entité"
    )
    client = models.ForeignKey(
        'client.Client', 
        on_delete=models.CASCADE, 
        related_name="opportunites",
        verbose_name="Client"
    )
    contact = models.ForeignKey(
        'client.Contact', 
        on_delete=models.CASCADE, 
        related_name="opportunites",
        verbose_name="Contact principal"
    )
    produits = models.ManyToManyField(
        'document.Product', 
        related_name="opportunites",
        verbose_name="Produits"
    )
    produit_principal = models.ForeignKey(
        'document.Product', 
        on_delete=models.CASCADE, 
        related_name="opportunites_principales",
        verbose_name="Produit principal"
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='opportunites_crees',
        verbose_name="Créé par"
    )
    
    # Champs de base
    reference = models.CharField(
        max_length=255, 
        unique=True, 
        blank=True,
        verbose_name="Référence"
    )
    sequence_number = models.IntegerField(
        blank=True, 
        null=True,
        verbose_name="Numéro de séquence"
    )
    description = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Description"
    )
    besoins_client = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Besoins du client"
    )
    
    commentaire = models.TextField(
        blank=True, 
        null=True,
        verbose_name="Commentaire"
    )
    
    # Montants et probabilité
    montant = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name="Montant"
    )
    montant_estime = models.DecimalField(
        max_digits=15, 
        decimal_places=2,
        verbose_name="Montant estimé"
    )
    probabilite = models.IntegerField(
        default=0, 
        help_text="Probabilité de conversion en %",
        verbose_name="Probabilité"
    )
    
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='opportunites_responsables',
        verbose_name="Responsable"
    )
    
    # Statut et dates
    statut = FSMField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PROSPECT',
        verbose_name="Statut"
    )
    date_creation = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création"
    )
    date_detection = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de détection"
    )
    date_modification = models.DateTimeField(
        auto_now=True,
        verbose_name="Date de modification"
    )
    date_cloture = models.DateTimeField(
        blank=True, 
        null=True,
        verbose_name="Date de clôture"
    )
    relance = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="Date de la prochaine relance",
        verbose_name="Date de relance"
    )
    
    # Configuration pour les délais de relance par statut (en jours)
    DELAIS_RELANCE = {
        'PROSPECT': 14,       # Relance après 14 jours pour les prospects
        'QUALIFICATION': 10,  # Relance après 10 jours pour les qualifications
        'PROPOSITION': 7,     # Relance après 7 jours pour les propositions
        'NEGOCIATION': 5,     # Relance après 5 jours pour les négociations
    }
    
    # Configuration pour les probabilités par statut
    PROBABILITES_STATUT = {
        'PROSPECT': 10,
        'QUALIFICATION': 30,
        'PROPOSITION': 50,
        'NEGOCIATION': 75,
        'GAGNEE': 100,
        'PERDUE': 0,
    }
    
    class Meta:
        verbose_name = "Opportunité"
        verbose_name_plural = "Opportunités"
        ordering = ['-date_creation']
        indexes = [
            models.Index(fields=['statut']),
            models.Index(fields=['client']),
            models.Index(fields=['entity']),
            models.Index(fields=['date_creation']),
            models.Index(fields=['relance']),
        ]
    
    def __str__(self):
        return f"Opportunité {self.reference} - {self.client.nom} - {self.statut}"
    
    def set_relance(self):
        """
        Configure la prochaine date de relance en fonction du statut actuel.
        Réinitialise la relance si l'opportunité est gagnée ou perdue.
        """
        # Pas de relance pour les opportunités clôturées
        if self.statut in ['GAGNEE', 'PERDUE']:
            self.relance = None
            return

        # Configurer la relance pour les statuts en cours
        if self.statut in self.DELAIS_RELANCE:
            # Base temporelle: soit maintenant, soit la date de relance précédente
            base_date = now() if not self.relance else self.relance
            self.relance = base_date + timedelta(days=self.DELAIS_RELANCE[self.statut])
    
    def log_action(self, action, user, changes=None):
        """
        Enregistre une action dans le journal d'audit.
        
        Args:
            action: Type d'action (CREATE, UPDATE, DELETE, etc.)
            user: Utilisateur ayant effectué l'action
            changes: Dictionnaire des modifications apportées
        """
        AuditLog.objects.create(
            user=user,
            action=action,
            content_type=ContentType.objects.get_for_model(self),
            object_id=str(self.pk),
            object_repr=str(self),
            changes=changes or {}
        )
    
    @property
    def necessite_relance(self):
        """
        Indique si l'opportunité nécessite une relance maintenant.
        
        Returns:
            bool: True si une relance est nécessaire, False sinon
        """
        return (
            self.relance is not None
            and self.relance <= now() 
            and self.statut not in ['GAGNEE', 'PERDUE']
        )
    
    @property
    def valeur_ponderee(self):
        """
        Calcule la valeur pondérée de l'opportunité en fonction de sa probabilité.
        Returns:
        Decimal: Montant estimé × probabilité / 100, ou None si les valeurs sont invalides
        """
        try:
            # Convert to Decimal with safety checks
            montant = Decimal(self.montant_estime or 0)
            probabilite = Decimal(self.probabilite or 0)
            return montant * probabilite / Decimal(100)
        except (TypeError, InvalidOperation, ValueError):
            # Return 0 or None based on your requirements
            return Decimal('0')
    def generer_reference(self):
        """
        Génère une référence unique pour l'opportunité.
        Format: {code_entite}/OPP/{code_client}/{année}{mois}{jour}/{code_produit}/{nb_opportunites}/{sequence}
        """
        if not self.reference:
            if not self.sequence_number:
                # Récupère le dernier numéro de séquence pour cette entité/client/mois/année
                date = self.date_creation or now()
                last_sequence = Opportunite.objects.filter(
                    entity=self.entity,
                    client=self.client,
                    date_creation__year=date.year,
                    date_creation__month=date.month
                ).aggregate(Max('sequence_number'))['sequence_number__max']
                self.sequence_number = (last_sequence or 0) + 1
            
            # Calcul du nombre total d'opportunités pour ce client (incluant celle-ci)
            total_opportunites_client = Opportunite.objects.filter(client=self.client).count() + 1
            
            date = self.date_creation or now()
            self.reference = (
                f"{self.entity.code}/OPP/{self.client.c_num}/"
                f"{str(date.year)[-2:]}{date.month:02d}{date.day:02d}/"
                f"{self.produit_principal.code}/"
                f"{total_opportunites_client}/"
                f"{self.sequence_number:04d}"
            )
        return self.reference
    
    @transition(field=statut, source='PROSPECT', target='QUALIFICATION')
    def qualifier(self, user):
        """
        Transition de statut: PROSPECT -> QUALIFICATION
        """
        self.log_action('UPDATE', user, {'statut': 'QUALIFICATION'})
        self.set_relance()
    
    @transition(field=statut, source='QUALIFICATION', target='PROPOSITION')
    def proposer(self, user):
        """
        Transition de statut: QUALIFICATION -> PROPOSITION
        """
        self.log_action('UPDATE', user, {'statut': 'PROPOSITION'})
        self.set_relance()
    
    @transition(field=statut, source='PROPOSITION', target='NEGOCIATION')
    def negocier(self, user):
        """
        Transition de statut: PROPOSITION -> NEGOCIATION
        """
        self.log_action('UPDATE', user, {'statut': 'NEGOCIATION'})
        self.set_relance()
    
    @transition(field=statut, source='*', target='GAGNEE')
    def gagner(self, user):
        """
        Transition de statut: état quelconque -> GAGNEE
        """
        self.date_cloture = now()
        self.relance = None
        self.log_action('UPDATE', user, {'statut': 'GAGNEE'})
    
    @transition(field=statut, source='*', target='PERDUE')
    def perdre(self, user, raison=None):
        """
        Transition de statut: état quelconque -> PERDUE
        
        Args:
            user: Utilisateur effectuant la transition
            raison: Raison optionnelle de la perte
        """
        self.date_cloture = now()
        self.relance = None
        changes = {'statut': 'PERDUE'}
        
        if raison:
            if self.description:
                self.description += f"\n\nRaison de perte: {raison}"
            else:
                self.description = f"Raison de perte: {raison}"
            changes['raison'] = raison
            
        self.log_action('UPDATE', user, changes)
    
    @transaction.atomic
    def creer_offre(self, user=None):
        """
        Crée une offre commerciale basée sur cette opportunité.
        
        Args:
            user: Utilisateur créant l'offre (par défaut, le créateur de l'opportunité)
            
        Returns:
            Offre: L'offre nouvellement créée
            
        Raises:
            ValueError: Si l'opportunité n'est pas dans un statut approprié
        """
        if self.statut not in ['QUALIFICATION', 'PROPOSITION', 'NEGOCIATION', 'GAGNEE']:
            raise ValueError("L'opportunité doit être au moins qualifiée pour créer une offre.")
        
        creator = user or self.created_by
        
        # Création de l'offre
        offre = Offre.objects.create(
            client=self.client,
            entity=self.entity,
            produit=self.produit_principal,
            contact=self.contact,
            montant=self.montant_estime,
            doc_type='OFF',
            created_by=creator,
            opportunite=self,  # Lien vers l'opportunité d'origine
        )
        
        # Ajout des produits associés à l'opportunité
        for produit in self.produits.all():
            offre.produits.add(produit)
        
        # Journalisation
        self.log_action('CREATE_OFFRE', creator, {
            'offre_id': offre.pk,
            'offre_reference': offre.reference
        })
        
        return offre
    
    def save(self, *args, **kwargs):
        """
        Sauvegarde l'opportunité avec logique métier associée:
        - Génération de référence
        - Mise à jour de la probabilité
        - Gestion des dates de clôture et relance
        """
        is_new = self.pk is None
        
        # Mise à jour de la probabilité en fonction du statut
        if self.statut in self.PROBABILITES_STATUT:
            self.probabilite = self.PROBABILITES_STATUT[self.statut]
        
        # Gestion des dates de clôture
        if self.statut in ['GAGNEE', 'PERDUE'] and not self.date_cloture:
            self.date_cloture = now()
            self.relance = None
        elif self.statut not in ['GAGNEE', 'PERDUE']:
            self.date_cloture = None
            self.set_relance()
        
        # Génération de la référence si nécessaire
        if not self.reference:
            self.generer_reference()
        
        # Sauvegarde
        super().save(*args, **kwargs)
        
        # Ajout de l'audit log pour la création
        if is_new and hasattr(self, 'created_by'):
            self.log_action('CREATE', self.created_by)
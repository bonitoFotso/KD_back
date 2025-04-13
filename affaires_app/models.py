from decimal import Decimal
from django.db import models
from django.conf import settings
from django.utils.timezone import now
from django.db.models import Max
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from factures_app.models import Facture
from status_traking.models import StatusChange, StatusTrackingModel


class Affaire(StatusTrackingModel):
    """
    Représente un projet contractualisé issu d'une offre acceptée par un client.
    Une affaire gère le cycle de vie complet du projet, incluant les rapports,
    les formations éventuelles et la facturation.
    """

    # Relation avec l'offre d'origine
    offre = models.OneToOneField(
        "offres_app.Offre",
        on_delete=models.CASCADE,
        related_name="affaire",
        help_text="Offre acceptée qui a généré cette affaire",
    )

    # Informations d'identification
    reference = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Référence unique de l'affaire (générée automatiquement)",
    )
    sequence_number = models.PositiveIntegerField(
        default=0,
        editable=False,
        help_text="Numéro de séquence pour la génération de référence",
    )
    doc_type = models.CharField(
        max_length=3,
        default="AFF",
        editable=False,
        help_text="Type de document (AFF pour Affaire)",
    )

    # Dates et durée
    date_debut = models.DateTimeField(
        verbose_name="Date de début",
        help_text="Date de début de l'affaire",
        default=now,
    )
    date_fin_prevue = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de fin prévue",
        help_text="Date de fin prévue pour l'affaire",
    )
    date_fin_reelle = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de fin réelle",
        help_text="Date de fin réelle de l'affaire (renseignée à la clôture)",
    )

    date_validation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de validation",
        help_text="Date à laquelle l'affaire a été validée",
    )
    date_debut_effective = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date de début effective",
        help_text="Date à laquelle l'affaire a réellement commencé",
    )
    date_annulation = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Date d'annulation",
        help_text="Date à laquelle l'affaire a été annulée",
    )
    raison_annulation = models.TextField(
        null=True,
        blank=True,
        verbose_name="Raison d'annulation",
        help_text="Raison pour laquelle l'affaire a été annulée",
    )

    # Responsable de l'affaire (différent du createur dans StatusTrackingModel)
    responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="affaires_gerees",
        verbose_name="Responsable",
        help_text="Utilisateur responsable de l'affaire",
    )

    # Statut et suivi
    STATUT_CHOICES = [
        ("BROUILLON", "Brouillon"),
        ("VALIDE", "Validée"),
        ("EN_COURS", "En cours"),
        ("EN_PAUSE", "En pause"),
        ("TERMINEE", "Terminée"),
        ("ANNULEE", "Annulée"),
    ]

    # Redéfinir statut pour être cohérent avec le modèle parent
    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default="BROUILLON",
        verbose_name="Statut",
        help_text="État actuel de l'affaire",
    )

    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
        help_text="Notes internes concernant l'affaire",
    )

    # Champs pour le suivi financier
    montant_total = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Montant total",
        help_text="Montant total de l'affaire (HT)",
    )
    montant_facture = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Montant facturé",
        help_text="Montant total facturé (HT)",
    )
    montant_paye = models.DecimalField(
        max_digits=20,
        decimal_places=2,
        default=Decimal("0"),
        verbose_name="Montant payé",
        help_text="Montant total payé (HT)",
    )

    class Meta:
        verbose_name = "Affaire"
        verbose_name_plural = "Affaires"
        ordering = ["-date_creation"]
        indexes = [
            models.Index(fields=["reference"]),
            models.Index(fields=["statut"]),
            models.Index(fields=["date_creation"]),
        ]

    def __str__(self):
        return f"Affaire {self.reference} - {self.offre.client.nom}"

    def get_status_choices(self):
        """Implémentation de la méthode abstraite de StatusTrackingModel"""
        return self.STATUT_CHOICES

    def clean(self):
        """Validation des données avant sauvegarde"""
        if self.date_fin_prevue and self.date_fin_prevue < self.date_debut:
            raise ValidationError(
                {
                    "date_fin_prevue": "La date de fin prévue ne peut pas être antérieure à la date de début."
                }
            )

        if self.date_fin_reelle and self.date_fin_reelle < self.date_debut:
            raise ValidationError(
                {
                    "date_fin_reelle": "La date de fin réelle ne peut pas être antérieure à la date de début."
                }
            )

        if self.statut == "TERMINEE" and not self.date_fin_reelle:
            raise ValidationError(
                {
                    "date_fin_reelle": "Une date de fin réelle est requise pour une affaire terminée."
                }
            )

    def generate_reference(self):
        """Génère une référence unique pour l'affaire"""
        date = self.date_creation or now()

        # Format: AFF + année (2 chiffres) + mois + ID client + ID offre + séquence
        if not self.sequence_number:
            # Récupère le dernier numéro de séquence pour le mois en cours
            last_sequence = (
                Affaire.objects.filter(
                    doc_type="AFF",
                    date_creation__year=date.year,
                    date_creation__month=date.month,
                ).aggregate(Max("sequence_number"))["sequence_number__max"]
                or 0
            )

            self.sequence_number = last_sequence + 1

        client_id = str(self.offre.client.pk)
        offre_id = str(self.offre.pk)
        sequence = str(self.sequence_number).zfill(3)

        return (
            f"AFF{date.year % 100:02d}{date.month:02d}{client_id}{offre_id}{sequence}"
        )

    def save(self, *args, **kwargs):
        """Sauvegarde avec génération de référence"""
        creating = not self.pk

        # Avant la première sauvegarde
        if creating:
            # Génère la référence si elle n'existe pas encore
            if not self.reference:
                self.reference = self.generate_reference()

            # Initialise le montant total depuis l'offre
            if hasattr(self.offre, "montant") and self.montant_total == 0:
                self.montant_total = self.offre.montant

            ## Si le createur n'est pas défini, utiliser created_by (compatibilité)
            # if hasattr(self, 'created_by') and self.created_by and not hasattr(self, 'createur'):
            #    self.createur = self.created_by

        # Validation manuelle
        self.full_clean()

        # Sauvegarde l'objet avec la méthode parent
        super().save(*args, **kwargs)

    def changer_statut(
        self,
        nouveau_statut,
        user=None,
        date_specifique=None,
        commentaire="",
        metadata=None,
    ):
        """
        Change le statut de l'affaire avec des actions spécifiques selon le statut

        Args:
            nouveau_statut (str): Le nouveau statut à appliquer
            user (User): L'utilisateur effectuant le changement
            date_specifique (datetime): Date spécifique pour le changement (optionnel)
            commentaire (str): Commentaire expliquant le changement
            metadata (dict): Métadonnées supplémentaires pour le changement

        Returns:
            bool: True si le statut a été changé, False sinon
        """
        # Vérifier si le statut change réellement
        if self.statut == nouveau_statut:
            return False

        # Sauvegarder l'ancien statut
        ancien_statut = self.statut

        # Préparation des métadonnées si non fournies
        if metadata is None:
            metadata = {}

        # Ajout de la date spécifique aux métadonnées pour traçabilité
        if date_specifique:
            metadata["date_changement_specifique"] = date_specifique.isoformat()

        # Actions spécifiques selon le nouveau statut
        if nouveau_statut == "TERMINEE":
            # Mise à jour de la date de fin réelle si nécessaire
            if not self.date_fin_reelle:
                self.date_fin_reelle = date_specifique or now()
                # Ajouter aux métadonnées pour traçabilité
                metadata["date_fin_reelle"] = self.date_fin_reelle.isoformat()

        elif nouveau_statut == "EN_COURS":
            # Actions à effectuer quand une affaire passe en cours
            # Par exemple, mise à jour de la date de début effective si non définie
            if not self.date_debut_effective:
                self.date_debut_effective = date_specifique or now()
                metadata["date_debut_effective"] = self.date_debut_effective.isoformat()

        elif nouveau_statut == "ANNULEE":
            # Actions spécifiques à l'annulation
            self.date_annulation = date_specifique or now()
            metadata["date_annulation"] = self.date_annulation.isoformat()

            # On pourrait aussi ajouter la raison d'annulation si fournie dans les métadonnées
            if "raison_annulation" in metadata:
                self.raison_annulation = metadata["raison_annulation"]

        # Stocker cet ancien statut pour utilisation dans les signaux
        self._old_statut = ancien_statut

        # Utiliser la méthode de la classe parent pour changer le statut avec historique
        changed = self.set_status(
            nouveau_statut,
            user=user,
            date_specifique=date_specifique,
            commentaire=commentaire,
            metadata=metadata,
        )

        # Actions post-changement de statut
        if changed:
            # Initialiser le projet si on passe à VALIDE depuis un autre statut
            if nouveau_statut == "VALIDE" and ancien_statut != "VALIDE":
                self.initialiser_projet()

            # Mise à jour des dates de l'affaire en fonction du nouveau statut
            self._update_affaire_dates(nouveau_statut, date_specifique)

            # Enregistrer les changements
            self.save(
                update_fields=[
                    "date_fin_reelle",
                    "date_debut_effective",
                    "date_annulation",
                ]
            )

        return changed

    def _update_affaire_dates(self, nouveau_statut, date_specifique=None):
        """Méthode utilitaire pour mettre à jour les dates de l'affaire selon le statut"""
        current_date = date_specifique or now()

        # Mise à jour des dates selon le statut
        if nouveau_statut == "VALIDE" and not hasattr(self, "date_validation"):
            self.date_validation = current_date
        elif nouveau_statut == "EN_COURS" and not hasattr(self, "date_debut_effective"):
            self.date_debut_effective = current_date
        elif nouveau_statut == "TERMINEE" and not self.date_fin_reelle:
            self.date_fin_reelle = current_date
        elif nouveau_statut == "ANNULEE" and not hasattr(self, "date_annulation"):
            self.date_annulation = current_date

    @transaction.atomic
    def initialiser_projet(self):
        """Initialise tous les éléments du projet après validation"""
        self.cree_rapports()
        self.cree_facture_initiale()

        # Événement de journal
        # self.log_event("Affaire initialisée", "Création des rapports et de la facture initiale")

    def cree_rapports(self):
        """Crée les rapports pour chaque produit de l'offre"""
        from document.models import Rapport
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"Création des rapports pour l'affaire {self.reference}")

        with transaction.atomic():
            # Récupération des rapports existants pour ne pas les recréer
            existing_reports = {
                rapport.produit.pk: rapport
                for rapport in Rapport.objects.filter(affaire=self)
            }

            rapports_crees = []
            produits_traites = set()

            # Traiter chaque produit individuellement
            for produit in self.offre.produits.all():
                # Éviter les doublons de produits
                if produit.id in produits_traites:
                    logger.warning(
                        f"Produit {produit.id} déjà traité pour l'affaire {self.reference}"
                    )
                    continue

                produits_traites.add(produit.id)

                # Vérifier si ce rapport existe déjà
                if produit.id in existing_reports:
                    rapport = existing_reports[produit.id]
                    logger.info(
                        f"Rapport déjà existant pour produit {produit.id} dans l'affaire {self.reference}"
                    )
                else:
                    # Créer un nouveau rapport avec get_or_create pour éviter les conflits
                    rapport, created = Rapport.objects.get_or_create(
                        affaire=self,
                        produit=produit,
                        defaults={
                            "client": self.offre.client,
                            "entity": self.offre.entity,
                            "sequence_number": self.sequence_number,
                            "statut": "BROUILLON",
                        },
                    )

                    if created:
                        logger.info(
                            f"Nouveau rapport créé pour produit {produit.id} dans l'affaire {self.reference}"
                        )
                    else:
                        logger.info(
                            f"Rapport existant trouvé pour produit {produit.id} dans l'affaire {self.reference}"
                        )

                rapports_crees.append(rapport)

                # Traiter immédiatement si c'est une formation
                if produit.category.code == "FOR":
                    try:
                        self.cree_formation(produit, rapport)
                        logger.info(f"Formation créée pour rapport {rapport.pk}")
                    except Exception as e:
                        logger.error(
                            f"Erreur lors de la création de formation pour rapport {rapport.pk}: {str(e)}"
                        )

            return rapports_crees

    def cree_formation(self, produit, rapport=None):
        """Crée une formation pour le produit spécifié"""
        from document.models import Formation, Rapport

        # Si le rapport n'est pas fourni, essaie de le récupérer
        if not rapport:
            try:
                rapport = Rapport.objects.get(affaire=self, produit=produit)
            except Rapport.DoesNotExist:
                return None

        # Crée la formation avec get_or_create pour éviter les doublons
        formation, created = Formation.objects.get_or_create(
            rapport=rapport,
            defaults={
                "titre": f"Formation {produit.name}",
                "client": self.offre.client,
                "affaire": self,
                "date_debut": self.date_debut,
                "date_fin": self.date_fin_prevue,
                "description": f"Formation {produit.name} pour {self.offre.client.nom}",
            },
        )

        return formation

    def cree_facture_initiale(self):
        """Crée la facture initiale pour l'affaire"""
        # Vérifie si une facture existe déjà
        if Facture.objects.filter(affaire=self).exists():
            return None

        # Crée la facture avec get_or_create pour éviter les doublons
        facture, created = Facture.objects.get_or_create(
            affaire=self,
            defaults={
                "statut": "BROUILLON",
                "sequence_number": self.sequence_number,
                "montant_ht": self.montant_total,
                "created_by": self.createur,
            },
        )

        return facture

    def get_progression(self):
        """Calcule le pourcentage de progression de l'affaire"""
        from document.models import Rapport

        rapports = Rapport.objects.filter(affaire=self)
        total_rapports = rapports.count()

        if total_rapports == 0:
            return 0

        rapports_termines = rapports.filter(statut__in=["VALIDE", "TERMINE"]).count()
        return int((rapports_termines / total_rapports) * 100)

    def get_montant_restant_a_facturer(self):
        """Calcule le montant restant à facturer"""
        return self.montant_total - self.montant_facture

    def get_montant_restant_a_payer(self):
        """Calcule le montant restant à payer"""
        return self.montant_facture - self.montant_paye

    def assigner_responsable(
        self, nouveau_responsable, user=None, commentaire="", metadata=None
    ):
        """
        Assigne un nouveau responsable à l'affaire avec traçabilité

        Args:
            nouveau_responsable (User): Le nouvel utilisateur responsable
            user (User): L'utilisateur effectuant le changement
            commentaire (str): Commentaire expliquant le changement
            metadata (dict): Métadonnées additionnelles

        Returns:
            bool: True si le responsable a été changé, False sinon
        """
        # Vérifier si le responsable change réellement
        if self.responsable and self.responsable.id == nouveau_responsable.id:
            return False

        # Enregistrer l'ancien responsable pour la journalisation
        ancien_responsable = self.responsable

        # Mettre à jour le responsable
        self.responsable = nouveau_responsable
        self.modificateur = user if user else self.modificateur
        self.save(update_fields=["responsable", "modificateur"])

        # Préparer les métadonnées
        if metadata is None:
            metadata = {}

        metadata["ancien_responsable_id"] = (
            ancien_responsable.id if ancien_responsable else None
        )
        metadata["ancien_responsable_nom"] = (
            ancien_responsable.username if ancien_responsable else "Aucun"
        )
        metadata["nouveau_responsable_id"] = nouveau_responsable.id
        metadata["nouveau_responsable_nom"] = nouveau_responsable.username

        # Journaliser le changement
        from django.contrib.contenttypes.models import ContentType

        content_type = ContentType.objects.get_for_model(self)


        StatusChange.objects.create(
            content_type=content_type,
            object_id=self.pk,
            ancien_statut="RESPONSABLE:"
            + (ancien_responsable.username if ancien_responsable else "None"),
            nouveau_statut="RESPONSABLE:" + nouveau_responsable.username,
            utilisateur=user,
            commentaire=commentaire,
            metadata=metadata,
        )

        return True


# Les signaux sont remplacés par la logique dans la méthode changer_statut()
# Cependant, pour maintenir la compatibilité avec le code existant, nous pouvons
# garder une version simplifiée des signaux qui se coordonne avec StatusTrackingModel


@receiver(pre_save, sender=Affaire)
def pre_save_affaire(sender, instance, **kwargs):
    """
    Actions à effectuer avant la sauvegarde d'une affaire.
    Gère la compatibilité avec created_by et createur.
    """
    # Si le modèle vient d'être créé et que created_by est défini mais pas createur
    if not instance.pk and hasattr(instance, "created_by") and instance.created_by:
        if not hasattr(instance, "createur") or not instance.createur:
            instance.createur = instance.created_by

    # Vérifier le changement de statut si c'est une mise à jour
    if instance.pk:
        try:
            old_instance = Affaire.objects.get(pk=instance.pk)

            # Si le statut a changé mais qu'on n'a pas utilisé changer_statut()
            if old_instance.statut != instance.statut and not hasattr(
                instance, "_old_statut"
            ):
                instance._old_statut = old_instance.statut

                # Mettre à jour la date de fin réelle si nécessaire
                if instance.statut == "TERMINEE" and not instance.date_fin_reelle:
                    instance.date_fin_reelle = now()
        except Affaire.DoesNotExist:
            pass


@receiver(post_save, sender=Affaire)
def post_save_affaire(sender, instance, created, **kwargs):
    """
    Actions à effectuer après la sauvegarde d'une affaire.
    Déclenche l'initialisation du projet si le statut passe à VALIDE.
    """
    # Vérifier si l'affaire vient d'être créée avec statut VALIDE
    if created and instance.statut == "VALIDE":
        # Appeler initialiser_projet en dehors de la transaction courante
        transaction.on_commit(lambda: instance.initialiser_projet())

    # Vérifier si le statut vient de passer à VALIDE (sans utiliser changer_statut)
    elif (
        hasattr(instance, "_old_statut")
        and instance._old_statut != "VALIDE"
        and instance.statut == "VALIDE"
    ):
        # Appeler initialiser_projet en dehors de la transaction courante
        transaction.on_commit(lambda: instance.initialiser_projet())

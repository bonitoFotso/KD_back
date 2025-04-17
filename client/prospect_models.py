from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.utils.timezone import now

from client.models import Categorie, Contact, Ville



class Entreprise(models.Model):
    """Représente une entreprise avec laquelle vous pouvez avoir différents types de relations"""

    nom = models.CharField(max_length=100)
    adresse = models.TextField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    site_web = models.URLField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    c_num = models.CharField(max_length=10, blank=True, null=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, blank=True, null=True)
    
    # Nouveaux champs
    secteur_activite = models.CharField(max_length=255, blank=True, null=True, verbose_name="Secteur d'activité")
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Catégorie")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    bp = models.CharField(max_length=20, blank=True, null=True, verbose_name="Boîte Postale")
    quartier = models.CharField(max_length=255, blank=True, null=True, verbose_name="Quartier")
    matricule = models.CharField(max_length=20, blank=True, null=True, verbose_name="Matricule")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="clients_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="clients_updated"
    )
    # Relations
    est_client = models.BooleanField(
        default=False, help_text="Indique si l'entreprise est un client actif"
    )
    date_conversion_client = models.DateField(
        blank=True, null=True, help_text="Date de conversion de prospect à client"
    )
    entites_agreement = models.ManyToManyField(
        'document.Entity',
        through="Agreement",
        blank=True,
        help_text="Entités avec lesquelles cette entreprise a un accord",
    )

    @property
    def est_prospect(self):
        """Une entreprise est un prospect si elle n'est pas client"""
        return not self.est_client

    @property
    def est_agree(self):
        """Une entreprise est agréée si elle a au moins un accord avec une entité"""
        return self.entites_agreement.exists()

    @property
    def statut(self):
        """Retourne le statut de l'entreprise selon votre logique métier"""
        if self.est_client:
            if self.est_agree:
                return "Client Agréé"
            return "Client"
        else:
            if self.est_agree:
                return "Prospect Agréé"
            return "Prospect"
        
    def save(self, *args, **kwargs):
        if not self.c_num:
            last_client = Entreprise.objects.filter(
                created_at__year=now().year
            ).count() + 1
            self.c_num = f"c{str(now().year)[-2:]}{now().month:02d}{now().day:02d}{last_client:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nom} ({self.statut})"


class Agreement(models.Model):
    """Gère les relations d'agreement entre entreprises et entités avec historique"""

    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="agreements"
    )
    entite = models.ForeignKey(
        'document.Entity', on_delete=models.CASCADE, related_name="agreements"
    )
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    est_actif = models.BooleanField(default=True)

    # Workflow de demande et validation
    STATUT_CHOICES = [
        ("DEMANDE", "Demande en cours"),
        ("EN_REVUE", "En cours de revue"),
        ("VALIDE", "Validé"),
        ("REJETE", "Rejeté"),
        ("EXPIRE", "Expiré"),
        ("RENOUVELLEMENT", "En attente de renouvellement"),
    ]
    statut_workflow = models.CharField(
        max_length=20, choices=STATUT_CHOICES, default="DEMANDE"
    )
    date_statut = models.DateField(auto_now=True)
    commentaires = models.TextField(blank=True, null=True)

    # Suivi des modifications
    cree_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="agreements_crees"
    )
    modifie_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="agreements_modifies"
    )

    class Meta:
        unique_together = ("entreprise", "entite", "date_debut")

    def __str__(self):
        return f"Agreement {self.entreprise.nom} - {self.entite.nom} ({self.get_statut_workflow_display()})"

    def est_a_renouveler(self, jours_avant=30):
        """Vérifie si l'agreement doit être renouvelé dans les X jours"""
        if not self.date_fin:
            return False
        today = timezone.now().date()
        return self.est_actif and (self.date_fin - today).days <= jours_avant




class TypeInteraction(models.Model):
    """Types d'interactions possibles avec paramètres personnalisables"""

    nom = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    couleur = models.CharField(
        max_length=20, blank=True, null=True, help_text="Code couleur pour l'interface"
    )

    def __str__(self):
        return self.nom


class Interaction(models.Model):
    """Pour suivre les interactions avec les contacts et entreprises"""

    date = models.DateTimeField()
    date_creation = models.DateTimeField(auto_now_add=True)
    type_interaction = models.ForeignKey(TypeInteraction, on_delete=models.PROTECT)
    titre = models.CharField(max_length=200)
    notes = models.TextField(blank=True, null=True)

    # Rendez-vous et relances
    est_rendez_vous = models.BooleanField(default=False)
    duree_minutes = models.PositiveIntegerField(blank=True, null=True)

    # Relance
    date_relance = models.DateField(blank=True, null=True)
    relance_effectuee = models.BooleanField(default=False)

    # Relations
    contact = models.ForeignKey(
        Contact, on_delete=models.CASCADE, related_name="interactions"
    )
    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="interactions"
    )
    entite = models.ForeignKey(
        'document.Entity', on_delete=models.CASCADE, related_name="interactions"
    )

    # Utilisateur ayant créé l'interaction
    cree_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="interactions_creees"
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.type_interaction} avec {self.contact} le {self.date.strftime('%d/%m/%Y')}"


class OpportuniteCommerciale(models.Model):
    """Gestion des opportunités commerciales"""

    titre = models.CharField(max_length=200)
    description = models.TextField()
    entreprise = models.ForeignKey(
        Entreprise, on_delete=models.CASCADE, related_name="opportunites"
    )
    contact_principal = models.ForeignKey(
        Contact, on_delete=models.SET_NULL, null=True, related_name="opportunites"
    )
    entite = models.ForeignKey(
        'document.Entity', on_delete=models.CASCADE, related_name="opportunites"
    )

    # Montant et probabilité
    montant_estime = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    PROBABILITE_CHOICES = [
        (10, "10% - Très faible"),
        (25, "25% - Faible"),
        (50, "50% - Moyenne"),
        (75, "75% - Forte"),
        (90, "90% - Très forte"),
    ]
    probabilite = models.IntegerField(choices=PROBABILITE_CHOICES, default=25)

    # Étapes et suivi
    ETAPE_CHOICES = [
        ("QUALIFICATION", "Qualification"),
        ("PROPOSITION", "Proposition"),
        ("NEGOCIATION", "Négociation"),
        ("GAGNEE", "Gagnée"),
        ("PERDUE", "Perdue"),
    ]
    etape = models.CharField(
        max_length=20, choices=ETAPE_CHOICES, default="QUALIFICATION"
    )

    # Dates
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_cloture_prevue = models.DateField(blank=True, null=True)
    date_cloture_reelle = models.DateField(blank=True, null=True)

    # Suivi
    cree_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="opportunites_creees"
    )
    responsable = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name="opportunites_gerees"
    )

    class Meta:
        ordering = ["-date_creation"]

    def __str__(self):
        return f"{self.titre} - {self.entreprise.nom} ({self.get_etape_display()})"

    @property
    def valeur_ponderee(self):
        """Calcule la valeur pondérée de l'opportunité"""
        if not self.montant_estime:
            return 0
        return (self.montant_estime * self.probabilite) / 100

    def marquer_gagnee(self):
        """Marque l'opportunité comme gagnée et convertit le prospect en client si nécessaire"""
        self.etape = "GAGNEE"
        self.date_cloture_reelle = timezone.now().date()

        # Conversion du prospect en client si ce n'est pas déjà le cas
        if not self.entreprise.est_client:
            self.entreprise.est_client = True
            self.entreprise.date_conversion_client = timezone.now().date()
            self.entreprise.save()

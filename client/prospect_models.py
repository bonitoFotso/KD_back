from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings
from django.utils.timezone import now

from client.models import Categorie, Contact, Entreprise, Ville







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

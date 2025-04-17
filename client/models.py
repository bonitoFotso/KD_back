from django.db import models

from django.core.validators import RegexValidator
from django.utils.timezone import now
from django.utils import timezone

from django.conf import settings
from django.db import models

class AuditableMixin(models.Model):
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="%(class)s_updated"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        
class Pays(models.Model):
    nom = models.CharField(max_length=100, unique=True)
    code_iso = models.CharField(max_length=3, unique=True)

    def __str__(self):
        return self.nom

    @property
    def nombre_de_regions(self):
        return self.regions.count()

    def liste_des_villes(self):
        villes = Ville.objects.filter(region__pays=self)
        return [ville.nom for ville in villes]
    

class Region(models.Model):
    nom = models.CharField(max_length=100)
    pays = models.ForeignKey(Pays, on_delete=models.CASCADE, related_name='regions')

    def __str__(self):
        return f"{self.nom} ({self.pays.nom})"

    @property
    def nombre_de_villes(self):
        return self.villes.count()

    def liste_des_villes(self):
        villes = self.villes.all()
        return [ville.nom for ville in villes]

class Ville(models.Model):
    nom = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='villes')

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"

    @property
    def nom_complet(self):
        return f"{self.nom}, {self.region.nom}, {self.region.pays.nom}"

    def description(self):
        return f"La ville de {self.nom} est située dans la région de {self.region.nom}, dans le pays de {self.region.pays.nom}. Sa population est estimée à {self.population if self.population is not None else 'inconnue'}."

class Categorie(models.Model):
    cat_choice = (
        ('PME', 'PME'),
        ('TPE', 'TPE'),
        ('PE', 'PE'),
        ('GE', 'GE'),
    )
    nom = models.CharField(max_length=255, choices=cat_choice)

    def __str__(self):
        return self.nom
    
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
        related_name="entreprises_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="entreprises_updated"
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
class Client(AuditableMixin, models.Model):
    nom = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(max_length=20, blank=True, null=True)
    adresse = models.TextField(blank=True, null=True)
    c_num = models.CharField(max_length=10, blank=True, null=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, blank=True, null=True)
    is_client = models.BooleanField(default=False)
    
    # Nouveaux champs
    secteur_activite = models.CharField(max_length=255, blank=True, null=True, verbose_name="Secteur d'activité")
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Catégorie")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    bp = models.CharField(max_length=20, blank=True, null=True, verbose_name="Boîte Postale")
    quartier = models.CharField(max_length=255, blank=True, null=True, verbose_name="Quartier")
    matricule = models.CharField(max_length=20, blank=True, null=True, verbose_name="Matricule")
    agreer = models.BooleanField(default=False, verbose_name="Agréé")
    agreement_fournisseur = models.BooleanField(default=False, verbose_name="Agreement Fournisseur")
    entite = models.CharField(max_length=255, blank=True, null=True, verbose_name="Entité")
    
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

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        if not self.c_num:
            last_client = Client.objects.filter(
                created_at__year=now().year
            ).count() + 1
            self.c_num = f"c{str(now().year)[-2:]}{now().month:02d}{now().day:02d}{last_client:04d}"
        super().save(*args, **kwargs)



class Site(AuditableMixin, models.Model):
    nom = models.CharField(max_length=255)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sites')
    localisation = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    s_num = models.CharField(max_length=15, blank=True, null=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sites_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sites_updated"
    )
    def save(self, *args, **kwargs):
        if not self.s_num:
            last_site = Site.objects.filter(
                client=self.client,
                created_at__year=now().year
            ).count() + 1
            self.s_num = f"{self.client.c_num}{last_site:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom


class Contact(models.Model):
    # Informations de base
    nom = models.CharField(max_length=255, verbose_name="Nom",blank=True, null=True,)
    prenom = models.CharField(max_length=255, blank=True, null=True, verbose_name="Prénom")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    telephone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    mobile = models.CharField(max_length=20, blank=True, null=True, verbose_name="Mobile")
    poste = models.CharField(max_length=255, blank=True, null=True, verbose_name="Poste")
    service = models.CharField(max_length=255, blank=True, null=True, verbose_name="Service")
    role_achat = models.CharField(max_length=255, blank=True, null=True, verbose_name="Rôle dans les achats")
    date_envoi = models.DateField(blank=True, null=True, verbose_name="Date d'envoi")
    relance = models.BooleanField(default=False, verbose_name="Relance")
    source = models.CharField(max_length=255, blank=True, null=True, verbose_name="Source")
    valide = models.BooleanField(default=True, verbose_name="Valide")
    # Relation avec le modèle Client
    client = models.ForeignKey(
        'Client',  # Remplacez 'Client' par le nom de votre modèle Client si nécessaire
        on_delete=models.CASCADE,
        related_name='contacts',
        blank=True,
        null=True,
        verbose_name="Client associé"
    )
    
    site = models.ForeignKey(
        'Site',  # Remplacez 'Site' par le nom de votre modèle Site si nécessaire
        on_delete=models.CASCADE,
        related_name='contacts',
        blank=True,
        null=True,
        verbose_name="Site associé"
    )

    # Informations supplémentaires
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    ville = models.ForeignKey(
        'Ville',  # Remplacez 'Ville' par le nom de votre modèle Ville si nécessaire
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Ville"
    )
    quartier = models.CharField(max_length=255, blank=True, null=True, verbose_name="Quartier")
    bp = models.CharField(max_length=10, blank=True, null=True, verbose_name="Boîte Postale")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes supplémentaires")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Date de mise à jour")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="contacts_created"
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="contacts_updated"
    )

    def __str__(self):
        return f"{self.nom} {self.prenom}" if self.prenom else self.email

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        
        
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
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="agreements_crees"
    )
    modifie_par = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="agreements_modifies"
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
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="interactions_creees"
    )

    class Meta:
        ordering = ["-date"]

    def __str__(self):
        return f"{self.type_interaction} avec {self.contact} le {self.date.strftime('%d/%m/%Y')}"

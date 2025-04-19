from django.db import models
from django.core.validators import RegexValidator
from django.utils.timezone import now
from django.utils import timezone
from django.conf import settings


class AuditableMixin(models.Model):
    """
    Mixin pour ajouter des champs d'audit (création/modification) à un modèle.
    """
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
    """
    Représente un pays avec son nom et code ISO.
    """
    nom = models.CharField(max_length=100, unique=True)
    code_iso = models.CharField(max_length=3, unique=True)

    def __str__(self):
        return self.nom

    @property
    def nombre_de_regions(self):
        """Retourne le nombre de régions dans ce pays."""
        return self.regions.count()
    
    @property
    def get_regions(self):
        """Retourne la liste des régions dans ce pays."""
        return self.regions.all()

    def liste_des_villes(self):
        """Retourne la liste des noms de villes dans ce pays."""
        villes = Ville.objects.filter(region__pays=self)
        return [ville.nom for ville in villes]
    
    class Meta:
        verbose_name = "Pays"
        verbose_name_plural = "Pays"


class Region(models.Model):
    """
    Représente une région administrative dans un pays.
    """
    nom = models.CharField(max_length=100)
    pays = models.ForeignKey(Pays, on_delete=models.CASCADE, related_name='regions')

    def __str__(self):
        return f"{self.nom} ({self.pays.nom})"

    @property
    def nombre_de_villes(self):
        """Retourne le nombre de villes dans cette région."""
        return self.villes.count()

    def liste_des_villes(self):
        """Retourne la liste des noms de villes dans cette région."""
        villes = self.villes.all()
        return [ville.nom for ville in villes]
    
    class Meta:
        verbose_name = "Région"
        verbose_name_plural = "Régions"
        unique_together = ('nom', 'pays')  # Évite les doublons de régions dans un même pays


class Ville(models.Model):
    """
    Représente une ville dans une région.
    """
    nom = models.CharField(max_length=100)
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='villes')
    population = models.IntegerField(null=True, blank=True)  # Ajouté pour corriger la référence dans description()

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"

    @property
    def nom_complet(self):
        """Retourne le nom complet de la ville avec région et pays."""
        return f"{self.nom}, {self.region.nom}, {self.region.pays.nom}"

    def description(self):
        """Retourne une description textuelle de la ville."""
        return f"La ville de {self.nom} est située dans la région de {self.region.nom}, dans le pays de {self.region.pays.nom}. Sa population est estimée à {self.population if self.population is not None else 'inconnue'}."
    
    class Meta:
        verbose_name = "Ville"
        verbose_name_plural = "Villes"
        unique_together = ('nom', 'region')  # Évite les doublons de villes dans une même région


class Categorie(models.Model):
    """
    Catégorie d'entreprise selon sa taille.
    """
    CATEGORIE_CHOICES = (
        ('PME', 'Petite et Moyenne Entreprise'),
        ('TPE', 'Très Petite Entreprise'),
        ('PE', 'Petite Entreprise'),
        ('GE', 'Grande Entreprise'),
    )
    nom = models.CharField(max_length=3, choices=CATEGORIE_CHOICES)

    def __str__(self):
        return self.get_nom_display()
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"


class Client(AuditableMixin):
    """
    Représente un client ou prospect avec ses informations détaillées.
    """
    # Informations de base
    nom = models.CharField(max_length=255)
    email = models.EmailField(blank=True, null=True)
    telephone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés.")]
    )
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    c_num = models.CharField(max_length=15, blank=True, null=True, unique=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, blank=True, null=True)
    
    # Informations commerciales
    secteur_activite = models.CharField(max_length=255, blank=True, null=True, verbose_name="Secteur d'activité")
    categorie = models.ForeignKey(Categorie, on_delete=models.CASCADE, blank=True, null=True, verbose_name="Catégorie")
    bp = models.CharField(max_length=20, blank=True, null=True, verbose_name="Boîte Postale")
    quartier = models.CharField(max_length=255, blank=True, null=True, verbose_name="Quartier")
    matricule = models.CharField(max_length=20, blank=True, null=True, verbose_name="Matricule")
    
    # Statut commercial
    est_client = models.BooleanField(
        default=False, 
        help_text="Indique si l'entreprise est un client actif",
        verbose_name="Est client"
    )
    date_conversion_client = models.DateField(
        blank=True, 
        null=True, 
        help_text="Date de conversion de prospect à client"
    )
    
    # Informations d'agrément
    agree = models.BooleanField(default=False, verbose_name="Agréé")  # Remplace 'agreer'
    entite = models.CharField(max_length=255, blank=True, null=True, verbose_name="Entité")
    entites_agreement = models.ManyToManyField(
        'document.Entity',
        through="Agreement",
        blank=True,
        help_text="Entités avec lesquelles cette entreprise a un accord",
    )
    

    def __str__(self):
        return self.nom

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
        """Retourne le statut de l'entreprise selon la logique métier"""
        if self.est_client:
            if self.est_agree:
                return "Client Agréé"
            return "Client"
        else:
            if self.est_agree:
                return "Prospect Agréé"
            return "Prospect"

    def save(self, *args, **kwargs):
        """
        Génère automatiquement un numéro de client unique si nécessaire.
        """
        if not self.c_num:
            # Utilisation d'une transaction pour éviter les problèmes de concurrence
            from django.db import transaction
            with transaction.atomic():
                # Année et date actuelles
                annee_courte = str(now().year)[-2:]
                mois = now().month
                jour = now().day
                
                # Récupère le nombre de clients créés aujourd'hui + 1
                last_client = Client.objects.select_for_update().filter(
                    created_at__year=now().year
                ).count() + 1
                
                # Format: cYYMMDDXXXX où XXXX est le compteur incrémental
                self.c_num = f"c{annee_courte}{mois:02d}{jour:02d}{last_client:04d}"
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Client"
        verbose_name_plural = "Clients"
        indexes = [
            models.Index(fields=['nom']),
            models.Index(fields=['c_num']),
            models.Index(fields=['est_client']),
        ]


class Site(AuditableMixin):
    """
    Représente un site/localisation physique d'un client.
    """
    nom = models.CharField(max_length=255)
    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name='sites')
    localisation = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    s_num = models.CharField(max_length=20, blank=True, null=True, unique=True)
    ville = models.ForeignKey(Ville, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.nom} - {self.client.nom}"

    def save(self, *args, **kwargs):
        """
        Génère automatiquement un numéro de site unique basé sur le client.
        """
        if not self.s_num:
            from django.db import transaction
            with transaction.atomic():
                # Récupère le nombre de sites pour ce client cette année + 1
                last_site = Site.objects.select_for_update().filter(
                    client=self.client,
                    created_at__year=now().year
                ).count() + 1
                
                # Format: [c_num du client]XXXX où XXXX est le compteur incrémental
                self.s_num = f"{self.client.c_num}{last_site:04d}"
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "Site"
        verbose_name_plural = "Sites"
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['s_num']),
        ]


class Contact(AuditableMixin):
    """
    Représente un contact/personne associé à un client ou site.
    """
    # Informations personnelles
    nom = models.CharField(max_length=255, verbose_name="Nom", blank=True, null=True)
    prenom = models.CharField(max_length=255, blank=True, null=True, verbose_name="Prénom")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    telephone = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Téléphone",
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés.")]
    )
    mobile = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        verbose_name="Mobile",
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Le numéro de téléphone doit être au format: '+999999999'. Jusqu'à 15 chiffres autorisés.")]
    )
    
    # Informations professionnelles
    poste = models.CharField(max_length=255, blank=True, null=True, verbose_name="Poste")
    service = models.CharField(max_length=255, blank=True, null=True, verbose_name="Service")
    role_achat = models.CharField(max_length=255, blank=True, null=True, verbose_name="Rôle dans les achats")
    
    # Suivi commercial
    date_envoi = models.DateField(blank=True, null=True, verbose_name="Date d'envoi")
    relance = models.BooleanField(default=False, verbose_name="Relance")
    source = models.CharField(max_length=255, blank=True, null=True, verbose_name="Source")
    valide = models.BooleanField(default=True, verbose_name="Valide")
    
    # Relations
    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='contacts',
        blank=True,
        null=True,
        verbose_name="Client associé"
    )
    site = models.ForeignKey(
        Site,
        on_delete=models.CASCADE,
        related_name='contacts',
        blank=True,
        null=True,
        verbose_name="Site associé"
    )

    # Adresse
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse")
    ville = models.ForeignKey(
        Ville,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        verbose_name="Ville"
    )
    quartier = models.CharField(max_length=255, blank=True, null=True, verbose_name="Quartier")
    bp = models.CharField(max_length=10, blank=True, null=True, verbose_name="Boîte Postale")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes supplémentaires")

    def __str__(self):
        if self.nom and self.prenom:
            return f"{self.nom} {self.prenom}"
        elif self.nom:
            return self.nom
        elif self.email:
            return self.email
        return "Contact sans nom"

    def clean(self):
        """
        Validation personnalisée pour s'assurer qu'au moins un moyen de contact existe.
        """
        from django.core.exceptions import ValidationError
        
        if not any([self.email, self.telephone, self.mobile]):
            raise ValidationError("Au moins un moyen de contact (email, téléphone ou mobile) doit être fourni.")

    class Meta:
        verbose_name = "Contact"
        verbose_name_plural = "Contacts"
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['site']),
            models.Index(fields=['nom', 'prenom']),
            models.Index(fields=['email']),
        ]


class Agreement(models.Model):
    """
    Gère les relations d'agreement entre entreprises et entités avec historique.
    """
    STATUT_CHOICES = [
        ("DEMANDE", "Demande en cours"),
        ("EN_REVUE", "En cours de revue"),
        ("VALIDE", "Validé"),
        ("REJETE", "Rejeté"),
        ("EXPIRE", "Expiré"),
        ("RENOUVELLEMENT", "En attente de renouvellement"),
    ]
    
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="agreements"
    )
    entite = models.ForeignKey(
        'document.Entity', on_delete=models.CASCADE, related_name="agreements"
    )
    
    # Période de validité
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    est_actif = models.BooleanField(default=True)

    # Workflow de demande et validation
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

    def __str__(self):
        return f"Agreement {self.client.nom} - {self.entite.nom} ({self.get_statut_workflow_display()})"

    def est_a_renouveler(self, jours_avant=30):
        """
        Vérifie si l'agreement doit être renouvelé dans les X jours.
        """
        if not self.date_fin:
            return False
        today = timezone.now().date()
        return self.est_actif and (self.date_fin - today).days <= jours_avant
    
    def clean(self):
        """
        Validation personnalisée pour les dates.
        """
        from django.core.exceptions import ValidationError
        
        if self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError({"date_fin": "La date de fin doit être postérieure à la date de début."})

    class Meta:
        verbose_name = "Agreement"
        verbose_name_plural = "Agreements"
        unique_together = ("client", "entite", "date_debut")
        indexes = [
            models.Index(fields=['client']),
            models.Index(fields=['entite']),
            models.Index(fields=['date_debut']),
            models.Index(fields=['date_fin']),
            models.Index(fields=['statut_workflow']),
        ]


class TypeInteraction(models.Model):
    """
    Types d'interactions possibles avec paramètres personnalisables.
    """
    nom = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    couleur = models.CharField(
        max_length=20, 
        blank=True, 
        null=True, 
        help_text="Code couleur pour l'interface (ex: #FF5733)"
    )

    def __str__(self):
        return self.nom
    
    class Meta:
        verbose_name = "Type d'interaction"
        verbose_name_plural = "Types d'interactions"


class Interaction(AuditableMixin):
    """
    Pour suivre les interactions avec les contacts et entreprises.
    """
    date = models.DateTimeField()
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
    client = models.ForeignKey(
        Client, on_delete=models.CASCADE, related_name="interactions"
    )
    entite = models.ForeignKey(
        'document.Entity', on_delete=models.CASCADE, related_name="interactions"
    )

    def __str__(self):
        return f"{self.type_interaction} avec {self.contact} le {self.date.strftime('%d/%m/%Y')}"
    
    def clean(self):
        """
        Validation personnalisée pour les dates.
        """
        from django.core.exceptions import ValidationError
        
        if self.date_relance and self.date_relance < self.date.date():
            raise ValidationError({"date_relance": "La date de relance doit être postérieure à la date d'interaction."})
        
        if self.est_rendez_vous and not self.duree_minutes:
            raise ValidationError({"duree_minutes": "La durée est requise pour un rendez-vous."})

    class Meta:
        verbose_name = "Interaction"
        verbose_name_plural = "Interactions"
        ordering = ["-date"]
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['contact']),
            models.Index(fields=['client']),
            models.Index(fields=['type_interaction']),
            models.Index(fields=['date_relance']),
        ]
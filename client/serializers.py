from rest_framework import serializers

from courrier.serializers import CourrierSerializer
from document.serializers import AffaireListSerializer, FactureListSerializer, OffreListSerializer, RapportListSerializer
from .models import Agreement, Categorie, Interaction, Pays, Region, TypeInteraction, Ville, Client, Site, Contact
from django.contrib.auth import get_user_model
User = get_user_model()
class UserSerializer(serializers.ModelSerializer):
    """Serializer pour le modèle User."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']

class VillesSerialiser(serializers.ModelSerializer):
    region = serializers.CharField(source='region.nom', read_only=True)
    pays = serializers.CharField(source='region.pays.nom', read_only=True)
    
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'region', 'pays']
        
class RegionListSerializer(serializers.ModelSerializer):
    pays = serializers.CharField(source='pays.nom', read_only=True)
    villes = VillesSerialiser(many=True)
    
    class Meta:
        model = Region
        fields = ['id', 'nom', 'pays', 'villes']

class PaysListSerializer(serializers.ModelSerializer):
    regions = RegionListSerializer(many=True)
    class Meta:
        model = Pays
        fields = ['id', 'nom', 'code_iso', 'regions']
    

class PaysDetailSerializer(serializers.ModelSerializer):
    nombre_de_regions = serializers.IntegerField(read_only=True)
    regions = serializers.SerializerMethodField()
    
    class Meta:
        model = Pays
        fields = ['id', 'nom', 'code_iso', 'nombre_de_regions', 'regions']
    
    def get_regions(self, obj):
        return RegionListSerializer(obj.regions.all(), many=True).data

class PaysEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pays
        fields = ['nom', 'code_iso']

  
class RegionDetailSerializer(serializers.ModelSerializer):
    pays_details = PaysListSerializer(source='pays', read_only=True)
    villes = serializers.SerializerMethodField()
    nombre_de_villes = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Region
        fields = ['id', 'nom', 'pays', 'pays_details', 'nombre_de_villes', 'villes']
    


class RegionEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ['nom', 'pays']

class VilleListSerializer(serializers.ModelSerializer):
    region = RegionListSerializer(read_only=True)
    region_nom = serializers.CharField(source='region.nom', read_only=True)
    pays_nom = serializers.CharField(source='region.pays.nom', read_only=True)
    
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'region_nom', 'pays_nom', 'region']

class VilleDetailSerializer(serializers.ModelSerializer):
    region_details = RegionListSerializer(source='region', read_only=True)
    
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'region', 'region_details']

class VilleEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ville
        fields = ['nom', 'region']

class ContactListSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    client_id = serializers.CharField(source='client.id', read_only=True)
    
    class Meta:
        model = Contact
        fields = ['id', 'nom', 'prenom', 'email', 'telephone', 'client_nom', 'poste','client_id']

class ContactDetailSerializer(serializers.ModelSerializer):
    client_details = serializers.SerializerMethodField()
    ville_details = VilleListSerializer(source='ville', read_only=True)
    
    class Meta:
        model = Contact
        fields = '__all__'
    
    def get_client_details(self, obj):
        if obj.client:
            return ClientListSerializer(obj.client).data
        return None

class ContactEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        exclude = ['created_at', 'updated_at']




class SiteEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['nom', 'client', 'localisation', 'description', 'ville']
        
        
class AgreementSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des agreements."""
    
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    entite_nom = serializers.CharField(source='entite.nom', read_only=True)
    statut_workflow_display = serializers.CharField(source='get_statut_workflow_display', read_only=True)
    a_renouveler = serializers.SerializerMethodField()
    
    class Meta:
        model = Agreement
        fields = ['id', 'client', 'client_nom', 'entite', 'entite_nom', 
                 'date_debut', 'date_fin', 'est_actif', 'statut_workflow', 
                 'statut_workflow_display', 'a_renouveler']
        read_only_fields = ['id']
    
    def get_a_renouveler(self, obj):
        return obj.est_a_renouveler()


class AgreementDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour un agreement."""
    
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    entite_nom = serializers.CharField(source='entite.nom', read_only=True)
    statut_workflow_display = serializers.CharField(source='get_statut_workflow_display', read_only=True)
    cree_par = UserSerializer(read_only=True)
    modifie_par = UserSerializer(read_only=True)
    a_renouveler = serializers.SerializerMethodField()
    
    class Meta:
        model = Agreement
        fields = ['id', 'client', 'client_nom', 'entite', 'entite_nom',
                 'date_debut', 'date_fin', 'est_actif', 'statut_workflow',
                 'statut_workflow_display', 'date_statut', 'commentaires',
                 'cree_par', 'modifie_par', 'a_renouveler']
        read_only_fields = ['id', 'cree_par', 'modifie_par', 'date_statut']
    
    def get_a_renouveler(self, obj):
        return obj.est_a_renouveler()


class TypeInteractionSerializer(serializers.ModelSerializer):
    """Serializer pour les types d'interactions."""
    
    class Meta:
        model = TypeInteraction
        fields = ['id', 'nom', 'description', 'couleur']
        read_only_fields = ['id']


class InteractionSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des interactions."""
    
    type_interaction_nom = serializers.CharField(source='type_interaction.nom', read_only=True)
    contact_nom = serializers.SerializerMethodField()
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    entite_nom = serializers.CharField(source='entite.nom', read_only=True)
    
    class Meta:
        model = Interaction
        fields = ['id', 'date', 'type_interaction', 'type_interaction_nom', 'titre',
                 'contact', 'contact_nom', 'client', 'client_nom', 'entite', 'entite_nom',
                 'est_rendez_vous', 'date_relance', 'relance_effectuee']
        read_only_fields = ['id']
    
    def get_contact_nom(self, obj):
        if obj.contact.prenom:
            return f"{obj.contact.nom} {obj.contact.prenom}"
        return obj.contact.nom


class InteractionDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une interaction."""
    
    type_interaction_nom = serializers.CharField(source='type_interaction.nom', read_only=True)
    contact_nom = serializers.SerializerMethodField()
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    entite_nom = serializers.CharField(source='entite.nom', read_only=True)
    created_by = UserSerializer(read_only=True)
    updated_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Interaction
        fields = ['id', 'date', 'type_interaction', 'type_interaction_nom', 'titre', 'notes',
                 'contact', 'contact_nom', 'client', 'client_nom', 'entite', 'entite_nom',
                 'est_rendez_vous', 'duree_minutes', 'date_relance', 'relance_effectuee',
                 'created_at', 'updated_at', 'created_by', 'updated_by']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']
    
    def get_contact_nom(self, obj):
        if obj.contact.prenom:
            return f"{obj.contact.nom} {obj.contact.prenom}"
        return obj.contact.nom

        
        
class CategorySerializer(serializers.ModelSerializer):
    """Serializer pour les catégories."""
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom']
        read_only_fields = ['id']
class CategoryDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une catégorie."""
    
    class Meta:
        model = Categorie
        fields = ['id', 'nom']
        read_only_fields = ['id']
class CategoryEditSerializer(serializers.ModelSerializer):
    """Serializer pour l'édition des catégories."""
    
    class Meta:
        model = Categorie
        fields = ['nom']
        read_only_fields = ['id']
class ClientSerializer(serializers.ModelSerializer):
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    region_nom = serializers.CharField(source='ville.region.nom', read_only=True
    )
    statut = serializers.CharField(read_only=True)
    pays_nom = serializers.CharField(source='ville.region.pays.nom', read_only=True)
    categorie = serializers.CharField(source='categorie.nom', read_only=True)
    class Meta:
        model = Client
        fields = [
            'id',
            'c_num',
            'nom',
            'email',
            'telephone',
            'ville_nom',
            'secteur_activite',
            'categorie',
            'agree',
            'est_client',
            'bp',
            'quartier',
            'matricule',
            'entite',
            'pays_nom',
            'region_nom',
            'statut',
        ]
        read_only_fields = ['c_num']

class ClientListSerializer(serializers.ModelSerializer):
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    region_nom = serializers.CharField(source='ville.region.nom', read_only=True
    )
    statut = serializers.CharField(read_only=True)
    contacts_count = serializers.IntegerField(source='contacts.count', read_only=True)
    offres_count = serializers.IntegerField(source='offres.count', read_only=True)
    affaires_count = serializers.IntegerField(source='affaires.count', read_only=True)
    factures_count = serializers.IntegerField(source='factures.count', read_only=True)
    opportunities_count = serializers.IntegerField(source='opportunites.count', read_only=True)
    courriers_count = serializers.IntegerField(source='courriers.count', read_only=True)
    categorie = serializers.CharField(source='categorie.nom', read_only=True)

    
    class Meta:
        model = Client
        fields = [
            'id',
            'c_num',
            'nom',
            'email',
            'telephone',
            'ville_nom',
            'secteur_activite',
            'categorie',
            'agree',
            'est_client',
            'bp',
            'quartier',
            'matricule',
            'entite',
            'contacts_count',
            'offres_count',
            'affaires_count',
            'factures_count',
            'region_nom',
            'opportunities_count',
            'courriers_count',
            'statut',
        ]
        read_only_fields = ['c_num']
        
class SiteListSerializer(serializers.ModelSerializer):
    client = ClientListSerializer(read_only=True)
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    
    class Meta:
        model = Site
        fields = ['id', 's_num', 'nom', 'client', 'ville_nom', 'localisation']
        read_only_fields = ['s_num']
        
        
class ClientDetailSerializer(ClientListSerializer):
    contacts = ContactListSerializer(many=True, read_only=True)
    offres = OffreListSerializer(many=True, read_only=True)
    factures = FactureListSerializer(many=True, read_only=True)
    sites = SiteListSerializer(many=True, read_only=True)
    affaires = AffaireListSerializer(many=True, read_only=True)
    rapports = RapportListSerializer(many=True, read_only=True)
    ville = VilleListSerializer(read_only=True)
    #opportunites = OpportuniteSerializer(many=True, read_only=True)
    courriers = CourrierSerializer(many=True, read_only=True)
    
    
    
    class Meta:
        model = Client
        fields = [
            'id',
            'c_num',
            'nom',
            'email',
            'telephone',
            'ville',
            'secteur_activite',
            'agree',
            'est_client',
            'bp',
            'quartier',
            'matricule',
            'entite',
            'contacts_count',
            'offres_count',
            'affaires_count',
            'factures_count',
            'region_nom',
            'contacts',
            'offres',
            'factures',
            'sites',
            'affaires',
            'rapports',
            'opportunites',
            'courriers',
        ]

class SiteDetailSerializer(serializers.ModelSerializer):
    client_details = ClientListSerializer(source='client', read_only=True)
    ville_details = VilleListSerializer(source='ville', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = Site
        fields = '__all__'
        read_only_fields = ['s_num', 'created_at', 'updated_at', 'created_by', 'updated_by']


class ClientEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        exclude = ['c_num', 'created_at', 'updated_at', 'created_by', 'updated_by']
        
        
class ContactDetailedSerializer(serializers.ModelSerializer):
   ville_nom = serializers.CharField(source='ville.nom', default='N/A')
   region = serializers.CharField(source='ville.region.nom', default='N/A')
   entreprise = serializers.CharField(source='client.nom', default='N/A')
   secteur = serializers.CharField(source='client.secteur_activite', default='N/A')
   agrement = serializers.BooleanField(source='client.agreer', default=False)
   status = serializers.SerializerMethodField()
   categorie = serializers.CharField(source='client.categorie', default='N/A')

   def get_status(self, obj):
       return 'Actif' if obj.relance else 'Inactif'

   class Meta:
       model = Contact
       fields = [
           'id', 'region', 'ville_nom', 'entreprise', 'secteur','categorie',
           'prenom', 'nom', 'poste', 'service', 'role_achat',
           'telephone', 'email', 'status', 'agrement'
       ]

class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = ['id', 'nom']

class ContactSerializer(serializers.ModelSerializer):
    site = SiteListSerializer(read_only=True)
    client = ClientListSerializer(read_only=True)
    ville = VilleListSerializer(read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    updated_by = serializers.CharField(source='updated_by.username', read_only=True)
    
    class Meta:
        model = Contact
        fields = ['id', 'nom', 'prenom', 'email', 'telephone', 'poste', 'service', 'client','notes','created_by','created_at','updated_at','updated_by','ville','quartier','bp','mobile',
                 'role_achat', 'source', 'valide', 'date_envoi', 'relance','site']
class ClientWithContactsListSerializer(serializers.ModelSerializer):
    contacts_count = serializers.IntegerField(source='contacts.count', read_only=True)
    contacts = ContactSerializer(many=True, read_only=True)
    ville = VilleListSerializer(read_only=True)
    categorie = CategoryListSerializer(read_only=True)
    created_by = serializers.CharField(source='created_by.username', read_only=True)
    updated_by = serializers.CharField(source='updated_by.username', read_only=True)

    class Meta:
        model = Client
        fields = ['id', 'nom', 'c_num', 'email', 'telephone', 'matricule', 'categorie','created_at', 'created_by', 'updated_at', 'updated_by',
                 'ville', 'agree', 'secteur_activite',
                 'contacts_count', 'contacts', 'entite']

class ClientWithContactsDetailSerializer(serializers.ModelSerializer):
    contacts = ContactSerializer(many=True, read_only=True)
    contacts_count = serializers.IntegerField(source='contacts.count', read_only=True)

    class Meta:
        model = Client
        fields = '__all__'
        
        

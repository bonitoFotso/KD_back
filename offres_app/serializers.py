# serializers.py
from rest_framework import serializers
from django.utils import timezone
from django.db import transaction
from django.db.models import Max

from api.user.serializers import UserSerializer

from .models import Offre
from client.models import Client, Contact
from document.models import Entity, Product

class EntitySerializer(serializers.ModelSerializer):
    """Sérialiseur pour les entités"""
    class Meta:
        model = Entity
        fields = ['id', 'code', 'name']


class ProductSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les produits"""
    departement = serializers.StringRelatedField(source='departement.name', read_only=True)
    class Meta:
        model = Product
        fields = ['id', 'code', 'departement', 'name']


class ContactSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les contacts"""
    client_id = serializers.IntegerField(source='client.id', read_only=True)
    class Meta:
        model = Contact
        fields = ['id', 'nom', 'email', 'telephone', 'client_id']
        
        
        


class ClientSerializer(serializers.ModelSerializer):
    """Sérialiseur complet pour les clients"""
    contacts = ContactSerializer(many=True, read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'c_num', 'nom', 'email', 'telephone', 
            'ville_nom', 'region_nom', 'secteur_activite', 
            'bp', 'quartier', 'entite', 'agreer', 
            'agreement_fournisseur', 'contacts'
        ]


class ClientLightSerializer(serializers.ModelSerializer):
    """Sérialiseur léger pour les clients (sans les contacts)"""
    ville_nom = serializers.StringRelatedField(source='ville.nom', read_only=True)
    region_nom = serializers.StringRelatedField(source='ville.region.nom', read_only=True)
    pays_nom = serializers.StringRelatedField(source='ville.region.pays.nom', read_only=True)
    class Meta:
        model = Client
        fields = [
            'id', 'c_num', 'nom', 'email', 'telephone', 
            'ville_nom', 'region_nom','pays_nom', 'secteur_activite'
        ]


class OffreProduitSerializer(serializers.Serializer):
    """Sérialiseur pour les produits dans une offre"""
    id = serializers.IntegerField()  # ID du produit
    #quantite = serializers.IntegerField(min_value=1)
    #remise = serializers.FloatField(min_value=0, max_value=100, default=0)

class OffreStatusChangeSerializer(serializers.Serializer):
    """Sérialiseur pour le changement de statut d'une offre"""
    #statut = serializers.ChoiceField(choices=Offre.STATUS_CHOICES)
    
    class Meta:
        model = Offre
        fields = ['statut']

class OffreSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la lecture des offres"""
    client = ClientLightSerializer()
    entity = EntitySerializer()
    produits = ProductSerializer(many=True, read_only=True)
    contact = ContactSerializer()
    produit_principal = ProductSerializer()
    user = UserSerializer()
    createur =  UserSerializer()
    
    
    class Meta:
        model = Offre
        fields = [
            'id', 'reference', 'date_creation', 'date_modification','user', 'createur',
            'statut', 'montant', 'relance',
            'necessite_relance', 'client',
            'contact', 'entity','produit_principal',
            'produits', 'notes', 'sequence_number','fichier',
            'date_envoi', 'date_validation', 'date_cloture'
        ]
        read_only_fields = [
            'reference', 'date_creation', 'date_modification',
            'date_validation', 'necessite_relance', 'sequence_number'
        ]
        

class OffreNoteSerializer(serializers.ModelSerializer):
    """Sérialiseur pour modifier les notes d'une offre"""
    notes = serializers.CharField(required=True)
    class Meta:
        model = Offre
        fields = ['notes']
        read_only_fields = ['id', 'date_creation', 'date_modification']
        extra_kwargs = {
            'notes': {'required': True}
        }
class OffreRelanceSerializer(serializers.ModelSerializer):
    """Sérialiseur pour modifier la date de relance d'une offre"""
    #relance = serializers.DateField(required=True)
    
    class Meta:
        model = Offre
        fields = ['relance']
        read_only_fields = ['id', 'date_creation', 'date_modification']
        #extra_kwargs = {
        #    'relance': {'required': True}
        #}


class OffreCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création et mise à jour des offres"""
    produits = OffreProduitSerializer(many=True, required=False)
    
    class Meta:
        model = Offre
        fields = [
            'statut', 'client', 'contact', 'entity',
            'produits', 'notes', 'montant', 'produit_principal','fichier'
        ]
    
    def validate(self, data):
        """Validation personnalisée des données"""
        # Vérifier que le produit principal est inclus dans les produits
        #produit_principal_id = data.get('produit')
        #produits_data = data.get('produits', [])
        
        #if produit_principal_id:
        #    # Vérifier si le produit principal fait partie des produits sélectionnés
        #    produit_ids = [produit.get('id') for produit in produits_data]
        #    if produit_principal_id not in produit_ids:
        #        raise serializers.ValidationError(
        #            {"produit": "Le produit principal doit être inclus dans la liste des produits"}
        #        )
        
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        """Créer une offre avec ses produits associés"""
        # Extraire les données des produits
        produits_data = validated_data.pop('produits', [])
        
        # Créer l'offre
        offre = Offre.objects.create(**validated_data)
        
        # Ajouter les produits à l'offre
        for produit_data in produits_data:
            product_id = produit_data.get('id')
            if product_id:
                try:
                    produit = Product.objects.get(id=product_id)
                    offre.produits.add(produit)
                except Product.DoesNotExist:
                    print(f"Produit ID {product_id} non trouvé lors de la création de l'offre {offre.pk}")
                    #logger.warning(f"Produit ID {product_id} non trouvé lors de la création de l'offre {offre.id}")
        
        return offre
    
    @transaction.atomic
    def update(self, instance, validated_data):
        """Mettre à jour une offre et ses produits associés"""
        # Extraire les données des produits
        produits_data = validated_data.pop('produits', None)
        
        # Mettre à jour les champs de base de l'offre
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        # Sauvegarder l'instance avant de gérer les relations
        instance.save()
        
        # Si les produits sont inclus dans la mise à jour
        if produits_data is not None:
            # Effacer les anciens produits et ajouter les nouveaux
            instance.produits.clear()
            
            for produit_data in produits_data:
                product_id = produit_data.get('id')
                if product_id:
                    try:
                        produit = Product.objects.get(id=product_id)
                        instance.produits.add(produit)
                    except Product.DoesNotExist:
                        print(f"Produit ID {product_id} non trouvé lors de la mise à jour de l'offre {instance.id}")
                        #logger.warning(f"Produit ID {product_id} non trouvé lors de la mise à jour de l'offre {instance.id}")
        
        return instance
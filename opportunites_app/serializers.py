from rest_framework import serializers
from django.utils.timezone import now
from decimal import Decimal

from affaires_app.serializers import UserBasicSerializer
import client

from .models import Opportunite
from client.serializers import ClientSerializer, ContactSerializer
from document.serializers import EntityDetailSerializer, ProductListSerializer


class OpportuniteSerializer(serializers.ModelSerializer):
    """
    Sérialiseur de base pour les opportunités avec informations essentielles
    pour l'affichage dans les listes.
    """
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    contact_nom = serializers.CharField(source='contact.nom', read_only=True)
    entity_code = serializers.CharField(source='entity.code', read_only=True)
    produit_principal_nom = serializers.CharField(source='produit_principal.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    valeur_ponderee = serializers.DecimalField(max_digits=15, decimal_places=2, read_only=True)
    created_by_nom = serializers.CharField(source='created_by.get_full_name', read_only=True)
    necessite_relance = serializers.BooleanField(read_only=True)
    client_ville = serializers.CharField(source='client.ville', read_only=True)
    contact_ville = serializers.CharField(source='contact.ville', read_only=True)
    client_pays = serializers.CharField(source='client.pays', read_only=True)
    contact_pays = serializers.CharField(source='contact.pays', read_only=True)
    client_region = serializers.CharField(source='client.region', read_only=True)
    contact_region = serializers.CharField(source='contact.region', read_only=True)
    
    class Meta:
        model = Opportunite
        fields = [
            'id', 'reference', 'client', 'client_nom', 'contact', 'contact_nom',
            'client_ville', 'contact_ville', 'client_pays', 'contact_pays',
            'client_region', 'contact_region', 'date_detection', 'entity_id',
            'entity', 'entity_code', 'produit_principal', 'produit_principal_nom',
            'statut', 'statut_display', 'montant', 'montant_estime', 'probabilite', 
            'valeur_ponderee', 'date_creation', 'date_modification', 'date_cloture',
            'relance', 'created_by', 'created_by_nom', 'necessite_relance'
        ]
        read_only_fields = ['reference', 'valeur_ponderee', 'created_by', 'necessite_relance']


class OpportuniteDetailSerializer(OpportuniteSerializer):
    """
    Sérialiseur détaillé pour l'affichage d'une opportunité avec toutes les informations.
    """
    client = ClientSerializer(read_only=True)
    contact = ContactSerializer(read_only=True)
    entity = EntityDetailSerializer(read_only=True)
    produit_principal = ProductListSerializer(read_only=True)
    produits = ProductListSerializer(many=True, read_only=True)
    responsable = UserBasicSerializer(read_only=True)
    
    class Meta(OpportuniteSerializer.Meta):
        fields = OpportuniteSerializer.Meta.fields + [
            'description', 'besoins_client', 'sequence_number', 'produits',
            'date_detection', 'responsable', 'commentaire'
        ]
        read_only_fields = OpportuniteSerializer.Meta.read_only_fields + [
            'sequence_number', 'date_detection'
        ]


class OpportuniteCreateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la création d'une opportunité.
    """
    class Meta:
        model = Opportunite
        fields = [
            'client', 'contact', 'entity', 'produit_principal', 'produits',
            'montant', 'montant_estime', 'description', 'besoins_client',
            'relance', 'statut'
        ]
    
    def validate(self, data):
        """
        Validation personnalisée pour les règles métier.
        """
        # Vérifier que le montant estimé est positif
        montant_estime = data.get('montant_estime')
        if montant_estime and montant_estime <= 0:
            raise serializers.ValidationError(
                {"montant_estime": "Le montant estimé doit être positif."}
            )
        
        # Vérifier que le contact appartient bien au client
        client = data.get('client')
        contact = data.get('contact')
        if client and contact and contact.client.id != client.id:
            raise serializers.ValidationError(
                {"contact": "Le contact doit appartenir au client sélectionné."}
            )
        
        # Vérifier que la date de relance est dans le futur
        relance = data.get('relance')
        if relance and relance <= now():
            raise serializers.ValidationError(
                {"relance": "La date de relance doit être dans le futur."}
            )
        
        return data


class OpportuniteUpdateSerializer(serializers.ModelSerializer):
    """
    Sérialiseur pour la mise à jour d'une opportunité.
    """
    class Meta:
        model = Opportunite
        fields = [
            'montant', 'montant_estime', 'probabilite', 'description', 
            'besoins_client', 'relance', 'contact', 'produit_principal', 
            'produits'
        ]
    
    def validate(self, data):
        """
        Validation personnalisée pour les règles métier.
        """
        # Vérifier que le montant estimé est positif s'il est fourni
        montant_estime = data.get('montant_estime')
        if montant_estime is not None and montant_estime <= 0:
            raise serializers.ValidationError(
                {"montant_estime": "Le montant estimé doit être positif."}
            )
        
        ## Vérifier que le contact appartient bien au client si fourni
        #contact = data.get('contact')
        #if contact:
        #    client = self.instance.client
        #    if contact.client.id != client.id:
        #        raise serializers.ValidationError(
        #            {"contact": "Le contact doit appartenir au client de l'opportunité."}
        #        )
        
        # Vérifier que la probabilité est entre 0 et 100 si fournie
        probabilite = data.get('probabilite')
        if probabilite is not None and (probabilite < 0 or probabilite > 100):
            raise serializers.ValidationError(
                {"probabilite": "La probabilité doit être comprise entre 0 et 100."}
            )
        
        return data


class OpportuniteTransitionSerializer(serializers.Serializer):
    """
    Sérialiseur pour effectuer des transitions d'état sur plusieurs opportunités.
    """
    ids = serializers.ListField(
        child=serializers.IntegerField(),
        min_length=1
    )
    raison = serializers.CharField(required=False, allow_blank=True)


class RaisonPerteSerializer(serializers.Serializer):
    """
    Sérialiseur pour la raison de perte d'une opportunité.
    """
    raison = serializers.CharField(allow_blank=True, required=False)
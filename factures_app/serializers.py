from rest_framework import serializers

from offres_app.serializers import ClientLightSerializer
from .models import Facture
from affaires_app.serializers import AffaireSerializer

class FactureSerializer(serializers.ModelSerializer):
    entity_code = serializers.CharField(source='affaire.offre.entity.code', read_only=True)
    affaire_reference = serializers.CharField(source='affaire.reference', read_only=True)
    est_en_retard = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_status_display', read_only=True)
    solde = serializers.SerializerMethodField()
    client = ClientLightSerializer(read_only=True)
    affaire = AffaireSerializer(read_only=True)
    
    class Meta:
        model = Facture
        fields = [
            'id', 'reference', 'affaire', 'affaire_reference', 'client', 
            'entity_code', 'statut_display', 'date_creation', 
            'date_emission', 'date_echeance', 'date_paiement',
            'montant_ht', 'montant_ttc', 'montant_paye', 'solde',
            'est_en_retard', 'fichier'
        ]
        read_only_fields = ['reference', 'created_by', 'updated_by', 'sequence_number']
    
    def get_est_en_retard(self, obj):
        return obj.est_en_retard()
    
    def get_solde(self, obj):
        return obj.get_solde()

class FactureDetailSerializer(serializers.ModelSerializer):
    affaire = AffaireSerializer(read_only=True)
    client_nom = serializers.CharField(source='affaire.offre.client.nom', read_only=True)
    entity_code = serializers.CharField(source='affaire.offre.entity.code', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    est_en_retard = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_status_display', read_only=True)
    solde = serializers.SerializerMethodField()

    class Meta:
        model = Facture
        fields = [
            'id', 'reference', 'affaire', 'client_nom', 'entity_code', 
            'statut', 'statut_display', 'sequence_number',
            'date_creation', 'date_emission', 'date_echeance', 'date_paiement',
            'montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc', 'montant_paye',
            'solde', 'est_en_retard', 'notes', 'fichier',
            'created_by', 'created_by_name', 'updated_by', 'updated_by_name',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['reference', 'created_by', 'updated_by', 
                          'created_at', 'updated_at', 'sequence_number']
    
    def get_est_en_retard(self, obj):
        return obj.est_en_retard()
    
    def get_solde(self, obj):
        return obj.get_solde()

class FactureCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facture
        fields = [
            'affaire', 'statut', 'date_creation', 'date_echeance',
            'montant_ht', 'taux_tva', 'notes', 'fichier'
        ]
    
    def validate(self, data):
        # Vérifier si l'affaire a déjà une facture
        affaire = data.get('affaire')
        instance = self.instance
        
        if affaire and not instance:
            existing_facture = Facture.objects.filter(affaire=affaire).first()
            if existing_facture:
                raise serializers.ValidationError("Cette affaire possède déjà une facture.")
        
        return data
    
    def create(self, validated_data):
        # Calculer automatiquement les montants TVA et TTC
        facture = Facture(**validated_data)
        facture.calculate_amounts()
        return super().create(validated_data)
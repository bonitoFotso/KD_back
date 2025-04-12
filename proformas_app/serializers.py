from rest_framework import serializers
from .models import Proforma
from offres_app.serializers import OffreSerializer

class ProformaSerializer(serializers.ModelSerializer):
    client_nom = serializers.CharField(source='offre.client.nom', read_only=True)
    entity_code = serializers.CharField(source='offre.entity.code', read_only=True)
    
    class Meta:
        model = Proforma
        fields = [
            'id', 'reference', 'offre', 'client_nom', 'entity_code', 
            'statut', 'date_creation', 'date_validation', 'date_expiration',
            'montant_ht', 'montant_ttc', 'fichier'
        ]
        read_only_fields = ['reference', 'created_by', 'updated_by', 'sequence_number']

class ProformaDetailSerializer(serializers.ModelSerializer):
    offre = OffreSerializer(read_only=True)
    client_nom = serializers.CharField(source='offre.client.nom', read_only=True)
    entity_code = serializers.CharField(source='offre.entity.code', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    class Meta:
        model = Proforma
        fields = [
            'id', 'reference', 'offre', 'client_nom', 'entity_code',
            'statut', 'date_creation', 'date_validation', 'date_expiration',
            'montant_ht', 'taux_tva', 'montant_tva', 'montant_ttc',
            'notes', 'fichier', 'created_by', 'created_by_name',
            'updated_by', 'updated_by_name', 'created_at', 'updated_at',
            'sequence_number'
        ]
        read_only_fields = ['reference', 'created_by', 'updated_by',
                           'created_at', 'updated_at', 'sequence_number']

class ProformaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        #id = serializers.
        model = Proforma
        fields = [
            'offre', 'statut', 'date_creation', 'date_expiration',
            'montant_ht', 'taux_tva', 'notes', 'fichier'
        ]
    
    def validate_offre(self, value):
        # Vérifier si une proforma existe déjà pour cette offre
        if Proforma.objects.filter(offre=value).exists() and not self.instance:
            raise serializers.ValidationError("Une proforma existe déjà pour cette offre.")
        return value
    
    def create(self, validated_data):
        # Calculer automatiquement les montants TVA et TTC
        proforma = Proforma(**validated_data)
        proforma.montant_tva = proforma.montant_ht * (proforma.taux_tva / 100)
        proforma.montant_ttc = proforma.montant_ht + proforma.montant_tva
        return super().create(validated_data)
from rest_framework import serializers

from client.models import Client
from document.models import Entity
from .models import Courrier, CourrierHistory
from document.serializers import EntityListSerializer

class ClientListSerializer(serializers.ModelSerializer):
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    region_nom = serializers.CharField(source='ville.region.nom', read_only=True
    )
    contacts_count = serializers.IntegerField(source='contacts.count', read_only=True)
    offres_count = serializers.IntegerField(source='offres.count', read_only=True)
    affaires_count = serializers.IntegerField(source='affaires.count', read_only=True)
    factures_count = serializers.IntegerField(source='factures.count', read_only=True)
    opportunities_count = serializers.IntegerField(source='opportunites.count', read_only=True)
    courriers_count = serializers.IntegerField(source='courriers.count', read_only=True)
    
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
            'agreer',
            'agreement_fournisseur',
            'is_client',
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
            'courriers_count'
        ]
        read_only_fields = ['c_num']

class CourrierListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des courriers (version légère)"""
    entite_nom = serializers.CharField(source='entite.nom', read_only=True)
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Courrier
        fields = [
            'id', 'reference', 'entite_nom', 'client_nom', 'doc_type', 
            'doc_type_display', 'objet', 'statut', 'statut_display', 
            'direction', 'direction_display', 'date_creation', 
            'date_envoi', 'date_reception', 'fichier', 'est_urgent',
            'created_by_name', 'is_overdue'
        ]


class CourrierSerializer(serializers.ModelSerializer):
    """Serializer complet pour les courriers"""
    entite = EntityListSerializer(read_only=True)
    entite_id = serializers.PrimaryKeyRelatedField(
        source='entite', write_only=True, 
        queryset=Entity.objects.all()
    )
    
    client = ClientListSerializer(read_only=True)
    client_id = serializers.PrimaryKeyRelatedField(
        source='client', write_only=True, 
        queryset=Client.objects.all()
    )
    
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    # updated_by_name = serializers.CharField(source='updated_by.get_full_name', read_only=True)
    
    doc_type_display = serializers.CharField(source='get_doc_type_display', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    direction_display = serializers.CharField(source='get_direction_display', read_only=True)
    is_overdue = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Courrier
        fields = [
            'id', 'reference', 'entite', 'entite_id', 'client', 'client_id',
            'doc_type', 'doc_type_display', 'direction', 'direction_display',
            'statut', 'statut_display', 'date_creation', 'date_envoi', 'created_by_name',
            'date_reception', 'objet', 'notes', 'fichier', 'est_urgent',
            'created_by', 'handled_by', 'is_overdue'
        ]
        read_only_fields = ['reference', 'date_creation', 'created_by', 'handled_by']


class CourrierHistorySerializer(serializers.ModelSerializer):
    """Serializer pour l'historique des courriers"""
    courrier_reference = serializers.CharField(source='courrier.reference', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    
    class Meta:
        model = CourrierHistory
        fields = [
            'id', 'courrier', 'courrier_reference', 'action', 
            'action_display', 'date_action', 'user', 'user_name', 'details'
        ]
from rest_framework import serializers
from django.db.models import Sum, Count
from django.utils.timezone import now

from client.models import Client
from document.serializers import OffreListSerializer

class ClientListSerializer(serializers.ModelSerializer):
    # Champs de base
    ville_nom = serializers.CharField(source='ville.nom', read_only=True)
    contacts_count = serializers.IntegerField(source='contacts.count', read_only=True)
    
    # Compteurs de documents par type
    offres_count = serializers.SerializerMethodField()
    proformas_count = serializers.SerializerMethodField()
    factures_count = serializers.SerializerMethodField()
    rapports_count = serializers.SerializerMethodField()
    
    # Statistiques des offres
    offres_en_cours = serializers.SerializerMethodField()
    offres_gagnees = serializers.SerializerMethodField()
    offres_perdues = serializers.SerializerMethodField()
    montant_total_offres = serializers.SerializerMethodField()

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
            'contacts_count',
            'offres_count',
            'proformas_count',
            'factures_count',
            'rapports_count',
            'offres_en_cours',
            'offres_gagnees',
            'offres_perdues',
            'montant_total_offres'
        ]
        read_only_fields = ['c_num']

    def _get_documents_by_type(self, obj, doc_type):
        """Méthode utilitaire pour obtenir les documents d'un type spécifique"""
        return obj.document_set.filter(doc_type=doc_type)

    def get_offres_count(self, obj):
        return self._get_documents_by_type(obj, 'OFF').count()

    def get_proformas_count(self, obj):
        return self._get_documents_by_type(obj, 'PRO').count()

    def get_factures_count(self, obj):
        return self._get_documents_by_type(obj, 'FAC').count()

    def get_rapports_count(self, obj):
        return self._get_documents_by_type(obj, 'RAP').count()

    def get_offres_en_cours(self, obj):
        return self._get_documents_by_type(obj, 'OFF').filter(
            statut__in=['BROUILLON', 'ENVOYE']
        ).count()

    def get_offres_gagnees(self, obj):
        return self._get_documents_by_type(obj, 'OFF').filter(
            statut='GAGNE'
        ).count()

    def get_offres_perdues(self, obj):
        return self._get_documents_by_type(obj, 'OFF').filter(
            statut='PERDU'
        ).count()

    def get_montant_total_offres(self, obj):
        total = self._get_documents_by_type(obj, 'OFF').filter(
            statut='GAGNE'
        ).aggregate(total=Sum('montant'))['total']
        return float(total) if total else 0.0

class ClientDetailSerializer(ClientListSerializer):
    documents_recents = serializers.SerializerMethodField()
    offres_recentes = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()

    class Meta(ClientListSerializer.Meta):
        fields = ClientListSerializer.Meta.fields + [
            'documents_recents',
            'offres_recentes',
            'contacts'
        ]

    def get_documents_recents(self, obj):
        documents = obj.document_set.all().order_by('-date_creation')[:10]
        return [{
            'id': doc.id,
            'type': doc.doc_type,
            'reference': doc.reference,
            'date_creation': doc.date_creation,
            'statut': doc.statut
        } for doc in documents]

    def get_offres_recentes(self, obj):
        offres = self._get_documents_by_type(obj, 'OFF').order_by('-date_creation')[:5]
        return OffreListSerializer(offres, many=True).data

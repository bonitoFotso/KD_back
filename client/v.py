from rest_framework import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Prefetch
from .models import Region, Ville, Client, Contact

class ContactDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            'id', 'nom', 'prenom', 'email', 'telephone', 
            'mobile', 'poste', 'service',
            'quartier', 'bp', 'notes'
        ]

class ClientDetailSerializer(serializers.ModelSerializer):
    contacts = ContactDetailSerializer(many=True, read_only=True)
    
    class Meta:
        model = Client
        fields = [
            'id', 'nom', 'email', 'telephone', 'adresse',
            'c_num', 'secteur_activite', 'bp', 'quartier',
            'matricule', 'agreer', 'agreement_fournisseur',
            'entite', 'contacts'
        ]

class VilleDetailSerializer(serializers.ModelSerializer):
    clients = serializers.SerializerMethodField()
    
    class Meta:
        model = Ville
        fields = ['id', 'nom', 'clients']
    
    def get_clients(self, obj):
        clients = obj.client_set.all()
        return ClientDetailSerializer(clients, many=True).data

class RegionDetailSerializer(serializers.ModelSerializer):
    villes = VilleDetailSerializer(many=True, read_only=True)
    pays_nom = serializers.CharField(source='pays.nom', read_only=True)
    
    class Meta:
        model = Region
        fields = ['id', 'nom', 'pays_nom', 'villes']

class RegionHierarchyView(APIView):
    def get(self, request):
        # Récupérer les paramètres de filtrage
        region_id = request.query_params.get('region_id')
        ville_id = request.query_params.get('ville_id')
        
        # Construire la requête de base avec les préchargements
        queryset = Region.objects.select_related('pays').prefetch_related(
            'villes',
            Prefetch(
                'villes__client_set',
                queryset=Client.objects.prefetch_related('contacts')
            )
        )
        
        # Appliquer les filtres si nécessaire
        if region_id:
            queryset = queryset.filter(id=region_id)
            
        if ville_id:
            queryset = queryset.filter(villes__id=ville_id)
        
        # Sérialiser et retourner les données
        serializer = RegionDetailSerializer(queryset, many=True)
        return Response(serializer.data)
from rest_framework import viewsets, serializers
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from document.models import Affaire, AttestationFormation, Client, Entity, Facture, Formation, Participant, Product, Proforma, Rapport, Site
from offres_app.models import Offre

# Serializers de base
class ClientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Client
        fields = ['id', 'nom', 'email', 'telephone', 'adresse']

class SiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Site
        fields = ['id', 'nom', 'localisation', 'description']

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'code', 'name']

class EntitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ['id', 'code', 'name']

class ParticipantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Participant
        fields = ['id', 'nom', 'prenom', 'email', 'telephone', 'fonction']

# Formation serializer sans participants
class FormationBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Formation
        fields = ['id', 'titre', 'date_debut', 'date_fin', 'description']

# Rapport serializer with minimal Formation info
class RapportBasicSerializer(serializers.ModelSerializer):
    site = SiteSerializer(read_only=True)
    produit = ProductSerializer(read_only=True)
    
    class Meta:
        model = Rapport
        fields = ['id', 'reference', 'statut', 'date_creation', 'site', 'produit']

class RapportSerializer(serializers.ModelSerializer):
    site = SiteSerializer(read_only=True)
    produit = ProductSerializer(read_only=True)
    # Removing the formation field since it's a reverse relationship
    
    class Meta:
        model = Rapport
        fields = ['id', 'reference', 'statut', 'date_creation', 'site', 'produit']

class AttestationFormationSerializer(serializers.ModelSerializer):
    participant = ParticipantSerializer(read_only=True)
    
    class Meta:
        model = AttestationFormation
        fields = ['id', 'reference', 'details_formation', 'participant', 'date_creation']

class ProformaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Proforma
        fields = ['id', 'reference', 'statut', 'date_creation']

class FactureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facture
        fields = ['id', 'reference', 'statut', 'date_creation']

class OffreSerializer(serializers.ModelSerializer):
    client = ClientSerializer(read_only=True)
    produit = ProductSerializer(many=True, read_only=True)
    sites = SiteSerializer(many=True, read_only=True)
    proforma = ProformaSerializer(read_only=True)
    entity = EntitySerializer(read_only=True)

    class Meta:
        model = Offre
        fields = ['id', 'reference', 'client', 'date_creation', 'statut', 
                 'date_modification', 'date_validation', 'produit', 'sites',
                 'proforma', 'entity']

# Formation serializer complet avec participants et rapport
class FormationDetailSerializer(serializers.ModelSerializer):
    participants = ParticipantSerializer(many=True, read_only=True)
    rapport = RapportBasicSerializer(read_only=True)
    
    class Meta:
        model = Formation
        fields = ['id', 'titre', 'date_debut', 'date_fin', 'description', 'participants', 'rapport']

class AffaireSerializer(serializers.ModelSerializer):
    offre = OffreSerializer(read_only=True)
    rapports = RapportSerializer(many=True, read_only=True)
    formations = FormationDetailSerializer(many=True, read_only=True)
    attestations = AttestationFormationSerializer(many=True, read_only=True)
    facture = FactureSerializer(read_only=True)

    class Meta:
        model = Affaire
        fields = ['id', 'reference', 'date_creation', 'statut', 'date_debut',
                 'date_fin_prevue', 'offre', 'rapports', 'formations',
                 'attestations', 'facture']

# ViewSets
class OffreViewSet(viewsets.ModelViewSet):
    queryset = Offre.objects.all()
    serializer_class = OffreSerializer

class AffaireViewSet(viewsets.ModelViewSet):
    queryset = Affaire.objects.all()
    serializer_class = AffaireSerializer

class RapportViewSet(viewsets.ModelViewSet):
    queryset = Rapport.objects.all()
    serializer_class = RapportSerializer

class ProformaViewSet(viewsets.ModelViewSet):
    queryset = Proforma.objects.all()
    serializer_class = ProformaSerializer

class FactureViewSet(viewsets.ModelViewSet):
    queryset = Facture.objects.all()
    serializer_class = FactureSerializer

class AttestationFormationViewSet(viewsets.ModelViewSet):
    queryset = AttestationFormation.objects.all()
    serializer_class = AttestationFormationSerializer

class FormationViewSet(viewsets.ModelViewSet):
    queryset = Formation.objects.all()
    serializer_class = FormationDetailSerializer

# URLs configuration
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'offres', OffreViewSet)
router.register(r'affaires', AffaireViewSet)
router.register(r'rapports', RapportViewSet)
router.register(r'proformas', ProformaViewSet)
router.register(r'factures', FactureViewSet)
router.register(r'attestations', AttestationFormationViewSet)
router.register(r'formations', FormationViewSet)

urlpatterns = router.urls
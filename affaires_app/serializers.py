from rest_framework import serializers
from django.utils.timezone import now
from django.contrib.auth import get_user_model

from factures_app.models import Facture

from .models import Affaire
from document.models import Rapport, Formation
from offres_app.models import Offre
from offres_app.serializers import OffreSerializer, ClientLightSerializer


User = get_user_model()


class UserBasicSerializer(serializers.ModelSerializer):
    """Sérialiseur simple pour les utilisateurs."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RapportSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les rapports liés à une affaire."""
    produit_nom = serializers.CharField(source='produit.name', read_only=True)
    produit_category = serializers.CharField(source='produit.category.code', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    has_formation = serializers.SerializerMethodField()
    
    class Meta:
        model = Rapport
        fields = [
            'id', 'produit', 'produit_nom', 'produit_category', 
            'statut', 'statut_display', 'has_formation',
            'date_creation', 'date_modification'
        ]
    
    def get_has_formation(self, obj):
        """Détermine si le rapport est lié à une formation."""
        return Formation.objects.filter(rapport=obj).exists()


class FormationSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les formations liées à un rapport."""
    
    class Meta:
        model = Formation
        fields = [
            'id', 'titre', 'date_debut', 'date_fin', 
            'description', 'statut'
        ]


class FactureSerializer(serializers.ModelSerializer):
    """Sérialiseur pour les factures liées à une affaire."""
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    
    class Meta:
        model = Facture
        fields = [
            'id', 'reference', 'client', 'client_nom',
            'montant_ht', 'montant_ttc', 'statut', 'statut_display',
            'date_creation', 'date_echeance'
        ]


class AffaireSerializer(serializers.ModelSerializer):
    """Sérialiseur de base pour les affaires."""
    client_nom = serializers.CharField(source='offre.client.nom', read_only=True)
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    responsable_nom = serializers.SerializerMethodField()
    progression = serializers.SerializerMethodField()
    en_retard = serializers.SerializerMethodField()
    
    class Meta:
        model = Affaire
        fields = [
            'id', 'reference', 'offre', 'client_nom',
            'date_debut', 'date_fin_prevue', 'date_fin_reelle',
            'statut', 'statut_display', 'responsable', 'responsable_nom',
            'montant_total', 'montant_facture', 'montant_paye',
            'progression', 'en_retard',
            'date_creation', 'date_modification'
        ]
    
    def get_responsable_nom(self, obj):
        """Retourne le nom complet du responsable."""
        if obj.responsable:
            return f"{obj.responsable.username}".strip() or obj.responsable.username
        return None
    
    def get_progression(self, obj):
        """Calcule le pourcentage de progression."""
        return obj.get_progression()
    
    def get_en_retard(self, obj):
        """Détermine si l'affaire est en retard."""
        if obj.statut == 'EN_COURS' and obj.date_fin_prevue and obj.date_fin_prevue < now():
            return True
        return False


class AffaireDetailSerializer(AffaireSerializer):
    """Sérialiseur détaillé pour une affaire spécifique."""
    offre = OffreSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    responsable = UserBasicSerializer(read_only=True)
    rapports = RapportSerializer(source='rapport_set', many=True, read_only=True)
    factures = FactureSerializer(source='facture_set', many=True, read_only=True)
    montant_restant_a_facturer = serializers.DecimalField(
        source='get_montant_restant_a_facturer',
        max_digits=10, decimal_places=2, read_only=True
    )
    montant_restant_a_payer = serializers.DecimalField(
        source='get_montant_restant_a_payer',
        max_digits=10, decimal_places=2, read_only=True
    )
    
    class Meta(AffaireSerializer.Meta):
        fields = AffaireSerializer.Meta.fields + [
            'created_by', 'notes',
            'rapports', 'factures',
            'montant_restant_a_facturer', 'montant_restant_a_payer'
        ]


class AffaireCreateSerializer(serializers.ModelSerializer):
    """Sérialiseur pour la création d'une affaire."""
    #offre_id = serializers.PrimaryKeyRelatedField(
    #    queryset=Offre.objects.filter(statut='ACCEPTEE'),
    #    source='offre',
    #    write_only=True
    #)
    #responsable_id = serializers.PrimaryKeyRelatedField(
    #    queryset=User.objects.all(),
    #    source='responsable',
    #    required=False,
    #    allow_null=True
    #)
    
    class Meta:
        model = Affaire
        fields = [
            'offre_id', 
            'responsable_id', 'notes', 'statut'
        ]
    
    def validate(self, data):
        """Validation personnalisée."""
        ## Vérification des dates
        #if data.get('date_fin_prevue') and data.get('date_debut') and data['date_fin_prevue'] < data['date_debut']:
        #    raise serializers.ValidationError({
        #        'date_fin_prevue': "La date de fin prévue ne peut pas être antérieure à la date de début."
        #    })
        
        # Vérification que l'offre n'est pas déjà associée à une affaire
        offre = data.get('offre')
        if offre and Affaire.objects.filter(offre=offre).exists():
            raise serializers.ValidationError({
                'offre_id': "Cette offre est déjà associée à une affaire existante."
            })
        
        return data
    
    def create(self, validated_data):
        """Création d'une affaire avec initialisation si nécessaire."""
        if not validated_data.get('date_debut'):
            validated_data['date_debut'] = now()
        
        instance = super().create(validated_data)
        
        # Si l'affaire est créée avec le statut VALIDE, on initialise automatiquement
        if instance.statut == 'VALIDE':
            instance.initialiser_projet()
        
        return instance


class ChangeStatutSerializer(serializers.Serializer):
    """Sérialiseur pour le changement de statut d'une affaire."""
    statut = serializers.ChoiceField(choices=Affaire.STATUT_CHOICES)
    commentaire = serializers.CharField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validation des transitions de statut autorisées."""
        affaire = self.context['view'].get_object()
        nouveau_statut = data['statut']
        
        # Définition des transitions autorisées
        transitions_autorisees = {
            'BROUILLON': ['VALIDE', 'ANNULEE'],
            'VALIDE': ['EN_COURS', 'ANNULEE'],
            'EN_COURS': ['EN_PAUSE', 'TERMINEE', 'ANNULEE'],
            'EN_PAUSE': ['EN_COURS', 'TERMINEE', 'ANNULEE'],
            'TERMINEE': ['EN_COURS'],  # Réouverture possible
            'ANNULEE': ['BROUILLON']  # Réactivation possible
        }
        
        # Vérification de la transition
        if nouveau_statut not in transitions_autorisees.get(affaire.statut, []):
            raise serializers.ValidationError({
                'statut': f"Transition de '{affaire.statut}' vers '{nouveau_statut}' non autorisée."
            })
        
        # Vérifications spécifiques au statut
        if nouveau_statut == 'TERMINEE' and not affaire.date_fin_reelle:
            # On pourrait automatiquement définir la date de fin réelle ici
            data['date_fin_reelle'] = now()
        
        return data


class DashboardSerializer(serializers.Serializer):
    """Sérialiseur pour les données du tableau de bord."""
    compteurs_statut = serializers.ListField(child=serializers.DictField())
    dernieres_affaires = serializers.ListField(child=serializers.DictField())
    affaires_en_retard = serializers.ListField(child=serializers.DictField())
    resume_financier = serializers.DictField()
from rest_framework import serializers
from django.utils.timezone import now
from django.contrib.auth import get_user_model
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
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
    
    class Meta:
        model = Facture
        fields = [
            'id', 'reference',
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


class AffaireDetailSerializer(serializers.ModelSerializer):
    """Sérialiseur détaillé pour une affaire spécifique."""
    offre = OffreSerializer(read_only=True)
    created_by = UserBasicSerializer(read_only=True)
    responsable = UserBasicSerializer(read_only=True)
    rapports = RapportSerializer(source='rapport_set', many=True, read_only=True)
    factures = FactureSerializer(source='facture_set', many=True, read_only=True)
    
    # Modify these two fields
    montant_restant_a_facturer = serializers.SerializerMethodField()
    montant_restant_a_payer = serializers.SerializerMethodField()
    
    en_retard = serializers.SerializerMethodField()
    
    class Meta:
        model = Affaire
        fields = [
            'id', 'reference', 'offre',
            'date_debut', 'date_fin_prevue', 'date_fin_reelle',
            'statut', 'responsable',
            'montant_total', 'montant_facture', 'montant_paye',
            'en_retard',
            'date_creation', 'date_modification',
            'created_by', 'notes',
            'rapports', 'factures',
            'montant_restant_a_facturer', 'montant_restant_a_payer'
        ]
    
    def get_montant_restant_a_facturer(self, obj):
        """Handle the montant_restant_a_facturer safely."""
        try:
            value = obj.get_montant_restant_a_facturer()
            # If value is None, return 0
            if value is None:
                return Decimal('0.00')
            # Ensure it's a Decimal
            if not isinstance(value,Decimal):
                value =Decimal(str(value))
            # Quantize to 2 decimal places
            return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except (InvalidOperation, TypeError, ValueError):
            # If any error occurs, return 0
            return Decimal('0.00')
    
    def get_montant_restant_a_payer(self, obj):
        """Handle the montant_restant_a_payer safely."""
        try:
            value = obj.get_montant_restant_a_payer()
            # If value is None, return 0
            if value is None:
                return Decimal('0.00')
            # Ensure it's a Decimal
            if not isinstance(value,Decimal):
                value =Decimal(str(value))
            # Quantize to 2 decimal places
            return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        except (InvalidOperation, TypeError, ValueError):
            # If any error occurs, return 0
            return Decimal('0.00')
    
    def get_en_retard(self, obj):
        """Détermine si l'affaire est en retard."""
        if obj.statut == 'EN_COURS' and obj.date_fin_prevue and obj.date_fin_prevue < now():
            return True
        return False



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
    dateChangement = serializers.DateTimeField(required=False)
    
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
            # Si la date spécifique est fournie, on l'utilise pour la date de fin réelle
            if 'date_specifique' in data:
                pass  # La date sera utilisée directement dans le modèle
            else:
                # On pourrait automatiquement définir la date de fin réelle ici
                data['date_specifique'] = now()
        
        return data
    
class AssignerResponsableSerializer(serializers.Serializer):
    """Sérialiseur pour l'assignation d'un responsable"""
    responsable_id = serializers.IntegerField(required=True)
    commentaire = serializers.CharField(required=False, allow_blank=True)
    
    def validate_responsable_id(self, value):
        """Valide que l'utilisateur existe"""
        try:
            User.objects.get(pk=value)
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("L'utilisateur spécifié n'existe pas.")


class DashboardSerializer(serializers.Serializer):
    """Sérialiseur pour les données du tableau de bord."""
    compteurs_statut = serializers.ListField(child=serializers.DictField())
    dernieres_affaires = serializers.ListField(child=serializers.DictField())
    affaires_en_retard = serializers.ListField(child=serializers.DictField())
    resume_financier = serializers.DictField()
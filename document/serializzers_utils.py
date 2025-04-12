from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework import serializers

from document.models import AuditLog

class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id',
            'user',
            'user_name',
            'action',
            'action_display',
            'object_repr',
            'changes',
            'timestamp'
        ]
        
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
        return None
class BaseDocumentSerializer(serializers.ModelSerializer):
    entity_code = serializers.CharField(source='entity.code', read_only=True)
    entity_name = serializers.CharField(source='entity.name', read_only=True)
    client_nom = serializers.CharField(source='client.nom', read_only=True)
    client_numero = serializers.CharField(source='client.c_num', read_only=True)
    created_by_name = serializers.SerializerMethodField()
    statut_display = serializers.CharField(source='get_statut_display', read_only=True)
    fichier_url = serializers.SerializerMethodField()
    can_envoyer = serializers.SerializerMethodField()
    can_valider = serializers.SerializerMethodField()
    can_refuser = serializers.SerializerMethodField()

    class Meta:
        abstract = True
        fields = [
            'id',
            'reference',
            'entity',
            'entity_code',
            'entity_name',
            'client',
            'client_nom',
            'client_numero',
            'date_creation',
            'statut',
            'statut_display',
            'doc_type',
            'created_by',
            'created_by_name',
            'sequence_number',
            'fichier',
            'fichier_url',
            'can_envoyer',
            'can_valider',
            'can_refuser'
        ]
        read_only_fields = [
            'reference',
            'date_creation',
            'sequence_number',
            'created_by'
        ]

    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}".strip() or obj.created_by.username
        return None

    def get_fichier_url(self, obj):
        if obj.fichier:
            return self.context['request'].build_absolute_uri(obj.fichier.url)
        return None

    def get_can_envoyer(self, obj):
        try:
            return obj.can_envoyer()
        except:
            return False

    def get_can_valider(self, obj):
        try:
            return obj.can_valider()
        except:
            return False

    def get_can_refuser(self, obj):
        try:
            return obj.can_refuser()
        except:
            return False

    def validate_doc_type(self, value):
        if not value.isalpha() or not value.isupper() or len(value) != 3:
            raise serializers.ValidationError(
                "Le type de document doit être composé de 3 lettres majuscules"
            )
        return value

    def create(self, validated_data):
        request = self.context.get('request')
        if request and request.user:
            validated_data['created_by'] = request.user
        return super().create(validated_data)

class DocumentListSerializer(BaseDocumentSerializer):
    """Serializer pour la liste des documents avec les champs essentiels"""
    
    class Meta(BaseDocumentSerializer.Meta):
        abstract = True
        fields = [
            'id',
            'reference',
            'client_nom',
            'date_creation',
            'statut',
            'statut_display',
            'doc_type',
            'can_envoyer',
            'can_valider',
            'can_refuser'
        ]

class DocumentDetailSerializer(BaseDocumentSerializer):
    """Serializer pour le détail d'un document avec tous les champs"""
    audit_logs = serializers.SerializerMethodField()

    class Meta(BaseDocumentSerializer.Meta):
        abstract = True
        fields = BaseDocumentSerializer.Meta.fields + ['audit_logs']

    def get_audit_logs(self, obj):
        from .serializers import AuditLogSerializer  # Import local pour éviter import circulaire
        audit_logs = obj.auditlog_set.all().order_by('-timestamp')
        return AuditLogSerializer(audit_logs, many=True).data
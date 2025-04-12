from django.contrib.contenttypes.models import ContentType
from .models import UserActionLog

def log_user_action(user, action_type, instance, field_name=None, old_value=None, new_value=None, description=None, request=None):
    """
    Utilitaire pour enregistrer une action utilisateur
    """
    content_type = ContentType.objects.get_for_model(instance)
    
    # Créer l'entrée de journal
    log_entry = UserActionLog(
        user=user,
        action_type=action_type,
        content_type=content_type,
        object_id=instance.id,
        field_name=field_name,
        old_value=old_value,
        new_value=new_value,
        description=description
    )
    
    # Enregistrer l'adresse IP si request est fourni
    if request and hasattr(request, 'META'):
        log_entry.ip_address = request.META.get('REMOTE_ADDR')
    
    log_entry.save()
    return log_entry